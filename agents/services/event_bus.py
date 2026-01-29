"""
Event bus for handling system-wide events and message passing
"""
from typing import Dict, Any, Optional, Callable, List
from datetime import datetime
from agents.models import Event, AuditLog, AgentSession, User
import logging

logger = logging.getLogger(__name__)


class EventBus:
    """
    Message bus pattern implementation for agent coordination
    Manages event flow: INTENT_RECEIVED → AGENT_SELECTED → CONTEXT_FETCHED → 
                        AGENT_RESPONSE → ACTIONS_APPLIED → AUDIT_LOGGED
    """
    
    def __init__(self):
        self._handlers: Dict[str, List[Callable]] = {}
        self._middleware: List[Callable] = []
    
    def subscribe(self, event_type: str, handler: Callable):
        """Subscribe a handler to an event type"""
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.info(f"Handler subscribed to {event_type}")
    
    def unsubscribe(self, event_type: str, handler: Callable):
        """Unsubscribe a handler from an event type"""
        if event_type in self._handlers and handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.info(f"Handler unsubscribed from {event_type}")
    
    def add_middleware(self, middleware: Callable):
        """Add middleware to process events before handlers"""
        self._middleware.append(middleware)
    
    async def publish(
        self, 
        event_type: str, 
        payload: Dict[str, Any],
        session: Optional[AgentSession] = None,
        user: Optional[User] = None,
        parent_event: Optional[Event] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Event:
        """
        Publish an event to the bus
        
        Args:
            event_type: Type of event (e.g., 'INTENT_RECEIVED')
            payload: Event data
            session: Agent session if applicable
            user: User who triggered the event
            parent_event: Parent event for chaining
            metadata: Additional metadata
            
        Returns:
            Created Event instance
        """
        # Create event record
        event = Event.objects.create(
            event_type=event_type,
            session=session,
            user=user,
            payload=payload,
            metadata=metadata or {},
            parent_event=parent_event
        )
        
        logger.info(f"Event published: {event_type} (ID: {event.id})")
        
        # Apply middleware
        for middleware in self._middleware:
            try:
                await middleware(event)
            except Exception as e:
                logger.error(f"Middleware error for {event_type}: {e}")
        
        # Notify handlers
        handlers = self._handlers.get(event_type, [])
        for handler in handlers:
            try:
                await handler(event)
            except Exception as e:
                logger.error(f"Handler error for {event_type}: {e}")
                # Publish error event
                await self.publish(
                    'ERROR_OCCURRED',
                    {
                        'original_event': event_type,
                        'error': str(e),
                        'handler': handler.__name__
                    },
                    session=session,
                    user=user,
                    parent_event=event
                )
        
        return event
    
    def get_event_chain(self, event: Event) -> List[Event]:
        """Get the complete chain of events from root to this event"""
        chain = [event]
        current = event
        
        while current.parent_event:
            current = current.parent_event
            chain.insert(0, current)
        
        return chain


# Singleton instance
event_bus = EventBus()


class AuditLogger:
    """
    Centralized audit logging service
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
        """
        Create an audit log entry
        
        Args:
            action_type: Type of action (USER_ACTION, AGENT_ACTION, etc.)
            action: Description of the action
            details: Detailed information about the action
            user: User who performed the action
            session: Agent session if applicable
            event: Related event
            resource: Resource affected (e.g., "Task:123")
            ip_address: IP address of the requester
            user_agent: User agent string
            success: Whether the action succeeded
            error_message: Error message if action failed
            
        Returns:
            Created AuditLog instance
        """
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
        
        logger.info(f"Audit log created: {action_type} - {action}")
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
