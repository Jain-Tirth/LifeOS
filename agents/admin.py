from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import (
    User,
    AgentSession, 
    Message, 
    MealPlan, 
    Task, 
    StudySession, 
    WellnessActivity,
    Event,
    AuditLog,
    AgentContext
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['email', 'first_name', 'last_name', 'is_staff', 'is_active', 'date_joined']
    list_filter = ['is_staff', 'is_active', 'date_joined']
    search_fields = ['email', 'first_name', 'last_name']
    ordering = ['-date_joined']
    
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'first_name', 'last_name', 'is_staff', 'is_active'),
        }),
    )


@admin.register(AgentSession)
class AgentSessionAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'agent_type', 'user', 'created_at', 'updated_at']
    list_filter = ['agent_type', 'created_at']
    search_fields = ['session_id', 'user__username']


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['session', 'role', 'content_preview', 'created_at']
    list_filter = ['role', 'created_at']
    search_fields = ['content']
    
    def content_preview(self, obj):
        return obj.content[:50] + '...' if len(obj.content) > 50 else obj.content


@admin.register(MealPlan)
class MealPlanAdmin(admin.ModelAdmin):
    list_display = ['meal_name', 'meal_type', 'date', 'user', 'created_at']
    list_filter = ['meal_type', 'date']
    search_fields = ['meal_name', 'ingredients']


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ['title', 'priority', 'status', 'due_date', 'user', 'created_at']
    list_filter = ['priority', 'status', 'due_date']
    search_fields = ['title', 'description']


@admin.register(StudySession)
class StudySessionAdmin(admin.ModelAdmin):
    list_display = ['subject', 'topic', 'duration', 'user', 'created_at']
    list_filter = ['subject', 'created_at']
    search_fields = ['subject', 'topic', 'notes']


@admin.register(WellnessActivity)
class WellnessActivityAdmin(admin.ModelAdmin):
    list_display = ['activity_type', 'duration', 'intensity', 'recorded_at', 'user']
    list_filter = ['activity_type', 'recorded_at']
    search_fields = ['notes']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['event_type', 'session', 'user', 'timestamp', 'parent_event']
    list_filter = ['event_type', 'timestamp']
    search_fields = ['payload']
    readonly_fields = ['timestamp']
    
    def has_add_permission(self, request):
        return False  # Events are created by the system


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ['action_type', 'action', 'user', 'resource', 'success', 'timestamp']
    list_filter = ['action_type', 'success', 'timestamp']
    search_fields = ['action', 'resource', 'details']
    readonly_fields = ['timestamp']
    
    def has_add_permission(self, request):
        return False  # Audit logs are created by the system
    
    def has_delete_permission(self, request, obj=None):
        return False  # Audit logs should not be deleted


@admin.register(AgentContext)
class AgentContextAdmin(admin.ModelAdmin):
    list_display = ['session', 'context_type', 'key', 'expires_at', 'updated_at']
    list_filter = ['context_type', 'updated_at']
    search_fields = ['key', 'value']
    readonly_fields = ['created_at', 'updated_at']
