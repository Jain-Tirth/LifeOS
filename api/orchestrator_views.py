from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.http import StreamingHttpResponse
from agents.models import AgentSession
from agents.services.orchestrator import orchestrator
from .orchestrator_serializers import ChatMessageSerializer, ChatResponseSerializer
from asgiref.sync import async_to_sync
import asyncio
import json


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat(request):
    """
    Send a message to the orchestrator for intelligent agent routing
    
    Request body:
    {
        "message": "I want to plan my meals for next week",
        "session_id": "optional-session-id",  (optional)
        "force_agent": "meal_planner"  (optional - bypass intent classification)
    }
    
    Response:
    {
        "success": true,
        "response": {...},
        "agent": "meal_planner",
        "intent_classification": {
            "primary_agent": "meal_planner",
            "confidence": 0.95,
            "reasoning": "..."
        },
        "session_id": "uuid"
    }
    """
    serializer = ChatMessageSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    message = serializer.validated_data['message']
    session_id = serializer.validated_data.get('session_id')
    force_agent = serializer.validated_data.get('force_agent')
    
    # Get or create session
    session = None
    if session_id:
        try:
            session = AgentSession.objects.get(
                session_id=session_id,
                user=request.user
            )
        except AgentSession.DoesNotExist:
            return Response({
                'error': 'Session not found or does not belong to user'
            }, status=status.HTTP_404_NOT_FOUND)
    
    # Process message through orchestrator
    try:
        result = asyncio.run(
            orchestrator.process_message(
                message=message,
                user=request.user,
                session=session,
                force_agent=force_agent
            )
        )
        
        response_serializer = ChatResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat_stream(request):
    """
    Stream agent responses in real-time using Server-Sent Events (SSE)
    
    Request body:
    {
        "message": "I want to plan my meals for next week",
        "session_id": "optional-session-id",  (optional)
        "force_agent": "meal_planner"  (optional)
    }
    
    Response: SSE stream with chunks of agent response
    """
    serializer = ChatMessageSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    message = serializer.validated_data['message']
    session_id = serializer.validated_data.get('session_id')
    force_agent = serializer.validated_data.get('force_agent')
    
    # Get or create session
    session = None
    if session_id:
        try:
            session = AgentSession.objects.get(
                session_id=session_id,
                user=request.user
            )
        except AgentSession.DoesNotExist:
            def error_stream():
                yield f"data: {json.dumps({'error': 'Session not found'})}\n\n"
            return StreamingHttpResponse(
                error_stream(),
                content_type='text/event-stream',
                status=404
            )
    
    def event_stream():
        """Generator function for SSE streaming"""
        import queue
        import threading
        
        q = queue.Queue()
        exception_holder = {'exception': None}
        
        def run_async_gen():
            """Run async generator in thread"""
            async def collect():
                try:
                    async for chunk in orchestrator.process_message_stream(
                        message=message,
                        user=request.user,
                        session=session,
                        force_agent=force_agent
                    ):
                        q.put(('data', chunk))
                except Exception as e:
                    exception_holder['exception'] = e
                    q.put(('error', str(e)))
                finally:
                    q.put(('done', None))
            
            asyncio.run(collect())
        
        # Start async generator in background thread
        thread = threading.Thread(target=run_async_gen, daemon=True)
        thread.start()
        
        # Yield chunks as they arrive from queue
        try:
            while True:
                # Non-blocking get with timeout to allow checking if done
                try:
                    item = q.get(timeout=30)  # 30 second timeout
                except queue.Empty:
                    yield f"data: {{\"type\": \"error\", \"error\": \"Timeout waiting for response\"}}\n\n"
                    break
                
                msg_type, data = item
                
                if msg_type == 'data':
                    yield f"data: {json.dumps(data)}\n\n"
                elif msg_type == 'error':
                    yield f"data: {json.dumps({'error': data, 'type': 'error'})}\n\n"
                    break
                elif msg_type == 'done':
                    yield "data: {\"type\": \"done\"}\n\n"
                    break
        finally:
            thread.join(timeout=1)
    
    response = StreamingHttpResponse(
        event_stream(),
        content_type='text/event-stream'
    )
    response['Cache-Control'] = 'no-cache'
    response['X-Accel-Buffering'] = 'no'
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_agents(request):
    """
    Get list of available agents
    
    Response:
    {
        "implemented": ["meal_planner"],
        "planned": ["meal_planner", "planner", "habit_coach", "knowledge", "wellness"]
    }
    """
    return Response({
        'implemented': orchestrator.get_available_agents(),
        'planned': orchestrator.get_all_agent_types()
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_sessions(request):
    """
    Get all sessions for the authenticated user
    
    Response:
    [
        {
            "session_id": "uuid",
            "agent_type": "meal_planner",
            "created_at": "2026-01-30T...",
            "updated_at": "2026-01-30T...",
            "message_count": 5
        }
    ]
    """
    sessions = AgentSession.objects.filter(user=request.user).order_by('-updated_at')
    
    session_data = []
    for session in sessions:
        session_data.append({
            'session_id': session.session_id,
            'agent_type': session.agent_type,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'message_count': session.messages.count()
        })
    
    return Response(session_data, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_session_messages(request, session_id):
    """
    Get all messages for a specific session
    
    Response:
    [
        {
            "role": "user",
            "content": "Plan my meals",
            "created_at": "2026-01-30T..."
        },
        {
            "role": "agent",
            "content": "...",
            "created_at": "2026-01-30T..."
        }
    ]
    """
    try:
        session = AgentSession.objects.get(
            session_id=session_id,
            user=request.user
        )
    except AgentSession.DoesNotExist:
        return Response({
            'error': 'Session not found or does not belong to user'
        }, status=status.HTTP_404_NOT_FOUND)
    
    messages = session.messages.all().order_by('created_at')
    
    message_data = [
        {
            'role': msg.role,
            'content': msg.content,
            'created_at': msg.created_at.isoformat()
        }
        for msg in messages
    ]
    
    return Response(message_data, status=status.HTTP_200_OK)
