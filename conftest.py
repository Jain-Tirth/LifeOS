"""
Pytest configuration for LifeOS.
Sets up Django settings and test fixtures.
"""
import os
import pytest
import django
from django.conf import settings

# Configure Django settings before importing models
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'lifeos.settings')

# Setup Django
django.setup()

@pytest.fixture(scope='session')
def django_db_setup():
    """Ensure database is configured for tests"""
    pass

@pytest.fixture
def test_user(db):
    """Create a test user"""
    from agents.models import User
    return User.objects.create_user(
        email='test@example.com',
        password='testpass123'
    )

@pytest.fixture
def test_session(db, test_user):
    """Create a test agent session"""
    from agents.models import AgentSession
    return AgentSession.objects.create(
        user=test_user,
        agent_type='test',
        session_id='test-session-123'
    )
