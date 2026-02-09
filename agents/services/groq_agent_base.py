"""
Groq Agent Base - Fast LLM agent using Groq API
Provides similar interface to Google ADK but uses Groq for better rate limits
"""
import os
from typing import AsyncGenerator, Optional
from groq import Groq, AsyncGroq
from django.conf import settings
from dotenv import load_dotenv

load_dotenv()


class GroqAgentRunner:
    """
    Base runner for Groq-based agents with streaming support
    
    Benefits over Gemini:
    - 30 requests/min (vs 15 for Gemini free)
    - Very fast inference
    - Multiple model options
    """
    
    AVAILABLE_MODELS = {
        'llama-3.3-70b': 'llama-3.3-70b-versatile',  # Best overall
        'llama-3.1-70b': 'llama-3.1-70b-versatile',  # Great alternative
        'mixtral-8x7b': 'mixtral-8x7b-32768',        # Good for context
        'gemma2-9b': 'gemma2-9b-it',                 # Faster, smaller
    }
    
    def __init__(
        self, 
        agent_name: str,
        system_instruction: str,
        model: str = 'llama-3.3-70b',
        temperature: float = 0.7,
        max_tokens: int = 8000
    ):
        """
        Initialize Groq agent
        
        Args:
            agent_name: Name of the agent
            system_instruction: System prompt for the agent
            model: Model to use (key from AVAILABLE_MODELS)
            temperature: Generation temperature (0-2)
            max_tokens: Maximum response tokens
        """
        self.agent_name = agent_name
        self.system_instruction = system_instruction
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Get model name
        self.model = self.AVAILABLE_MODELS.get(model, self.AVAILABLE_MODELS['llama-3.3-70b'])
        
        # Initialize Groq clients
        api_key = self._get_api_key()
        self.client = Groq(api_key=api_key)
        self.async_client = AsyncGroq(api_key=api_key)
        
        # Simple in-memory conversation storage
        self.conversations = {}
    
    def _get_api_key(self) -> str:
        """Get Groq API key from settings or environment"""
        api_key = getattr(settings, 'GROQ_API_KEY', None) or os.getenv('GROQ_API_KEY')
        if not api_key:
            raise ValueError(
                "GROQ_API_KEY not found. Get one free at https://console.groq.com/keys"
            )
        return api_key
    
    def _get_conversation(self, session_id: str) -> list:
        """Get or create conversation history for session"""
        if session_id not in self.conversations:
            self.conversations[session_id] = [
                {"role": "system", "content": self.system_instruction}
            ]
        return self.conversations[session_id]
    
    async def run_agent(self, user_input: str, session_id: str = "default") -> str:
        """
        Run agent and return complete response
        
        Args:
            user_input: User's message
            session_id: Session ID for conversation tracking
            
        Returns:
            Complete agent response
        """
        try:
            # Get conversation history
            messages = self._get_conversation(session_id)
            
            # Add user message
            messages.append({"role": "user", "content": user_input})
            
            # Get response from Groq
            response = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            
            # Extract assistant's reply
            assistant_message = response.choices[0].message.content
            
            # Add to conversation history
            messages.append({"role": "assistant", "content": assistant_message})
            
            return assistant_message
            
        except Exception as e:
            print(f"❌ Groq API Error in {self.agent_name}: {e}")
            raise
    
    async def run_agent_stream(
        self, 
        user_input: str, 
        session_id: str = "default"
    ) -> AsyncGenerator[str, None]:
        """
        Stream agent responses in real-time
        
        Args:
            user_input: User's message
            session_id: Session ID for conversation tracking
            
        Yields:
            Response chunks as they're generated
        """
        try:
            # Get conversation history
            messages = self._get_conversation(session_id)
            
            # Add user message
            messages.append({"role": "user", "content": user_input})
            
            # Stream response from Groq
            stream = await self.async_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                stream=True,
            )
            
            # Collect full response for history
            full_response = ""
            
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    content = chunk.choices[0].delta.content
                    full_response += content
                    yield content
            
            # Add complete response to history
            messages.append({"role": "assistant", "content": full_response})
            
        except Exception as e:
            print(f"❌ Groq Streaming Error in {self.agent_name}: {e}")
            raise
    
    def clear_conversation(self, session_id: str):
        """Clear conversation history for a session"""
        if session_id in self.conversations:
            self.conversations[session_id] = [
                {"role": "system", "content": self.system_instruction}
            ]
