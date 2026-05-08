from django.urls import path
from . import views
from .views import google_oauth

app_name = 'agents'

urlpatterns = [
    # Agent interaction endpoints
    path('productivity/', views.productivity_agent_view, name='productivity'),
    path('wellness/', views.wellness_agent_view, name='wellness'),
    
    # Google OAuth endpoints
    path('auth/google/', google_oauth.google_oauth_start, name='google_oauth_start'),
    path('auth/google/callback/', google_oauth.google_oauth_callback, name='google_oauth_callback'),
]
