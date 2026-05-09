import pytest
from rest_framework.test import APIClient
from agents.models import User
from unittest.mock import patch
import uuid

@pytest.mark.django_db
class TestRateLimiting:
    """Verify rate limiting protects against abuse"""

    @pytest.fixture
    def client_with_user(self):
        user = User.objects.create_user(
            email='ratelimit@test.com',
            password='pass'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        return client, user

    def test_session_creation_throttle(self, client_with_user):
        """Max 5 sessions per hour"""
        client, user = client_with_user

        # We need to simulate the redis cache or django cache throttling behavior.
        # Ensure that django cache is setup for throttling tests (usually locmem works fine).

        # Create 5 sessions (should succeed)
        for i in range(5):
            response = client.post(
                '/api/create-session/',
                {'agent_type': 'meal_planner'},
                format='json'
            )
            assert response.status_code == 201

        # 6th session should be throttled
        response = client.post(
            '/api/create-session/',
            {'agent_type': 'meal_planner'},
            format='json'
        )
        assert response.status_code == 429

    def test_agent_message_throttle(self, client_with_user):
        """Max 10 messages per minute"""
        client, user = client_with_user

        from django.core.cache import cache
        cache.clear()

        # Need to create a session first
        response = client.post(
            '/api/create-session/',
            {'agent_type': 'meal_planner'},
            format='json'
        )
        session_id = response.json().get('id') or response.json().get('session_id')

        # Use mocked orchestrator to avoid external api calls
        with patch('agents.services.orchestrator.orchestrator.process_message') as mock_process:
            mock_process.return_value = {"success": True}

            # Use mock to patch the orchestrator
            with patch('agents.services.orchestrator.orchestrator.process_message') as mock_process:
                import asyncio

                async def mock_process_message(*args, **kwargs):
                    return {"success": True}

                mock_process.side_effect = mock_process_message

                # Send 10 messages (should succeed)
                for i in range(10):
                    # For a valid run, also mock the Message creation that usually happens inside orchestrator
                    from agents.models import Message
                    Message.objects.create(session_id=session_id, role='agent', content='test')

                    response = client.post(
                        f'/api/sessions/{session_id}/send_message/',
                        {'content': f'message {i}'},
                        format='json'
                    )
                    assert response.status_code in [200, 201]  # Not throttled

                # 11th message should be throttled
                response = client.post(
                    f'/api/sessions/{session_id}/send_message/',
                    {'content': 'message 11'},
                    format='json'
                )
            assert response.status_code == 429  # Throttled
            assert 'Retry-After' in response.headers or 'Retry-After' in response
