from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from . import views
from . import auth_views
from . import orchestrator_views

router = DefaultRouter()
router.register(r'sessions', views.AgentSessionViewSet, basename='agent-session')
router.register(r'messages', views.MessageViewSet, basename='message')
router.register(r'tasks', views.TaskViewSet, basename='task')
router.register(r'wellness-activities', views.WellnessActivityViewSet, basename='wellness-activity')
router.register(r'habits', views.HabitViewSet, basename='habit')

@api_view(['GET'])
def health_check(request):
    """Health check endpoint for Cloud Run"""
    from django.db import connection
    try:
        # Test database connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        return Response({
            'status': 'healthy',
            'database': 'connected'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'status': 'unhealthy',
            'database': 'disconnected',
            'error': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)


urlpatterns = [
    # Health check endpoint (no auth required)
    path('health/', health_check, name='health-check'),
    
    # Authentication endpoints
    path('auth/csrf/', auth_views.get_csrf_token, name='get-csrf-token'),
    path('auth/register/', auth_views.register, name='register'),
    path('auth/login/', auth_views.login, name='login'),
    path('auth/logout/', auth_views.logout, name='logout'),
    path('auth/refresh/', auth_views.refresh_token, name='refresh-token'),
    path('auth/profile/', auth_views.get_user_profile, name='user-profile'),
    path('auth/profile/update/', auth_views.update_user_profile, name='update-profile'),
    path('auth/preferences/', auth_views.update_user_preferences, name='update-preferences'),
    
    # Orchestrator endpoints
    path('chat/', orchestrator_views.chat, name='chat'),
    path('chat/stream/', orchestrator_views.chat_stream, name='chat-stream'),
    path('agents/', orchestrator_views.get_available_agents, name='available-agents'),
    path('my-sessions/', orchestrator_views.get_user_sessions, name='user-sessions'),
    path('sessions/<str:session_id>/messages/', orchestrator_views.get_session_messages, name='session-messages'),
    path('sessions/<str:session_id>/delete/', orchestrator_views.delete_session, name='delete-session'),
    
    # Save agent data endpoints
    path('save-agent-response/', orchestrator_views.save_agent_response, name='save-agent-response'),
    path('bulk-save-agent-responses/', orchestrator_views.bulk_save_agent_responses, name='bulk-save-agent-responses'),
    path('sessions/<str:session_id>/saved-items/', orchestrator_views.get_session_saved_items, name='session-saved-items'),
    
    # Agent and data endpoints
    path('', include(router.urls)),
    path('create-session/', views.create_agent_session, name='create-session'),
]
