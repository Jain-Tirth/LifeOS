import pytest
from agents.models import Event, AgentSession, User
from agents.services.event_bus import event_bus

@pytest.mark.django_db
@pytest.mark.asyncio
class TestEventSourcing:
    """Verify event bus persistence"""

    @pytest.fixture
    async def user_and_session(self):
        from asgiref.sync import sync_to_async
        import uuid
        test_email = f"events_{uuid.uuid4()}@test.com"
        user = await sync_to_async(User.objects.create_user)(
            email=test_email,
            password='pass'
        )
        session = await AgentSession.objects.acreate(
            user=user,
            agent_type='test',
            session_id=str(uuid.uuid4())
        )
        return user, session

    @pytest.mark.asyncio
    async def test_event_persisted_to_db(self, user_and_session):
        """Events are written to DB, not memory"""
        user, session = await user_and_session

        event = await event_bus.publish(
            'INTENT_RECEIVED',
            payload={'test': 'data'},
            session=session,
            user=user,
            idempotency_key='test-key-1'
        )

        # Verify in DB
        assert event is not None
        assert event.id is not None
        db_event = await Event.objects.aget(id=event.id)
        assert db_event.event_type == 'INTENT_RECEIVED'
        assert db_event.payload['test'] == 'data'

    @pytest.mark.asyncio
    async def test_idempotency_deduplicates(self, user_and_session):
        """Same idempotency key returns existing event"""
        user, session = await user_and_session

        # First call
        event1 = await event_bus.publish(
            'TEST_EVENT',
            payload={'version': 1},
            session=session,
            user=user,
            idempotency_key='dedup-test'
        )

        # Second call with same key
        event2 = await event_bus.publish(
            'TEST_EVENT',
            payload={'version': 2},  # Different payload
            session=session,
            user=user,
            idempotency_key='dedup-test'
        )

        # Should be same event
        assert event1.id == event2.id
        assert event2.payload['version'] == 1  # Original payload preserved

    @pytest.mark.asyncio
    async def test_event_chain_with_parent(self, user_and_session):
        """Events form causal chain"""
        user, session = await user_and_session

        parent = await event_bus.publish(
            'INTENT_RECEIVED',
            payload={},
            session=session,
            user=user,
            idempotency_key='parent-1'
        )

        child = await event_bus.publish(
            'AGENT_SELECTED',
            payload={},
            session=session,
            user=user,
            parent_event=parent,
            idempotency_key='child-1'
        )

        assert child.parent_event.id == parent.id
