from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from backend.tasks.models import Task
from .serializers import TaskSerializer
from .base_viewsets import UserOwnedViewSet
import logging

logger = logging.getLogger(__name__)

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


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_check(request):
    """Production health check endpoint."""
    from django.db import connection
    from django.core.cache import cache
    import os

    status_data = {
        'status': 'healthy',
        'database': 'disconnected',
        'redis': 'disconnected',
        'groq_api': 'invalid'
    }

    try:
        connection.cursor()
        status_data['database'] = 'connected'
    except Exception:
        status_data['status'] = 'unhealthy'

    try:
        cache.set('health_check', '1', timeout=1)
        if cache.get('health_check') == '1':
            status_data['redis'] = 'connected'
    except Exception:
        status_data['status'] = 'unhealthy'

    from django.conf import settings
    if getattr(settings, 'GROQ_API_KEY', None) or os.getenv('GROQ_API_KEY'):
        status_data['groq_api'] = 'valid'
    else:
        status_data['status'] = 'unhealthy'

    status_code = status.HTTP_200_OK if status_data['status'] == 'healthy' else status.HTTP_503_SERVICE_UNAVAILABLE
    return Response(status_data, status=status_code)
