from django.urls import path
from . import views

app_name = 'agents'

urlpatterns = [
    # Agent interaction endpoints
    path('meal-planner/', views.meal_planner_view, name='meal_planner'),
    path('productivity/', views.productivity_agent_view, name='productivity'),
    path('study-buddy/', views.study_buddy_view, name='study_buddy'),
    path('wellness/', views.wellness_agent_view, name='wellness'),
]
