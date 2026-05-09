"""
Groq Agent Base - Fast LLM agent using Groq API
Now with DB-persisted history, context injection, and TOOL CALLING (actionable agent).
"""
import os
import json
import logging
from typing import AsyncGenerator, Optional, Dict, Any, List
from django.conf import settings
from dotenv import load_dotenv
from asgiref.sync import sync_to_async
from .groq_client import GroqClientFactory
from .tool_executor import tool_executor

load_dotenv()

logger = logging.getLogger(__name__)


class GroqAgentRunner:
    """
    Base runner for Groq-based agents with:
    - DB-persisted conversation history (survives server restarts)
    - User context injection (agents know WHO they're talking to)
    - Native function calling (agents can EXECUTE actions, not just chat)
    - Streaming support
    - Execution trace for transparency UI
    """
    
    AVAILABLE_MODELS = {
        'llama-3.3-70b': 'llama-3.3-70b-versatile',
        'llama-3.1-70b': 'llama-3.1-70b-versatile',
        'mixtral-8x7b': 'mixtral-8x7b-32768',
        'gemma2-9b': 'gemma2-9b-it',
    }
    
    def __init__(
        self, 
        agent_name: str,
        system_instruction: str,
        model: str = 'llama-3.3-70b',
        temperature: float = 0.7,
        max_tokens: int = 8000,
        enable_tools: bool = True
    ):
        self.agent_name = agent_name
        self.enable_tools = enable_tools
        
        # Append formatting guidelines AND tool usage instructions
        strict_formatting = """
        
VISUAL STYLING GUIDELINES (STRICT COMPLIANCE REQUIRED):
- Headers: Always start your response with a clear ## Header.
- Bold Emphasis: Use bolding for all key terms, deadlines, and important actions.
- Lists over Paragraphs: If you have more than two sentences, convert them into a bulleted or numbered list.
- Horizontal Rules: Use --- to separate the conversational greeting from the main data/notes.
- Callout Blocks: Wrap specific advice or "next steps" in > Blockquotes.
- Tables: If comparing two or more things, use a Markdown table.
- Task: Provide well-structured, professional, and visually scannable responses.

TOOL USAGE RULES (CRITICAL):
- When the user asks you to DO something (create task, check balance, schedule event), YOU MUST call the appropriate tool.
- Do NOT just say "I'll create a task" - actually CALL the create_task tool with proper arguments.
- After calling a tool, wait for the result, then inform the user of the outcome.
- If multiple actions are needed, call tools one at a time in sequence.
- Available tools: """ + (", ".join(tool_executor.tools.keys()) if enable_tools else "None") + """
"""
        self.system_instruction = system_instruction + strict_formatting
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Get model name
        self.model = self.AVAILABLE_MODELS.get(model, self.AVAILABLE_MODELS['llama-3.3-70b'])
        
        # Initialize Groq clients
        self.client = GroqClientFactory.get_client()
        self.async_client = GroqClientFactory.get_async_client()
        
        # Get tool definitions for function calling
        self.tools = tool_executor.get_tool_definitions() if enable_tools else []
    
    async def _load_history_from_db(self, session_id: str) -> List[Dict[str, str]]:
        """
        Load conversation history from DB with smart truncation to fit
        within token context limits, keeping system message and most recent.
        """
        from agents.models import Message, AgentSession
        import tiktoken
        
        try:
            session = await sync_to_async(
                AgentSession.objects.filter(session_id=session_id).first
            )()
            
            if not session:
                return []
            
            # Load ALL messages (no arbitrary window limit)
            all_messages = await sync_to_async(
                lambda: list(session.messages.order_by('created_at'))
            )()
            
            # Convert to OpenAI format
            history = []
            for msg in all_messages:
                role = 'assistant' if msg.role == 'agent' else msg.role
                if role in ('user', 'assistant'):
                    history.append({
                        'role': role,
                        'content': msg.content
                    })

            if not history:
                return []

            # Count tokens and truncate if necessary
            # We use cl100k_base which is a good proxy for most models
            try:
                enc = tiktoken.get_encoding("cl100k_base")
            except Exception:
                # Fallback to cl100k_base if model not found
                enc = tiktoken.get_encoding("cl100k_base")

            MAX_TOKENS = 7000  # Leave 1k for response

            total_tokens = sum(len(enc.encode(h['content'])) for h in history)

            if total_tokens > MAX_TOKENS:
                # Keep last N messages
                keep_recent = []
                token_count = 0
                for msg in reversed(history):
                    msg_tokens = len(enc.encode(msg['content']))
                    if token_count + msg_tokens > MAX_TOKENS - 500:
                        break
                    keep_recent.insert(0, msg)
                    token_count += msg_tokens

                history = keep_recent
            
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
        Run agent with tool calling support and return complete response.
        
        Args:
            user_input: User's message
            session_id: Session ID for conversation tracking
            user_context: User profile context from UserProfile.get_agent_context()
            
        Returns:
            Complete agent response (may include executed tool results)
        """
        try:
            messages = await self._build_messages(user_input, session_id, user_context)
            
            # Build API call with tools if enabled
            api_kwargs = {
                "model": self.model,
                "messages": messages,
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "frequency_penalty": 0.2,
                "presence_penalty": 0.2,
            }
            
            # Add tools for function calling if enabled
            if self.tools:
                api_kwargs["tools"] = self.tools
            
            response = await self.async_client.chat.completions.create(**api_kwargs)
            
            assistant_message = response.choices[0].message.content
            
            # Check if LLM requested tool calls
            if response.choices[0].message.tool_calls:
                logger.info(f"Tool calls detected: {len(response.choices[0].message.tool_calls)}")
                
                # Execute each tool call
                for tool_call in response.choices[0].message.tool_calls:
                    tool_name = tool_call.function.name
                    tool_args = json.loads(tool_call.function.arguments)
                    
                    # Execute the tool
                    result = await tool_executor.execute_tool(tool_name, tool_args)
                    
                    # Add tool result to messages for next iteration
                    messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": tool_call.id,
                            "type": "function",
                            "function": {
                                "name": tool_name,
                                "arguments": tool_call.function.arguments
                            }
                        }]
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result)
                    })
                
                # Make second API call with tool results
                final_response = await self.async_client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                assistant_message = final_response.choices[0].message.content or assistant_message
            
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
