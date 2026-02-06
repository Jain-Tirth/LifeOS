from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import auth_views
from . import orchestrator_views

router = DefaultRouter()
router.register(r'sessions', views.AgentSessionViewSet, basename='agent-session')
router.register(r'messages', views.MessageViewSet, basename='message')
router.register(r'meal-plans', views.MealPlanViewSet, basename='meal-plan')
router.register(r'tasks', views.TaskViewSet, basename='task')
router.register(r'study-sessions', views.StudySessionViewSet, basename='study-session')
router.register(r'wellness-activities', views.WellnessActivityViewSet, basename='wellness-activity')

urlpatterns = [
    # Authentication endpoints
    path('auth/register/', auth_views.register, name='register'),
    path('auth/login/', auth_views.login, name='login'),
    path('auth/profile/', auth_views.get_user_profile, name='user-profile'),
    path('auth/profile/update/', auth_views.update_user_profile, name='update-profile'),
    
    # Orchestrator endpoints
    path('chat/', orchestrator_views.chat, name='chat'),
    path('chat/stream/', orchestrator_views.chat_stream, name='chat-stream'),
    path('agents/', orchestrator_views.get_available_agents, name='available-agents'),
    path('my-sessions/', orchestrator_views.get_user_sessions, name='user-sessions'),
    path('sessions/<str:session_id>/messages/', orchestrator_views.get_session_messages, name='session-messages'),
    
    # Agent and data endpoints
    path('', include(router.urls)),
    path('create-session/', views.create_agent_session, name='create-session'),
]
