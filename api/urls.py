from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from . import views
from . import auth_views

router = DefaultRouter()
router.register(r'tasks', views.TaskViewSet, basename='task')

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
    path('auth/password-reset/', auth_views.request_password_reset, name='request-password-reset'),
    path('auth/password-reset-confirm/', auth_views.reset_password, name='reset-password'),
    
    # Health check
    path('health/', views.health_check, name='health-check'),

    # Task endpoints
    path('', include(router.urls)),
]
