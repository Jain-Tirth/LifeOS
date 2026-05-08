"""
Groq Agent Base - Fast LLM agent using Groq API
Now with DB-persisted history and context injection (no more amnesia).
"""
import os
import json
import logging
from typing import AsyncGenerator, Optional, Dict, Any, List
from groq import Groq, AsyncGroq
from django.conf import settings
from dotenv import load_dotenv
from asgiref.sync import sync_to_async

load_dotenv()

logger = logging.getLogger(__name__)


class GroqAgentRunner:
    """
    Base runner for Groq-based agents with:
    - DB-persisted conversation history (survives server restarts)
    - User context injection (agents know WHO they're talking to)
    - Streaming support
    """
    
    AVAILABLE_MODELS = {
        'llama-3.3-70b': 'llama-3.3-70b-versatile',
        'llama-3.1-70b': 'llama-3.1-70b-versatile',
        'mixtral-8x7b': 'mixtral-8x7b-32768',
        'gemma2-9b': 'gemma2-9b-it',
    }
    
    # How many past messages to load from DB for context
    HISTORY_WINDOW = 20
    
    def __init__(
        self, 
        agent_name: str,
        system_instruction: str,
        model: str = 'llama-3.3-70b',
        temperature: float = 0.7,
        max_tokens: int = 8000
    ):
        self.agent_name = agent_name
        
        # Append formatting guidelines
        strict_formatting = """
        
VISUAL STYLING GUIDELINES (STRICT COMPLIANCE REQUIRED):
- Headers: Always start your response with a clear ## Header.
- Bold Emphasis: Use bolding for all key terms, deadlines, and important actions.
- Lists over Paragraphs: If you have more than two sentences, convert them into a bulleted or numbered list.
- Horizontal Rules: Use --- to separate the conversational greeting from the main data/notes.
- Callout Blocks: Wrap specific advice or "next steps" in > Blockquotes.
- Tables: If comparing two or more things, use a Markdown table.
- Task: Provide well-structured, professional, and visually scannable responses.
"""
        self.system_instruction = system_instruction + strict_formatting
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Get model name
        self.model = self.AVAILABLE_MODELS.get(model, self.AVAILABLE_MODELS['llama-3.3-70b'])
        
        # Initialize Groq clients
        api_key = self._get_api_key()
        self.client = Groq(api_key=api_key)
        self.async_client = AsyncGroq(api_key=api_key)
    
    def _get_api_key(self) -> str:
        """Get Groq API key from settings or environment"""
        api_key = getattr(settings, 'GROQ_API_KEY', None) or os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found. Get one free at https://console.groq.com/keys"
            )
        return api_key
    
    async def _load_history_from_db(self, session_id: str) -> List[Dict[str, str]]:
        """
        Load conversation history from DB instead of in-memory dict.
        This means history survives server restarts.
        """
        from agents.models import Message, AgentSession
        
        try:
            session = await sync_to_async(
                AgentSession.objects.filter(session_id=session_id).first
            )()
            
            if not session:
                return []
            
            messages = await sync_to_async(
                lambda: list(
                    session.messages.order_by('-created_at')[:self.HISTORY_WINDOW]
                )
            )()
            
            # Reverse to chronological order
            messages.reverse()
            
            history = []
            for msg in messages:
                role = 'assistant' if msg.role == 'agent' else msg.role
                if role in ('user', 'assistant'):
                    history.append({
                        'role': role,
                        'content': msg.content
                    })
            
            return history
            
        except Exception as e:
            logger.warning(f"Failed to load history from DB for {session_id}: {e}")
            return []
    
    def _build_user_context_message(self, user_context: Dict[str, Any]) -> str:
        """
        Convert user profile context into a natural-language system message
        that the agent can understand and use.
        """
        if not user_context:
            return ""
        
        parts = []
        
        name = user_context.get('name', '')
        if name and name != '':
            parts.append(f"You are talking to {name}.")
        
        tz = user_context.get('timezone', '')
        if tz:
            parts.append(f"Their timezone is {tz}.")
        
        # Dietary
        dietary = user_context.get('dietary_preferences', {})
        if dietary:
            diet_type = dietary.get('type', '')
            if diet_type:
                parts.append(f"Dietary preference: {diet_type}.")
            allergies = dietary.get('allergies', [])
            if allergies:
                parts.append(f"Allergies: {', '.join(allergies)}.")
            cuisines = dietary.get('cuisine', [])
            if cuisines:
                parts.append(f"Preferred cuisines: {', '.join(cuisines)}.")
        
        # Work
        work = user_context.get('work_hours', {})
        if work:
            start = work.get('start', '')
            end = work.get('end', '')
            if start and end:
                parts.append(f"Work hours: {start} to {end}.")
        
        # Fitness
        fitness = user_context.get('fitness_level', '')
        if fitness:
            parts.append(f"Fitness level: {fitness}.")
        
        conditions = user_context.get('health_conditions', [])
        if conditions:
            parts.append(f"Health conditions to be aware of: {', '.join(conditions)}.")
        
        # Learning
        learning = user_context.get('learning_style', '')
        if learning:
            parts.append(f"Learning style: {learning}.")
        
        # Goals
        goals = user_context.get('goals', [])
        if goals:
            goal_strs = []
            for g in goals[:5]:  # Cap at 5
                if isinstance(g, dict):
                    goal_strs.append(f"- {g.get('goal', str(g))}")
                else:
                    goal_strs.append(f"- {g}")
            parts.append(f"Current goals:\n" + "\n".join(goal_strs))
        
        # About me
        about = user_context.get('about_me', '')
        if about:
            parts.append(f"Additional info: {about}")
        
        return "\n".join(parts)
    
    async def _build_messages(
        self, 
        user_input: str, 
        session_id: str,
        user_context: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, str]]:
        """
        Build the full message array for the Groq API call:
        [system_prompt, user_context, ...history, current_message]
        """
        messages = [
            {"role": "system", "content": self.system_instruction}
        ]
        
        # Inject user context as a second system message
        if user_context:
            context_text = self._build_user_context_message(user_context)
            if context_text:
                messages.append({
                    "role": "system",
                    "content": f"USER PROFILE (use this to personalize your responses):\n{context_text}"
                })
        
        # Load conversation history from DB
        history = await self._load_history_from_db(session_id)
        messages.extend(history)
        
        # Add current user message
        messages.append({"role": "user", "content": user_input})
        
        return messages
    
    async def run_agent(
        self, 
        user_input: str, 
        session_id: str = "default",
        user_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Run agent and return complete response.
        
        Args:
            user_input: User's message
            session_id: Session ID for conversation tracking
            user_context: User profile context from UserProfile.get_agent_context()
            
        Returns:
            Complete agent response
        """
        try:
            messages = await self._build_messages(user_input, session_id, user_context)
            
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                frequency_penalty=0.2,
                presence_penalty=0.2,
            )
            
            assistant_message = response.choices[0].message.content
            return assistant_message
            
        except Exception as e:
            logger.error(f"Groq API Error in {self.agent_name}: {e}")
            raise
    
    async def run_agent_stream(
        self, 
        user_input: str, 
        session_id: str = "default",
        user_context: Optional[Dict[str, Any]] = None
    ) -> AsyncGenerator[str, None]:
        """
        Stream agent responses in real-time.
        
        Args:
            user_input: User's message
            session_id: Session ID for conversation tracking
            user_context: User profile context from UserProfile.get_agent_context()
            
        Yields:
            Response chunks as they're generated
        """
        try:
            messages = await self._build_messages(user_input, session_id, user_context)
            
            stream = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                frequency_penalty=0.2,
                presence_penalty=0.2,
                stream=True,
            )
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    yield content
            
        except Exception as e:
            logger.error(f"Groq Streaming Error in {self.agent_name}: {e}")
            raise
    
    def clear_conversation(self, session_id: str):
        """Clear conversation history for a session (deletes from DB)"""
        from agents.models import Message, AgentSession
        try:
            session = AgentSession.objects.filter(session_id=session_id).first()
            if session:
                session.messages.all().delete()
        except Exception as e:
            logger.warning(f"Failed to clear conversation {session_id}: {e}")
