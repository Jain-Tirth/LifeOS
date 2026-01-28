from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json


def meal_planner_view(request):
    """Handle meal planner agent requests"""
    if request.method == 'GET':
        return render(request, 'agents/meal_planner.html')
    return JsonResponse({'status': 'success'})


def productivity_agent_view(request):
    """Handle productivity agent requests"""
    if request.method == 'GET':
        return render(request, 'agents/productivity.html')
    return JsonResponse({'status': 'success'})


def study_buddy_view(request):
    """Handle study buddy agent requests"""
    if request.method == 'GET':
        return render(request, 'agents/study_buddy.html')
    return JsonResponse({'status': 'success'})


def wellness_agent_view(request):
    """Handle wellness agent requests"""
    if request.method == 'GET':
        return render(request, 'agents/wellness.html')
    return JsonResponse({'status': 'success'})
