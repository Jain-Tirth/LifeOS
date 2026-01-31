"""
Views for serving the chat UI
"""
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt


@csrf_exempt
def chat_ui(request):
    """Render the chat interface"""
    return render(request, 'chat.html')
