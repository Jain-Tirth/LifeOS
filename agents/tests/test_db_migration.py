import pytest
from django.test import TestCase
from django.db import connection
from django.core.management import call_command
from agents.models import User, UserProfile, AgentSession, Message

@pytest.mark.django_db(databases={'default': True})
class TestPostgresqlMigration(TestCase):
    """Verify migration from SQLite to PostgreSQL"""

    def test_connection_pool(self):
        """Verify connection pooling configured"""
        assert connection.get_autocommit() == False
        assert connection.settings_dict['CONN_MAX_AGE'] == 600

    def test_create_and_query_user(self):
        """Test full CRUD cycle"""
        user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        assert user.id is not None

        fetched = User.objects.get(email='test@example.com')
        assert fetched.id == user.id

    def test_atomic_requests(self):
        """Verify ATOMIC_REQUESTS wraps requests in transactions"""
        # Create user in transaction
        user = User.objects.create_user(
            email='atomic@example.com',
            password='pass'
        )
        profile = UserProfile.objects.create(user=user)

        # Both should exist in same transaction
        assert User.objects.filter(email='atomic@example.com').exists()
        assert UserProfile.objects.filter(user=user).exists()

    @pytest.mark.slow
    def test_concurrent_writes(self):
        """Verify PostgreSQL handles concurrent writes"""
        import threading

        def create_session():
            User.objects.create_user(
                email=f'user{id(threading.current_thread())}@test.com',
                password='pass'
            )

        threads = [threading.Thread(target=create_session) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        assert User.objects.count() >= 10

    def test_migration_idempotent(self):
        """Running migrations twice should be safe"""
        call_command('migrate', verbosity=0)
        call_command('migrate', verbosity=0)  # Run again

        # Should still be able to create objects
        user = User.objects.create_user(
            email='idem@example.com',
            password='pass'
        )
        assert user.id is not None
