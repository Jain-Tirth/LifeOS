"""
Context manager for handling agent session context and memory
"""
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
from agents.models import AgentContext, AgentSession, Message
from django.utils import timezone
from django.db import models
from asgiref.sync import sync_to_async
import json
import logging

logger = logging.getLogger(__name__)


class ContextManager:
    """
    Manages context for agent sessions including conversation history,
    user preferences, and temporal context
    """
    
    def __init__(self, session: AgentSession):
        self.session = session
    
    async def get_context(self, context_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Retrieve context for the session
        
        Args:
            context_type: Optional filter by context type
            
        Returns:
            Dictionary of context data
        """
        @sync_to_async
        def _get_contexts():
            query = AgentContext.objects.filter(session=self.session)
            
            # Filter expired contexts
            query = query.filter(
                models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=timezone.now())
            )
            
            if context_type:
                query = query.filter(context_type=context_type)
            
            contexts = {}
            for ctx in query:
                if ctx.context_type not in contexts:
                    contexts[ctx.context_type] = {}
                contexts[ctx.context_type][ctx.key] = ctx.value
            
            return contexts
        
        return await _get_contexts()
    
    async def set_context(
        self,
        context_type: str,
        key: str,
        value: Any,
        expires_in_hours: Optional[int] = None
    ) -> AgentContext:
        """
        Store context for the session
        
        Args:
            context_type: Type of context (USER_PREFERENCES, etc.)
            key: Context key identifier
            value: Context data (will be JSON serialized)
            expires_in_hours: Optional expiration time in hours
            
        Returns:
            Created or updated AgentContext
        """
        expires_at = None
        if expires_in_hours:
            expires_at = timezone.now() + timedelta(hours=expires_in_hours)
        
        context, created = await sync_to_async(AgentContext.objects.update_or_create)(
            session=self.session,
            context_type=context_type,
            key=key,
            defaults={
                'value': value,
                'expires_at': expires_at
            }
        )
        
        action = "Created" if created else "Updated"
        logger.info(f"{action} context: {context_type}.{key} for session {self.session.session_id}")
        
        return context
    
    async def get_conversation_history(self, limit: int = 10) -> List[Dict[str, str]]:
        """
        Get recent conversation history for the session
        
        Args:
            limit: Maximum number of messages to retrieve
            
        Returns:
            List of message dictionaries
        """
        @sync_to_async
        def _get_messages():
            messages = Message.objects.filter(
                session=self.session
            ).order_by('-created_at')[:limit]
            
            return [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.created_at.isoformat()
                }
                for msg in reversed(list(messages))
            ]
        
        return await _get_messages()
    
    async def get_user_preferences(self) -> Dict[str, Any]:
        """
        Get user preferences from context
        
        Returns:
            Dictionary of user preferences
        """
        contexts = await self.get_context('USER_PREFERENCES')
        return contexts.get('USER_PREFERENCES', {})
    
    async def set_user_preference(self, key: str, value: Any):
        """
        Set a user preference
        
        Args:
            key: Preference key
            value: Preference value
        """
        preferences = await self.get_user_preferences()
        preferences[key] = value
        
        await self.set_context(
            context_type='USER_PREFERENCES',
            key=key,
            value=value
        )
    
    async def get_temporal_context(self) -> Dict[str, Any]:
        """
        Get temporal context (time of day, day of week, etc.)
        
        Returns:
            Dictionary with temporal information
        """
        now = timezone.now()
        
        return {
            'timestamp': now.isoformat(),
            'time_of_day': self._get_time_of_day(now),
            'day_of_week': now.strftime('%A'),
            'date': now.date().isoformat(),
            'hour': now.hour,
            'is_weekend': now.weekday() >= 5
        }
    
    def _get_time_of_day(self, dt: datetime) -> str:
        """Categorize time of day"""
        hour = dt.hour
        if 5 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 17:
            return 'afternoon'
        elif 17 <= hour < 21:
            return 'evening'
        else:
            return 'night'
    
    async def build_full_context(self) -> Dict[str, Any]:
        """
        Build complete context for agent interaction
        
        Returns:
            Comprehensive context dictionary
        """
        return {
            'conversation_history': await self.get_conversation_history(),
            'user_preferences': await self.get_user_preferences(),
            'temporal_context': await self.get_temporal_context(),
            'session_contexts': await self.get_context()
        }
    
    async def cleanup_expired_contexts(self):
        """Remove expired contexts from the database"""
        deleted_count = AgentContext.objects.filter(
            session=self.session,
            expires_at__lt=timezone.now()
        ).delete()[0]
        
        if deleted_count > 0:
            logger.info(f"Cleaned up {deleted_count} expired contexts for session {self.session.session_id}")


# Import models here to avoid circular import
from django.db import models
