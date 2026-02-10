## Import ADK components
import asyncio
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
from google.genai.types import Content, Part
from google.genai import types
from dotenv import load_dotenv
from django.conf import settings
import json
import os
from typing import Dict, List, Any

load_dotenv()

def setup_ai_key():
    try:
        GEMINI_API_KEY = getattr(settings, 'GEMINI_API_KEY', os.getenv("GEMINI_API_KEY"))
        if GEMINI_API_KEY is None:
            raise ValueError("GEMINI_API_KEY not set")
        
        # Ensure GOOGLE_API_KEY is set for ADK components
        os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
        return GEMINI_API_KEY
    except Exception as e:
        print(f"Error setting up AI key: {e}")

setup_ai_key()

# Configure retry options
retry_config = types.HttpRetryOptions(
    attempts=8,  # Maximum retry attempts
    exp_base=10,  # Delay multiplier
    initial_delay=3,
    max_delay=60,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

shopping_agent = Agent(
    name="ShoppingAgent",
    model=Gemini(model="gemini-2.0-flash-lite", retry_options=retry_config),
    description="A helpful assistant for shopping lists and budget tracking.",
    instruction="""You are a shopping list and budget management agent. You help users:
    1. Create and organize shopping lists by category (groceries, household items, etc.)
    2. Track shopping budgets and expenses
    3. Suggest cost-effective purchasing decisions
    4. Compare prices and find deals
    5. Manage multiple shopping lists (weekly groceries, special events, etc.)
    
    Focus on practical shopping assistance without meal planning or recipes.
    Ask about budget constraints and shopping preferences if not provided.
    Be helpful, budget-conscious, and organized.""",
    tools=[google_search],
)

class ShoppingAgentRunner:
    def __init__(self, agent: Agent):
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=agent,
            app_name="ShoppingAgentApp",
            memory_service=InMemoryMemoryService(),
            session_service=self.session_service,
        )

    async def run_agent(self, user_input: str, session_id: str = "default_user"):
        try:
            # Create session if it doesn't exist
            if not self.session_service.get_session(session_id=session_id, app_name="ShoppingAgentApp", user_id=session_id):
                self.session_service.create_session(
                    session_id=session_id,
                    user_id=session_id,
                    app_name="ShoppingAgentApp",
                )
            
            response_gen = self.runner.run(
                user_id=session_id,
                session_id = session_id,
                new_message=Content(role="user", parts=[Part(text=user_input)]),
            )

            # Response is a generator, collect all chunks
            result = ""
            for chunk in response_gen:
                if hasattr(chunk, "text"):
                    result += chunk.text
                else:
                    result += str(chunk)

            return result

        except Exception as e:
            print(f"Error running shopping agent: {e}")
            return None
    
    async def run_agent_stream(self, user_input: str, session_id: str = "default_user"):
        """Stream agent responses chunk by chunk"""
        try:
            # Create session if it doesn't exist
            if not self.session_service.get_session(session_id=session_id, app_name="ShoppingAgentApp", user_id=session_id):
                self.session_service.create_session(
                    session_id=session_id,
                    user_id=session_id,
                    app_name="ShoppingAgentApp",
                )
            
            print(f"[SHOPPING AGENT] Starting runner.run()")
            response_gen = self.runner.run(
                user_id=session_id,
                session_id=session_id,
                new_message=Content(role="user", parts=[Part(text=user_input)]),
            )

            # Yield chunks as they arrive
            chunk_count = 0
            for chunk in response_gen:
                chunk_count += 1
                print(f"[SHOPPING AGENT] Raw chunk {chunk_count}")
                # Extract text from Event.content.parts
                if hasattr(chunk, "content") and chunk.content and hasattr(chunk.content, "parts"):
                    for part in chunk.content.parts:
                        if hasattr(part, "text") and part.text:
                            print(f"[SHOPPING AGENT] Yielding text: {part.text[:50]}...")
                            yield part.text
                else:
                    print(f"[SHOPPING AGENT] Chunk has no content.parts")
            
            print(f"[SHOPPING AGENT] Generator exhausted after {chunk_count} chunks")

        except Exception as e:
            print(f"Error streaming shopping agent: {e}")
            yield None
# Create a singleton instance
shopping_agent_runner = ShoppingAgentRunner(shopping_agent)
