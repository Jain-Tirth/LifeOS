from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action, permission_classes, throttle_classes
from rest_framework.response import Response
from .throttles import AgentMessageThrottle, AgentSessionThrottle, BurstThrottle, AuthRateThrottle
from rest_framework.permissions import IsAuthenticated
from agents.models import (
    AgentSession, 
    Message, 
    MealPlan,
    Task, 
    StudySession,
    WellnessActivity,
    Habit,
    HabitLog
)
from .serializers import (
    AgentSessionSerializer,
    MessageSerializer,
    MealPlanSerializer,
    TaskSerializer,
    StudySessionSerializer,
    WellnessActivitySerializer,
    HabitSerializer,
    HabitLogSerializer
)
from .base_viewsets import UserOwnedViewSet
from agents.services.orchestrator import orchestrator
from asgiref.sync import async_to_sync
import uuid
import logging
import re

logger = logging.getLogger(__name__)

# Maximum message length to prevent prompt injection and cost explosion
MAX_MESSAGE_LENGTH = 4000


def sanitize_input(content):
    """
    Sanitize user input to prevent prompt injection attacks.
    Removes or escapes potentially dangerous patterns.
    """
    if not content:
        return content
    
    # Remove potential system prompt injection patterns
    dangerous_patterns = [
        r'(?i)ignore\s+previous\s+instructions',
        r'(?i)system:\s*',
        r'(?i)you\s+are\s+now',
        r'(?i)forget\s+all',
        r'(?i)bypass\s+',
        r'(?i)override\s+',
    ]
    
    sanitized = content
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '[REMOVED]', sanitized)
    
    return sanitized.strip()


