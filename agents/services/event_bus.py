"""
Event bus for handling system-wide events and audit logging.
Slimmed down: removed unused subscriber/middleware infrastructure.
Only writes meaningful events to DB (not every pipeline step).
"""
from typing import Dict, Any, Optional, List
from datetime import datetime
from agents.models import Event, AuditLog, AgentSession, User
from asgiref.sync import sync_to_async
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """
    Lightweight event bus — writes only significant events to DB.
    
    Previous version wrote 6 Event rows per message (INTENT_RECEIVED, AGENT_SELECTED,
    CONTEXT_FETCHED, AGENT_RESPONSE, ACTIONS_APPLIED, AUDIT_LOGGED). That's 6 DB writes
    just for overhead. Now we only persist events that carry real diagnostic value.
    """
    
    # Events worth persisting (the rest are just logged)
    PERSIST_EVENTS = {'AGENT_RESPONSE', 'ACTIONS_APPLIED', 'ERROR_OCCURRED'}
    
    async def publish(
        self, 
        event_type: str, 
        payload: Dict[str, Any],
        session: Optional[AgentSession] = None,
        user: Optional[User] = None,
        parent_event: Optional[Event] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Event]:
        """
        Publish an event. Only persists significant events to DB.
        All events are logged regardless.
        """
        logger.info(f"Event: {event_type} | session={session.session_id if session else 'none'}")
        
        # Only write to DB for significant events
        if event_type in self.PERSIST_EVENTS:
            try:
                event = await sync_to_async(Event.objects.create)(
                    event_type=event_type,
                    session=session,
                    user=user,
                    payload=payload,
                    metadata=metadata or {},
                    parent_event=parent_event
                )
                return event
            except Exception as e:
                logger.error(f"Failed to persist event {event_type}: {e}")
                return None
        
        # Non-persisted events just get logged
        return None


# Singleton instance
event_bus = EventBus()


class AuditLogger:
    """
    Centralized audit logging service.
    Unchanged — audit logs are always valuable.
    """
    
    @staticmethod
    def log(
        action_type: str,
        action: str,
        details: Dict[str, Any],
        user: Optional[User] = None,
        session: Optional[AgentSession] = None,
        event: Optional[Event] = None,
        resource: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AuditLog:
        """Create an audit log entry."""
        audit_log = AuditLog.objects.create(
            action_type=action_type,
            user=user,
            session=session,
            event=event,
            action=action,
            resource=resource,
            details=details,
            ip_address=ip_address,
            user_agent=user_agent,
            success=success,
            error_message=error_message
        )
        
        logger.info(f"Audit: {action_type} - {action}")
        return audit_log
    
    @staticmethod
    def log_user_action(action: str, user: User, details: Dict[str, Any], **kwargs) -> AuditLog:
        """Convenience method for logging user actions"""
        return AuditLogger.log(
            action_type='USER_ACTION',
            action=action,
            details=details,
            user=user,
            **kwargs
        )
    
    @staticmethod
    def log_agent_action(action: str, session: AgentSession, details: Dict[str, Any], **kwargs) -> AuditLog:
        """Convenience method for logging agent actions"""
        return AuditLogger.log(
            action_type='AGENT_ACTION',
            action=action,
            details=details,
            session=session,
            **kwargs
        )
    
    @staticmethod
    def log_authentication(action: str, user: Optional[User], details: Dict[str, Any], **kwargs) -> AuditLog:
        """Convenience method for logging authentication events"""
        return AuditLogger.log(
            action_type='AUTHENTICATION',
            action=action,
            details=details,
            user=user,
            **kwargs
        )


# Singleton instance
audit_logger = AuditLogger()
