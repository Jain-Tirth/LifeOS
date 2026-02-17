from rest_framework import serializers
from agents.models import (
    AgentSession, 
    Message, 
    MealPlan, 
    Task, 
    StudySession, 
    WellnessActivity
)


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'role', 'content', 'metadata', 'created_at']


class AgentSessionSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta:
        model = AgentSession
        fields = ['id', 'session_id', 'agent_type', 'created_at', 'updated_at', 'messages']


class MealPlanSerializer(serializers.ModelSerializer):
    """Serializer for meal plans with session_id support"""
    session_id = serializers.CharField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = MealPlan
        fields = ['id', 'date', 'meal_type', 'meal_name', 'ingredients', 
                  'instructions', 'nutritional_info', 'preferences', 
                  'created_at', 'session_id', 'user', 'session']
        read_only_fields = ['id', 'created_at', 'user', 'session']
        extra_kwargs = {
            'user': {'required': False},
            'session': {'required': False},
        }
    
    def create(self, validated_data):
        # Extract session_id if provided
        session_id = validated_data.pop('session_id', None)
        
        # Look up session by session_id (UUID string)
        if session_id:
            try:
                session = AgentSession.objects.get(session_id=session_id)
                validated_data['session'] = session
            except AgentSession.DoesNotExist:
                raise serializers.ValidationError({
                    'session_id': f'Session with id {session_id} does not exist'
                })
        
        return super().create(validated_data)


class TaskSerializer(serializers.ModelSerializer):
    """Serializer for tasks with session_id support"""
    session_id = serializers.CharField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = Task
        fields = ['id', 'title', 'description', 'priority', 'status', 
                  'due_date', 'completed_at', 'created_at', 'updated_at',
                  'session_id', 'user', 'session']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user', 'session']
        extra_kwargs = {
            'user': {'required': False},
            'session': {'required': False},
        }
    
    def create(self, validated_data):
        # Extract session_id if provided
        session_id = validated_data.pop('session_id', None)
        
        # Look up session by session_id (UUID string)
        if session_id:
            try:
                session = AgentSession.objects.get(session_id=session_id)
                validated_data['session'] = session
            except AgentSession.DoesNotExist:
                raise serializers.ValidationError({
                    'session_id': f'Session with id {session_id} does not exist'
                })
        
        return super().create(validated_data)
    
    def update(self, instance, validated_data):
        # Remove session_id from update if provided (shouldn't be changed)
        validated_data.pop('session_id', None)
        return super().update(instance, validated_data)


class StudySessionSerializer(serializers.ModelSerializer):
    """Serializer for study sessions with session_id support"""
    session_id = serializers.CharField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = StudySession
        fields = ['id', 'subject', 'topic', 'duration', 'notes', 
                  'resources', 'created_at', 'session_id', 'user', 'session']
        read_only_fields = ['id', 'created_at', 'user', 'session']
        extra_kwargs = {
            'user': {'required': False},
            'session': {'required': False},
        }
    
    def create(self, validated_data):
        # Extract session_id if provided
        session_id = validated_data.pop('session_id', None)
        
        # Look up session by session_id (UUID string)
        if session_id:
            try:
                session = AgentSession.objects.get(session_id=session_id)
                validated_data['session'] = session
            except AgentSession.DoesNotExist:
                raise serializers.ValidationError({
                    'session_id': f'Session with id {session_id} does not exist'
                })
        
        return super().create(validated_data)


class WellnessActivitySerializer(serializers.ModelSerializer):
    """Serializer for wellness activities with session_id support"""
    session_id = serializers.CharField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = WellnessActivity
        fields = ['id', 'activity_type', 'duration', 'intensity', 'notes', 
                  'metadata', 'recorded_at', 'created_at', 'session_id', 'user', 'session']
        read_only_fields = ['id', 'created_at', 'user', 'session']
        extra_kwargs = {
            'user': {'required': False},
            'session': {'required': False},
        }
    
    def create(self, validated_data):
        # Extract session_id if provided
        session_id = validated_data.pop('session_id', None)
        
        # Look up session by session_id (UUID string)
        if session_id:
            try:
                session = AgentSession.objects.get(session_id=session_id)
                validated_data['session'] = session
            except AgentSession.DoesNotExist:
                raise serializers.ValidationError({
                    'session_id': f'Session with id {session_id} does not exist'
                })
        
        return super().create(validated_data)