class AgentSessionViewSet(viewsets.ModelViewSet):
    queryset = AgentSession.objects.all()
    serializer_class = AgentSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AgentSession.objects.filter(user=self.request.user).order_by('-updated_at')
    
    @action(detail=True, methods=['post'], throttle_classes=[AgentMessageThrottle, BurstThrottle])
    def send_message(self, request, pk=None):
        """Send a message to an agent session with input validation and sanitization"""
        session = self.get_object()
        content = request.data.get('content', '').strip()
        
        # Validate content presence
        if not content:
            return Response(
                {'error': 'Content is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate content length to prevent token limit exhaustion and cost explosion
        if len(content) > MAX_MESSAGE_LENGTH:
            return Response(
                {'error': f'Message exceeds {MAX_MESSAGE_LENGTH} character limit. Please shorten your message.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Sanitize input to prevent prompt injection attacks
        sanitized_content = sanitize_input(content)
        
        # Create user message with sanitized content
        user_message = Message.objects.create(
            session=session,
            role='user',
            content=sanitized_content
        )
        
        result = async_to_sync(orchestrator.process_message)(
            message=sanitized_content,
            user=request.user,
            session=session
        )

        if not result.get('success'):
            return Response(
                {'error': result.get('error', 'Failed to process message')},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        agent_response = Message.objects.filter(
            session=session,
            role='agent'
        ).order_by('-created_at').first()

        if not agent_response:
            return Response(
                {'error': 'Agent response was not created'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        return Response({
            'user_message': MessageSerializer(user_message).data,
            'agent_response': MessageSerializer(agent_response).data
        })


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Message.objects.filter(session__user=self.request.user).order_by('created_at')


class MealPlanViewSet(UserOwnedViewSet):
    """ViewSet for managing meal plans with enhanced save-to-agent logic"""
    queryset = MealPlan.objects.all()
    serializer_class = MealPlanSerializer

    def get_queryset(self):
        """Filter meal plans by user and query parameters"""
        queryset = super().get_queryset()

        # Support query parameters for filtering
        date = self.request.query_params.get('date')
        meal_type = self.request.query_params.get('meal_type')
        session_id = self.request.query_params.get('session_id')

        if date:
            queryset = queryset.filter(date=date)
        if meal_type:
            queryset = queryset.filter(meal_type=meal_type)
        if session_id:
            queryset = queryset.filter(session__session_id=session_id)

        return queryset.order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """Override create to add custom response with success message"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response({
            'success': True,
            'message': 'Meal plan saved successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)


class TaskViewSet(UserOwnedViewSet):
    """ViewSet for managing tasks with enhanced save-to-agent logic"""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    
    def get_queryset(self):
        """Filter tasks by user and query parameters"""
        queryset = super().get_queryset()
        
        # Support query parameters for filtering
        status_param = self.request.query_params.get('status')
        priority = self.request.query_params.get('priority')
        session_id = self.request.query_params.get('session_id')
        
        if status_param:
            queryset = queryset.filter(status=status_param)
        if priority:
            queryset = queryset.filter(priority=priority)
        if session_id:
            queryset = queryset.filter(session__session_id=session_id)
        
        return queryset.order_by('-priority', 'due_date', '-created_at')
    
    def create(self, request, *args, **kwargs):
        """Override create to add custom response with success message"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        return Response({
            'success': True,
            'message': 'Task saved successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)
    
    def perform_update(self, serializer):
        """Update task with logging"""
        try:
            serializer.save()
            logger.info(f"Task updated successfully")
        except Exception as e:
            logger.error(f"Error updating task: {str(e)}")
            raise


class StudySessionViewSet(UserOwnedViewSet):
    """ViewSet for managing study sessions with enhanced save-to-agent logic"""
    queryset = StudySession.objects.all()
    serializer_class = StudySessionSerializer

    def get_queryset(self):
        """Filter study sessions by user and query parameters"""
        queryset = super().get_queryset()

        # Support query parameters for filtering
        subject = self.request.query_params.get('subject')
        session_id = self.request.query_params.get('session_id')

        if subject:
            queryset = queryset.filter(subject__icontains=subject)
        if session_id:
            queryset = queryset.filter(session__session_id=session_id)

        return queryset.order_by('-created_at')

    def create(self, request, *args, **kwargs):
        """Override create to add custom response with success message"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)

        return Response({
            'success': True,
            'message': 'Study session saved successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)


class WellnessActivityViewSet(UserOwnedViewSet):
    """ViewSet for managing wellness activities with enhanced save-to-agent logic"""
    queryset = WellnessActivity.objects.all()
    serializer_class = WellnessActivitySerializer
    
    def get_queryset(self):
        """Filter wellness activities by user and query parameters"""
        queryset = super().get_queryset()
        
        # Support query parameters for filtering
        activity_type = self.request.query_params.get('activity_type')
        session_id = self.request.query_params.get('session_id')
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        if session_id:
            queryset = queryset.filter(session__session_id=session_id)
        if start_date:
            queryset = queryset.filter(recorded_at__gte=start_date)
        if end_date:
            queryset = queryset.filter(recorded_at__lte=end_date)
        
        return queryset.order_by('-recorded_at')
    
    def create(self, request, *args, **kwargs):
        """Override create to add custom response with success message"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        
        return Response({
            'success': True,
            'message': 'Wellness activity saved successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED, headers=headers)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_check(request):
    """
    Production health check endpoint
    """
    from django.db import connection
    from django.core.cache import cache
    import os

    status_data = {
        'status': 'healthy',
        'database': 'disconnected',
        'redis': 'disconnected',
        'groq_api': 'invalid'
    }

    # Check DB
    try:
        connection.cursor()
        status_data['database'] = 'connected'
    except Exception:
        status_data['status'] = 'unhealthy'

    # Check Redis
    try:
        cache.set('health_check', '1', timeout=1)
        if cache.get('health_check') == '1':
            status_data['redis'] = 'connected'
    except Exception:
        status_data['status'] = 'unhealthy'

    from django.conf import settings
    # Check Groq config
    if getattr(settings, 'GROQ_API_KEY', None) or os.getenv('GROQ_API_KEY'):
        status_data['groq_api'] = 'valid'
    else:
        status_data['status'] = 'unhealthy'

    status_code = status.HTTP_200_OK if status_data['status'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(status_data, status=status_code)

class HabitViewSet(viewsets.ModelViewSet):
    """CRUD for habits + toggle completion + daily digest."""
    queryset = Habit.objects.all()
    serializer_class = HabitSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        qs = Habit.objects.filter(user=self.request.user, is_active=True)
        category = self.request.query_params.get('category')
        if category:
            qs = qs.filter(category=category)
        return qs
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def toggle_today(self, request, pk=None):
        """Toggle habit completion for today. One-click endpoint."""
        from datetime import date, datetime
        
        habit = self.get_object()
        today = date.today()
        
        log, created = HabitLog.objects.get_or_create(
            habit=habit,
            date=today,
            defaults={'completed': True, 'completed_at': datetime.now(), 'count': 1}
        )
        
        if not created:
            log.completed = not log.completed
            log.completed_at = datetime.now() if log.completed else None
            log.count = 1 if log.completed else 0
            log.save()
        
        # Update streak and total completions
        habit.calculate_streak()
        habit.total_completions = habit.logs.filter(completed=True).count()
        habit.save(update_fields=['total_completions'])
        
        return Response({
            'completed': log.completed,
            'current_streak': habit.current_streak,
            'best_streak': habit.best_streak,
            'total_completions': habit.total_completions,
        })
    
    @action(detail=False, methods=['get'])
    def daily_digest(self, request):
        """Get today's habit summary: which habits are due, which are done."""
        from datetime import date
        
        today = date.today()
        habits = self.get_queryset()
        
        digest = []
        for habit in habits:
            log = habit.logs.filter(date=today).first()
            digest.append({
                'id': habit.id,
                'name': habit.name,
                'icon': habit.icon,
                'color': habit.color,
                'category': habit.category,
                'completed': log.completed if log else False,
                'current_streak': habit.current_streak,
                'target_count': habit.target_count,
                'actual_count': log.count if log else 0,
            })
        
        completed_count = sum(1 for h in digest if h['completed'])
        return Response({
            'date': str(today),
            'total': len(digest),
            'completed': completed_count,
            'pending': len(digest) - completed_count,
            'completion_rate': round(completed_count / max(len(digest), 1) * 100),
            'habits': digest,
        })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@throttle_classes([AgentSessionThrottle])
def create_agent_session(request):
    """Create a new agent session"""
    agent_type = request.data.get('agent_type')
    
    if not agent_type:
        return Response(
            {'error': 'agent_type is required'}, 
            status=status.HTTP_400_BAD_REQUEST
        )
    
    session = AgentSession.objects.create(
        agent_type=agent_type,
        session_id=str(uuid.uuid4()),
        user=request.user if request.user.is_authenticated else None
    )
    
    serializer = AgentSessionSerializer(session)
    return Response(serializer.data, status=status.HTTP_201_CREATED)
