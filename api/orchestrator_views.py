from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.http import StreamingHttpResponse
from agents.models import AgentSession, MealPlan, Task, StudySession, WellnessActivity
from agents.services.orchestrator import orchestrator
from .orchestrator_serializers import ChatMessageSerializer, ChatResponseSerializer
from .serializers import (
    MealPlanSerializer, 
    TaskSerializer, 
    StudySessionSerializer, 
    WellnessActivitySerializer
)
from asgiref.sync import async_to_sync
import asyncio
import json
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
@permission_classes([AllowAny])
def chat(request):
    """
    Send a message to the orchestrator for intelligent agent routing
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
                user=request.user if request.user.is_authenticated else None
            )
        except AgentSession.DoesNotExist:
            return Response({
                'error': 'Session not found or does not belong to user'
            }, status=status.HTTP_404_NOT_FOUND)
    
    # Process message through orchestrator
    try:
        # Note: In a real Django view, we should use a wrapper to run the async orchestrator
        # or use an async view (Django 3.1+)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            orchestrator.process_message(
                message=message,
                user=request.user if request.user.is_authenticated else None,
                session=session,
                force_agent=force_agent
            )
        )
        loop.close()
        
        response_serializer = ChatResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)
        
    except Exception as e:
        import traceback
        return Response({
            'success': False,
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def chat_stream(request):
    """
    Stream agent responses in real-time using Server-Sent Events (SSE)
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
                user=request.user if request.user.is_authenticated else None
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
            # Create a new event loop for the background thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def collect():
                try:
                    async for chunk in orchestrator.process_message_stream(
                        message=message,
                        user=request.user if request.user.is_authenticated else None,
                        session=session,
                        force_agent=force_agent
                    ):
                        q.put(('data', chunk))
                except Exception as e:
                    import traceback
                    print(f"Streaming error in thread: {e}")
                    traceback.print_exc()
                    exception_holder['exception'] = e
                    q.put(('error', str(e)))
                finally:
                    q.put(('done', None))
            
            try:
                loop.run_until_complete(collect())
            finally:
                loop.close()
        
        # Start async generator in background thread
        thread = threading.Thread(target=run_async_gen, daemon=True)
        thread.start()
        
        # Yield chunks as they arrive from queue
        try:
            while True:
                # Non-blocking get with timeout to allow checking if done
                try:
                    item = q.get(timeout=60)  # 60 second timeout
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
@permission_classes([AllowAny])
def get_available_agents(request):
    """
    Get list of available agents
    """
    return Response({
        'implemented': orchestrator.get_available_agents(),
        'planned': orchestrator.get_all_agent_types()
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_user_sessions(request):
    """
    Get all sessions for the user (handles unauthenticated)
    """
    sessions = AgentSession.objects.filter(
        user=request.user if request.user.is_authenticated else None
    ).order_by('-updated_at')
    
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
@permission_classes([AllowAny])
def get_session_messages(request, session_id):
    """
    Get all messages for a specific session
    """
    try:
        session = AgentSession.objects.get(
            session_id=session_id,
            user=request.user if request.user.is_authenticated else None
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


@api_view(['POST'])
@permission_classes([AllowAny])
def save_agent_response(request):
    """
    Generic endpoint to save agent response data to appropriate model
    Automatically routes to correct model based on agent_type
    """
    agent_type = request.data.get('agent_type')
    session_id = request.data.get('session_id')
    data = request.data.get('data', {})
    
    if not agent_type:
        return Response({
            'success': False,
            'error': 'agent_type is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Add session_id to data if provided
    if session_id:
        data['session_id'] = session_id
    
    try:
        # Route to appropriate serializer based on agent type
        if 'meal' in agent_type.lower() or 'planner' in agent_type.lower():
            serializer = MealPlanSerializer(data=data, context={'request': request})
        elif 'productivity' in agent_type.lower() or 'task' in agent_type.lower():
            serializer = TaskSerializer(data=data, context={'request': request})
        elif 'study' in agent_type.lower() or 'buddy' in agent_type.lower():
            serializer = StudySessionSerializer(data=data, context={'request': request})
        elif 'wellness' in agent_type.lower():
            serializer = WellnessActivitySerializer(data=data, context={'request': request})
        else:
            return Response({
                'success': False,
                'error': f'Unknown agent type: {agent_type}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate and save
        if serializer.is_valid():
            # Set user if authenticated
            if request.user.is_authenticated:
                serializer.save(user=request.user)
            else:
                serializer.save()
            
            logger.info(f"Agent response saved successfully for {agent_type}")
            
            return Response({
                'success': True,
                'message': 'Agent response saved successfully',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        else:
            return Response({
                'success': False,
                'errors': serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        logger.error(f"Error saving agent response: {str(e)}")
        return Response({
            'success': False,
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
def bulk_save_agent_responses(request):
    """
    Bulk save multiple agent responses at once
    Useful for saving multiple items from a single agent interaction
    """
    items = request.data.get('items', [])
    
    if not items or not isinstance(items, list):
        return Response({
            'success': False,
            'error': 'items array is required'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    saved_items = []
    errors = []
    
    for idx, item in enumerate(items):
        agent_type = item.get('agent_type')
        session_id = item.get('session_id')
        data = item.get('data', {})
        
        if not agent_type:
            errors.append({
                'index': idx,
                'error': 'agent_type is required'
            })
            continue
        
        # Add session_id to data if provided
        if session_id:
            data['session_id'] = session_id
        
        try:
            # Route to appropriate serializer
            if 'meal' in agent_type.lower() or 'planner' in agent_type.lower():
                serializer = MealPlanSerializer(data=data, context={'request': request})
            elif 'productivity' in agent_type.lower() or 'task' in agent_type.lower():
                serializer = TaskSerializer(data=data, context={'request': request})
            elif 'study' in agent_type.lower() or 'buddy' in agent_type.lower():
                serializer = StudySessionSerializer(data=data, context={'request': request})
            elif 'wellness' in agent_type.lower():
                serializer = WellnessActivitySerializer(data=data, context={'request': request})
            else:
                errors.append({
                    'index': idx,
                    'error': f'Unknown agent type: {agent_type}'
                })
                continue
            
            # Validate and save
            if serializer.is_valid():
                if request.user.is_authenticated:
                    obj = serializer.save(user=request.user)
                else:
                    obj = serializer.save()
                
                saved_items.append({
                    'index': idx,
                    'agent_type': agent_type,
                    'data': serializer.data
                })
            else:
                errors.append({
                    'index': idx,
                    'errors': serializer.errors
                })
                
        except Exception as e:
            logger.error(f"Error saving item {idx}: {str(e)}")
            errors.append({
                'index': idx,
                'error': str(e)
            })
    
    return Response({
        'success': len(errors) == 0,
        'saved_count': len(saved_items),
        'error_count': len(errors),
        'saved_items': saved_items,
        'errors': errors
    }, status=status.HTTP_201_CREATED if saved_items else status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([AllowAny])
def delete_session(request, session_id):
    """
    Delete a specific agent session and all its messages.
    """
    try:
        session = AgentSession.objects.get(
            session_id=session_id,
            user=request.user if request.user.is_authenticated else None
        )
        session.delete()
        return Response({'success': True}, status=status.HTTP_204_NO_CONTENT)
    except AgentSession.DoesNotExist:
        return Response({
            'error': 'Session not found or does not belong to user'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_session_saved_items(request, session_id):
    """
    Get all items saved from a specific agent session
    Returns meal plans, tasks, study sessions, and wellness activities
    """
    try:
        session = AgentSession.objects.get(
            session_id=session_id,
            user=request.user if request.user.is_authenticated else None
        )
    except AgentSession.DoesNotExist:
        return Response({
            'error': 'Session not found or does not belong to user'
        }, status=status.HTTP_404_NOT_FOUND)
    
    # Gather all related items
    meal_plans = MealPlan.objects.filter(session=session)
    tasks = Task.objects.filter(session=session)
    study_sessions = StudySession.objects.filter(session=session)
    wellness_activities = WellnessActivity.objects.filter(session=session)
    
    return Response({
        'session_id': session_id,
        'saved_items': {
            'meal_plans': MealPlanSerializer(meal_plans, many=True).data,
            'tasks': TaskSerializer(tasks, many=True).data,
            'study_sessions': StudySessionSerializer(study_sessions, many=True).data,
            'wellness_activities': WellnessActivitySerializer(wellness_activities, many=True).data,
        },
        'total_count': (
            meal_plans.count() + 
            tasks.count() + 
            study_sessions.count() + 
            wellness_activities.count()
        )
    }, status=status.HTTP_200_OK)
