from rest_framework import serializers
from backend.execution.logs.models import AgentSession, Message
from backend.tasks.models import Task


class MessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Message
        fields = ['id', 'role', 'content', 'metadata', 'created_at']


class AgentSessionSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    class Meta:
        model = AgentSession
        fields = ['id', 'session_id', 'agent_type', 'created_at', 'updated_at', 'messages']


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
        session_id = validated_data.pop('session_id', None)

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
        validated_data.pop('session_id', None)
        return super().update(instance, validated_data)


