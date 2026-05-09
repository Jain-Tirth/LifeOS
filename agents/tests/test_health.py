import pytest
from rest_framework.test import APIClient
from agents.models import User
import httpx

class TestProductionSmoke:
    """Quick smoke tests after deployment"""

    @pytest.fixture
    def api_client_authenticated(self):
        """Authenticated API client"""
        user = User.objects.create_user(
            email='api@test.com',
            password='apitest123'
        )
        client = APIClient()
        client.force_authenticate(user=user)
        return client, user

    @pytest.mark.django_db
    def test_health_check(self, api_client_authenticated):
        """API is responding"""
        client, user = api_client_authenticated
        response = client.get('/api/health/')
        assert response.status_code == 200
        assert response.json()['status'] == 'healthy'

    @pytest.mark.django_db
    def test_database_connected(self, api_client_authenticated):
        """Database is reachable"""
        client, user = api_client_authenticated
        response = client.get('/api/health/')
        assert response.json()['database'] == 'connected'

    @pytest.mark.django_db
    def test_groq_api_key_valid(self, api_client_authenticated):
        """Groq API configured"""
        client, user = api_client_authenticated
        response = client.get('/api/health/')
        assert response.json()['groq_api'] == 'valid'
