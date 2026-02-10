from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
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
    queryset = MealPlan.objects.all()
    serializer_class = MealPlanSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current user if authenticated
        if self.request.user.is_authenticated:
            queryset = queryset.filter(user=self.request.user)
        
        date = self.request.query_params.get('date')
        meal_type = self.request.query_params.get('meal_type')
        
        if date:
            queryset = queryset.filter(date=date)
        if meal_type:
            queryset = queryset.filter(meal_type=meal_type)
        
        return queryset
    
    def perform_create(self, serializer):
        # Automatically assign current user if authenticated
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all()
    serializer_class = TaskSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current user if authenticated
        if self.request.user.is_authenticated:
            queryset = queryset.filter(user=self.request.user)
        
        status_param = self.request.query_params.get('status')
        priority = self.request.query_params.get('priority')
        
        if status_param:
            queryset = queryset.filter(status=status_param)
        if priority:
            queryset = queryset.filter(priority=priority)
        
        return queryset
    
    def perform_create(self, serializer):
        # Automatically assign current user if authenticated
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()


class StudySessionViewSet(viewsets.ModelViewSet):
    queryset = StudySession.objects.all()
    serializer_class = StudySessionSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current user if authenticated
        if self.request.user.is_authenticated:
            queryset = queryset.filter(user=self.request.user)
        return queryset
    
    def perform_create(self, serializer):
        # Automatically assign current user if authenticated
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()


class WellnessActivityViewSet(viewsets.ModelViewSet):
    queryset = WellnessActivity.objects.all()
    serializer_class = WellnessActivitySerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by current user if authenticated
        if self.request.user.is_authenticated:
            queryset = queryset.filter(user=self.request.user)
        
        activity_type = self.request.query_params.get('activity_type')
        
        if activity_type:
            queryset = queryset.filter(activity_type=activity_type)
        
        return queryset
    
    def perform_create(self, serializer):
        # Automatically assign current user if authenticated
        if self.request.user.is_authenticated:
            serializer.save(user=self.request.user)
        else:
            serializer.save()


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
