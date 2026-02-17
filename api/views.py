from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from agents.models import (
    AgentSession, 
    Message, 
    MealPlan, 
    Task, 
    StudySession, 
    WellnessActivity
)
from .serializers import (
    AgentSessionSerializer,
    MessageSerializer,
    MealPlanSerializer,
    TaskSerializer,
    StudySessionSerializer,
    WellnessActivitySerializer
)
import uuid
import logging

logger = logging.getLogger(__name__)


class AgentSessionViewSet(viewsets.ModelViewSet):
    queryset = AgentSession.objects.all()
    serializer_class = AgentSessionSerializer
    
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
        
        # TODO: Process with actual agent and get response
        # For now, create a placeholder response
        agent_response = Message.objects.create(
            session=session,
            role='agent',
            content='This is a placeholder response. Agent integration pending.'
        )
        
        return Response({
            'user_message': MessageSerializer(user_message).data,
            'agent_response': MessageSerializer(agent_response).data
        })


class MessageViewSet(viewsets.ModelViewSet):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer


class MealPlanViewSet(viewsets.ModelViewSet):
    """ViewSet for managing meal plans with enhanced save-to-agent logic"""
    queryset = MealPlan.objects.all()
    serializer_class = MealPlanSerializer
    permission_classes = [AllowAny]  # Allow unauthenticated users to save
    
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
    permission_classes = [AllowAny]  # Allow unauthenticated users to save
    
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
    permission_classes = [AllowAny]  # Allow unauthenticated users to save
    
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
    permission_classes = [AllowAny]  # Allow unauthenticated users to save
    
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


@api_view(['POST'])
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
