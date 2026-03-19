"""
Enhanced agent orchestrator for coordinating multiple AI agents in the LifeOS system.
Now actually wires context → agents and implements ACTIONS_APPLIED.
"""
from typing import Dict, Any, Optional, List
from agents.models import AgentSession, Message, User, UserProfile

# Import Groq-based agents
from .study_agent import study_agent_runner
from .productivity_agent import productivity_agent_runner
from .wellness_agent import wellness_agent_runner
from .meal_planner_agent import meal_planner_agent_runner
from .habit_coach_agent import habit_coach_runner
from .planner_agent import planner_agent_runner
from .knowledge_agent import knowledge_agent_runner

from .event_bus import event_bus, audit_logger
from .intent_classifier import intent_classifier
from .context_manager import ContextManager
from .action_applier import action_applier
from asgiref.sync import sync_to_async
import logging
import uuid
import asyncio

logger = logging.getLogger(__name__)


class EnhancedOrchestrator:
    """
    Enhanced orchestrator with:
    - User context injection into agent calls
    - DB-backed conversation history
    - Optimized intent classification (keyword-first)
    """
    
    def __init__(self):
        self.agents = {
            'study_agent': study_agent_runner,
            'productivity_agent': productivity_agent_runner,
            'wellness_agent': wellness_agent_runner,
            'meal_planner_agent': meal_planner_agent_runner,
            'habit_coach_agent': habit_coach_runner,
            'planner_agent': planner_agent_runner,
            'knowledge_agent': knowledge_agent_runner,
        }

    MAX_AGENT_RETRIES = 2
    DEFAULT_AGENT = 'productivity_agent'

    def _resolve_selected_agent(self, intent_result: Dict[str, Any]) -> str:
        """
        Resolve final agent with confidence and availability fallback behavior.
        """
        candidate = intent_result.get('primary_agent') or self.DEFAULT_AGENT
        confidence = float(intent_result.get('confidence', 0) or 0)
        fallback = intent_result.get('fallback_agent') or self.DEFAULT_AGENT

        if candidate in self.agents and confidence >= 0.2:
            return candidate

        if fallback in self.agents:
            return fallback

        return self.DEFAULT_AGENT

    async def _call_agent_with_retries(
        self,
        agent_runner,
        message: str,
        session_id: str,
        user_context: Dict[str, Any],
    ) -> str:
        """Call an agent with basic retry handling for transient failures."""
        last_error = None
        for attempt in range(1, self.MAX_AGENT_RETRIES + 2):
            try:
                return await agent_runner.run_agent(
                    message,
                    session_id=session_id,
                    user_context=user_context,
                )
            except Exception as exc:
                last_error = exc
                if attempt <= self.MAX_AGENT_RETRIES:
                    backoff_seconds = 0.4 * attempt
                    logger.warning(
                        "Agent call failed (attempt %s/%s). Retrying in %.1fs. Error=%s",
                        attempt,
                        self.MAX_AGENT_RETRIES + 1,
                        backoff_seconds,
                        exc,
                    )
                    await asyncio.sleep(backoff_seconds)
                else:
                    logger.error("Agent call failed after retries: %s", exc)

        raise last_error
    
    async def _get_user_context(self, user: User, agent_type: str = None) -> Dict[str, Any]:
        """
        Load user profile and build agent-specific context.
        This is what makes agents actually personal.
        """
        try:
            profile = await sync_to_async(
                lambda: UserProfile.objects.filter(user=user).first()
            )()
            
            if profile:
                return await sync_to_async(
                    lambda: profile.get_agent_context(agent_type)
                )()
            
            # No profile yet — return minimal context
            return {
                'name': await sync_to_async(user.get_full_name)(),
                'timezone': 'Asia/Kolkata',
            }
        except Exception as e:
            logger.warning(f"Failed to load user context: {e}")
            return {}
    
    async def process_message(
        self,
        message: str,
        user: User,
        session: Optional[AgentSession] = None,
        force_agent: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Process a user message with full orchestration:
        INTENT_RECEIVED → AGENT_SELECTED → CONTEXT_FETCHED → 
        AGENT_RESPONSE → ACTIONS_APPLIED → AUDIT_LOGGED
        """
        try:
            # Create or get session
            if not session:
                session = await sync_to_async(AgentSession.objects.create)(
                    user=user if user.is_authenticated else None,
                    session_id=str(uuid.uuid4()),
                    agent_type='orchestrator'
                )
            
            # Step 1: INTENT_RECEIVED
            intent_event = await event_bus.publish(
                'INTENT_RECEIVED',
                payload={
                    'message': message,
                    'user_id': user.id,
                    'session_id': session.session_id
                },
                session=session,
                user=user if user.is_authenticated else None
            )
            
            # Save user message
            await sync_to_async(Message.objects.create)(
                session=session,
                role='user',
                content=message
            )
            
            # Step 2: AGENT_SELECTED - Classify intent
            if force_agent:
                selected_agent = force_agent
                intent_result = {
                    'primary_agent': force_agent,
                    'confidence': 1.0,
                    'reasoning': 'Forced agent selection',
                    'is_multi_agent': False
                }
            else:
                context_manager = ContextManager(session)
                conversation_history = await context_manager.get_conversation_history()
                intent_result = await intent_classifier.classify_intent(
                    message, 
                    conversation_history
                )
                selected_agent = self._resolve_selected_agent(intent_result)
            
            agent_selected_event = await event_bus.publish(
                'AGENT_SELECTED',
                payload={
                    'selected_agent': selected_agent,
                    'intent_classification': intent_result
                },
                session=session,
                user=user if user.is_authenticated else None,
                parent_event=intent_event
            )
            
            # Step 3: CONTEXT_FETCHED - Build context INCLUDING user profile
            context_manager = ContextManager(session)
            full_context = await context_manager.build_full_context()
            
            # Get user-specific context for the selected agent
            user_context = await self._get_user_context(user, selected_agent)
            
            context_event = await event_bus.publish(
                'CONTEXT_FETCHED',
                payload={
                    'context_keys': list(full_context.keys()),
                    'has_user_profile': bool(user_context),
                    'conversation_length': len(full_context.get('conversation_history', []))
                },
                session=session,
                user=user if user.is_authenticated else None,
                parent_event=agent_selected_event
            )
            
            # Step 4: AGENT_RESPONSE - Route to agent WITH context
            if selected_agent not in self.agents:
                error_msg = f"Agent '{selected_agent}' not yet implemented"
                logger.warning(error_msg)
                
                await event_bus.publish(
                    'ERROR_OCCURRED',
                    payload={
                        'error': error_msg,
                        'selected_agent': selected_agent
                    },
                    session=session,
                    user=user if user.is_authenticated else None,
                    parent_event=context_event
                )
                
                return {
                    'success': False,
                    'error': error_msg,
                    'available_agents': list(self.agents.keys()),
                    'intent_classification': intent_result
                }
            
            # Execute agent WITH user context injected
            agent_runner = self.agents[selected_agent]
            agent_response = await self._call_agent_with_retries(
                agent_runner=agent_runner,
                message=message,
                session_id=session.session_id,
                user_context=user_context,
            )
            
            response_event = await event_bus.publish(
                'AGENT_RESPONSE',
                payload={
                    'agent': selected_agent,
                    'response_received': True
                },
                session=session,
                user=user if user.is_authenticated else None,
                parent_event=context_event
            )
            
            # Save agent message with agent type in metadata
            await sync_to_async(Message.objects.create)(
                session=session,
                role='agent',
                content=str(agent_response),
                metadata={'agent_type': selected_agent}
            )
            
            # Step 5: ACTIONS_APPLIED
            actions_applied = await action_applier.apply_actions(
                response_text=str(agent_response),
                session=session,
                user=user if user.is_authenticated else None,
            )
            await event_bus.publish(
                'ACTIONS_APPLIED',
                payload={
                    'actions': actions_applied
                },
                session=session,
                user=user if user.is_authenticated else None,
                parent_event=response_event
            )
            
            # Step 6: AUDIT_LOGGED
            await sync_to_async(audit_logger.log_agent_action)(
                action='Agent Message Processed',
                session=session,
                details={
                    'agent': selected_agent,
                    'message_length': len(message),
                    'intent_confidence': intent_result.get('confidence', 0),
                    'has_user_context': bool(user_context),
                    'actions_count': len(actions_applied)
                },
                user=user if user.is_authenticated else None,
                event=response_event,
                success=True
            )
            
            await event_bus.publish(
                'AUDIT_LOGGED',
                payload={
                    'audit_created': True
                },
                session=session,
                user=user if user.is_authenticated else None,
                parent_event=response_event
            )
            
            return {
                'success': True,
                'response': agent_response,
                'agent': selected_agent,
                'intent_classification': intent_result,
                'session_id': session.session_id,
                'context': full_context,
                'actions_applied': actions_applied,
            }
            
        except Exception as e:
            logger.error(f"Orchestration error: {e}", exc_info=True)
            
            if session:
                await sync_to_async(audit_logger.log_agent_action)(
                    action='Agent Message Processing Failed',
                    session=session,
                    details={
                        'error': str(e),
                        'message': message
                    },
                    user=user if user.is_authenticated else None,
                    success=False,
                    error_message=str(e)
                )
            
            return {
                'success': False,
                'error': str(e)
            }
    
    async def process_message_stream(
        self,
        message: str,
        user: User,
        session: Optional[AgentSession] = None,
        force_agent: Optional[str] = None
    ):
        """
        Stream agent responses in real-time.
        Now with user context injection.
        """
        try:
            # Create or get session
            if not session:
                session = await sync_to_async(AgentSession.objects.create)(
                    user=user if user.is_authenticated else None,
                    session_id=str(uuid.uuid4()),
                    agent_type='orchestrator'
                )
            
            # Classify intent
            if force_agent:
                selected_agent = force_agent
                intent_result = {
                    'primary_agent': force_agent,
                    'confidence': 1.0,
                    'reasoning': 'Forced agent selection',
                }
            else:
                context_manager = ContextManager(session)
                conversation_history = await context_manager.get_conversation_history()
                intent_result = await intent_classifier.classify_intent(
                    message, 
                    conversation_history
                )
                selected_agent = self._resolve_selected_agent(intent_result)
            
            # Yield agent info
            yield {
                'type': 'agent_selected',
                'agent': selected_agent,
                'session_id': session.session_id,
                'intent': intent_result
            }
            
            # Save user message
            await sync_to_async(Message.objects.create)(
                session=session,
                role='user',
                content=message
            )
            
            # Check if agent exists
            if selected_agent not in self.agents:
                yield {
                    'type': 'error',
                    'error': f"Agent '{selected_agent}' not yet implemented"
                }
                return
            
            # Get user context for personalization
            user_context = await self._get_user_context(user, selected_agent)
            
            # Stream agent response WITH user context
            agent_runner = self.agents[selected_agent]
            full_response = ""
            
            chunk_count = 0
            async for chunk in agent_runner.run_agent_stream(
                message, 
                session_id=session.session_id,
                user_context=user_context
            ):
                if chunk:
                    chunk_count += 1
                    full_response += chunk
                    yield {
                        'type': 'chunk',
                        'content': chunk
                    }
            
            logger.debug(f"Stream complete: agent={selected_agent} chunks={chunk_count} len={len(full_response)}")
            
            # Save agent message with agent type in metadata
            await sync_to_async(Message.objects.create)(
                session=session,
                role='agent',
                content=full_response,
                metadata={'agent_type': selected_agent}
            )
            
            # Log completion
            await sync_to_async(audit_logger.log_agent_action)(
                action='Agent Message Streamed',
                session=session,
                details={
                    'agent': selected_agent,
                    'message_length': len(message),
                    'has_user_context': bool(user_context),
                },
                user=user if user.is_authenticated else None,
                success=True
            )
            
        except Exception as e:
            logger.error(f"Streaming error: {e}", exc_info=True)
            yield {
                'type': 'error',
                'error': str(e)
            }
    
    async def route_message(
        self, 
        agent_type: str, 
        message: str, 
        session_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Legacy method: Route a message to a specific agent"""
        if agent_type not in self.agents:
            return {
                'error': f'Unknown agent type: {agent_type}',
                'available_agents': list(self.agents.keys())
            }
        
        agent_runner = self.agents[agent_type]
        
        try:
            response = await agent_runner.run_agent(
                message, 
                session_id=session_id,
                user_context=context
            )
            return {
                'success': True,
                'response': response,
                'agent_type': agent_type
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'agent_type': agent_type
            }
    
    def get_available_agents(self) -> List[str]:
        """Return list of available agent types"""
        return list(self.agents.keys())
    
    def get_all_agent_types(self) -> List[str]:
        """Return list of all planned agent types"""
        return [
            'study_agent',
            'productivity_agent',
            'wellness_agent',
            'meal_planner_agent',
            'habit_coach_agent',
            'planner_agent',
            'knowledge_agent',
        ]


# Singleton instance
orchestrator = EnhancedOrchestrator()
