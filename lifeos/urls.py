"""
URL configuration for LifeOS project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from api.ui_views import chat_ui

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('agents/', include('agents.urls')),
    path('', chat_ui, name='chat_ui'),  # Chat UI at root
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
