from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action, permission_classes
from rest_framework.response import Response
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
from agents.services.orchestrator import orchestrator
from asgiref.sync import async_to_sync
import uuid
import logging

logger = logging.getLogger(__name__)


class AgentSessionViewSet(viewsets.ModelViewSet):
    queryset = AgentSession.objects.all()
    serializer_class = AgentSessionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return AgentSession.objects.filter(user=self.request.user).order_by('-updated_at')
    
    @action(detail=True, methods=['post'])
    def send_message(self, request, pk=None):
        """Send a message to an agent session"""
        session = self.get_object()
        content = request.data.get('content')
        
        if not content:
            return Response(
                {'error': 'Content is required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create user message
        user_message = Message.objects.create(
            session=session,
            role='user',
            content=content
        )
        
        result = async_to_sync(orchestrator.process_message)(
            message=content,
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


class MealPlanViewSet(viewsets.ModelViewSet):
    """ViewSet for managing meal plans with enhanced save-to-agent logic"""
    queryset = MealPlan.objects.all()
    serializer_class = MealPlanSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter meal plans by user and query parameters"""
        queryset = super().get_queryset()
        
        # Filter by current user if authenticated
        if self.request.user.is_authenticated:
            queryset = queryset.filter(user=self.request.user)
        
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
    
    def perform_create(self, serializer):
        """Save meal plan with automatic user assignment"""
        try:
            # Automatically assign current user if authenticated
            if self.request.user.is_authenticated:
                serializer.save(user=self.request.user)
            else:
                serializer.save()
            
            logger.info(f"Meal plan created successfully from agent")
        except Exception as e:
            logger.error(f"Error creating meal plan: {str(e)}")
            raise
    
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


class TaskViewSet(viewsets.ModelViewSet):
    """ViewSet for managing tasks with enhanced save-to-agent logic"""
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter tasks by user and query parameters"""
        queryset = super().get_queryset()
        
        # Filter by current user if authenticated
        if self.request.user.is_authenticated:
            queryset = queryset.filter(user=self.request.user)
        
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
    
    def perform_create(self, serializer):
        """Save task with automatic user assignment"""
        try:
            # Automatically assign current user if authenticated
            if self.request.user.is_authenticated:
                serializer.save(user=self.request.user)
            else:
                serializer.save()
            
            logger.info(f"Task created successfully from agent")
        except Exception as e:
            logger.error(f"Error creating task: {str(e)}")
            raise
    
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


class StudySessionViewSet(viewsets.ModelViewSet):
    """ViewSet for managing study sessions with enhanced save-to-agent logic"""
    queryset = StudySession.objects.all()
    serializer_class = StudySessionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter study sessions by user and query parameters"""
        queryset = super().get_queryset()
        
        # Filter by current user if authenticated
        if self.request.user.is_authenticated:
            queryset = queryset.filter(user=self.request.user)
        
        # Support query parameters for filtering
        subject = self.request.query_params.get('subject')
        session_id = self.request.query_params.get('session_id')
        
        if subject:
            queryset = queryset.filter(subject__icontains=subject)
        if session_id:
            queryset = queryset.filter(session__session_id=session_id)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        """Save study session with automatic user assignment"""
        try:
            # Automatically assign current user if authenticated
            if self.request.user.is_authenticated:
                serializer.save(user=self.request.user)
            else:
                serializer.save()
            
            logger.info(f"Study session created successfully from agent")
        except Exception as e:
            logger.error(f"Error creating study session: {str(e)}")
            raise
    
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


class WellnessActivityViewSet(viewsets.ModelViewSet):
    """ViewSet for managing wellness activities with enhanced save-to-agent logic"""
    queryset = WellnessActivity.objects.all()
    serializer_class = WellnessActivitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """Filter wellness activities by user and query parameters"""
        queryset = super().get_queryset()
        
        # Filter by current user if authenticated
        if self.request.user.is_authenticated:
            queryset = queryset.filter(user=self.request.user)
        
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
    
    def perform_create(self, serializer):
        """Save wellness activity with automatic user assignment"""
        try:
            # Automatically assign current user if authenticated
            if self.request.user.is_authenticated:
                serializer.save(user=self.request.user)
            else:
                serializer.save()
            
            logger.info(f"Wellness activity created successfully from agent")
        except Exception as e:
            logger.error(f"Error creating wellness activity: {str(e)}")
            raise
    
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
