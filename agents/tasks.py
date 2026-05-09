import logging
from celery import shared_task
from asgiref.sync import async_to_sync
from agents.services.orchestrator import orchestrator
from agents.models import AgentSession, User

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def process_agent_message_task(self, message: str, user_id: int, session_id: str = None, force_agent: str = None):
    """
    Background task to process agent message.
    Implements DDIA Ch11: Task Queue for durable execution.
    """
    try:
        user = User.objects.get(id=user_id)
        session = AgentSession.objects.filter(session_id=session_id).first() if session_id else None

        # We use async_to_sync because orchestrator is fully async now
        result = async_to_sync(orchestrator.process_message)(
            message=message,
            user=user,
            session=session,
            force_agent=force_agent
        )

        if not result.get('success'):
            logger.error(f"Agent processing failed in background task: {result.get('error')}")
            # Could raise exception here to trigger retry, depending on error type

        return result

    except Exception as exc:
        logger.error(f"Task failed: {exc}", exc_info=True)
        # Retry exponentially backoff
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)
