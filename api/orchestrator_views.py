from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from agents.models import AgentSession
from agents.services.orchestrator import orchestrator
from .orchestrator_serializers import ChatMessageSerializer, ChatResponseSerializer
import asyncio


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
