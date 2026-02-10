from rest_framework import serializers


class ChatMessageSerializer(serializers.Serializer):
    """Serializer for chat messages to orchestrator"""
    message = serializers.CharField(required=True, max_length=5000)
    session_id = serializers.CharField(required=False, allow_null=True)
    force_agent = serializers.ChoiceField(
        required=False,
        allow_null=True,
        choices=['meal_planner_agent', 'productivity_agent', 'study_agent', 'wellness_agent', 'shopping_agent']
    )


class ChatResponseSerializer(serializers.Serializer):
    """Serializer for orchestrator responses"""
    success = serializers.BooleanField()
    response = serializers.JSONField(required=False)
    agent = serializers.CharField(required=False)
    intent_classification = serializers.JSONField(required=False)
    session_id = serializers.CharField(required=False)
    error = serializers.CharField(required=False)
