"""
Enhanced agent orchestrator for coordinating multiple AI agents in the LifeOS system.
"""
from typing import Dict, Any, Optional, List
from agents.models import AgentSession, Message, User

# Import Groq-based agents (faster, better rate limits)
from .shopping_agent import shopping_agent_runner
from .study_agent import study_agent_runner
from .productivity_agent import productivity_agent_runner
from .wellness_agent import wellness_agent_runner
from .meal_planner_agent import meal_planner_agent_runner

from .event_bus import event_bus, audit_logger
from .intent_classifier import intent_classifier
from .context_manager import ContextManager
from asgiref.sync import sync_to_async
import logging
import uuid

logger = logging.getLogger(__name__)


class EnhancedOrchestrator:
    """
    Enhanced orchestrator with intent classification, context management,
    and multi-agent coordination.
    """
    
    def __init__(self):
        self.agents = {
            'shopping_agent': shopping_agent_runner,
            'study_agent': study_agent_runner,
            'productivity_agent': productivity_agent_runner,
            'wellness_agent': wellness_agent_runner,
            'meal_planner_agent': meal_planner_agent_runner,
        }
    
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
        
        Args:
            message: User's message
            user: User making the request
            session: Existing session or None to create new one
            force_agent: Force routing to specific agent (bypass intent classification)
            
        Returns:
            Complete response with agent output and metadata
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
                selected_agent = intent_result['primary_agent']
            
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
            
            # Step 3: CONTEXT_FETCHED - Build context
            context_manager = ContextManager(session)
            full_context = await context_manager.build_full_context()
            
            context_event = await event_bus.publish(
                'CONTEXT_FETCHED',
                payload={
                    'context_keys': list(full_context.keys()),
                    'conversation_length': len(full_context.get('conversation_history', []))
                },
                session=session,
                user=user if user.is_authenticated else None,
                parent_event=agent_selected_event
            )
            
            # Step 4: AGENT_RESPONSE - Route to agent
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
            
            # Execute agent
            agent_runner = self.agents[selected_agent]
            agent_response = await agent_runner.run_agent(
                message, 
                session_id=session.session_id
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
            
            # Step 5: ACTIONS_APPLIED (placeholder for future actions)
            await event_bus.publish(
                'ACTIONS_APPLIED',
                payload={
                    'actions': []  # Future: task creation, reminders, etc.
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
                    'intent_confidence': intent_result.get('confidence', 0)
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
                'context': full_context
            }
            
        except Exception as e:
            logger.error(f"Orchestration error: {e}", exc_info=True)
            
            # Log error
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
        Yields chunks of data for SSE streaming.
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
                selected_agent = intent_result['primary_agent']
            
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
            
            # Stream agent response
            agent_runner = self.agents[selected_agent]
            full_response = ""
            
            print(f"[ORCHESTRATOR] Starting stream from {selected_agent}")
            
            chunk_count = 0
            async for chunk in agent_runner.run_agent_stream(
                message, 
                session_id=session.session_id
            ):
                if chunk:
                    chunk_count += 1
                    print(f"[ORCHESTRATOR] Chunk {chunk_count}: {chunk[:50]}...")
                    full_response += chunk
                    yield {
                        'type': 'chunk',
                        'content': chunk
                    }
            
            print(f"[ORCHESTRATOR] Stream complete. {chunk_count} chunks, total length: {len(full_response)}")
            
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
        """
        Legacy method: Route a message to a specific agent (bypasses intent classification)
        
        Args:
            agent_type: Type of agent to route to
            message: User message to send to the agent
            session_id: Optional session ID for maintaining conversation context
            context: Additional context to pass to the agent
            
        Returns:
            Response from the agent
        """
        if agent_type not in self.agents:
            return {
                'error': f'Unknown agent type: {agent_type}',
                'available_agents': list(self.agents.keys())
            }
        
        agent_runner = self.agents[agent_type]
        
        try:
            response = await agent_runner.run_agent(message, session_id=session_id)
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
        """Return list of all planned agent types (implemented + planned)"""
        return ['study_agent', 'productivity_agent', 'wellness_agent', 'shopping_agent']


# Singleton instance
orchestrator = EnhancedOrchestrator()
