## Import ADK components
import asyncio
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner, InMemoryRunner
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
        return GEMINI_API_KEY
    except Exception as e:
        print(f"Error: {e}")

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
    description="A helpful assistant for meal planning, recipes, shopping lists, and budget tracking.",
    instruction="""You are a shopping and meal planning agent. You help users:
    1. Plan nutritious meals based on preferences, dietary restrictions, and goals
    2. Suggest recipes with ingredients and cooking instructions
    3. Create shopping lists organized by category
    4. Track meal budgets and suggest cost-effective options
    5. Optimize grocery purchases to reduce waste
    
    Ask about preferences if not provided. Be friendly, health-conscious, and budget-aware.""",
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
# Create a singleton instance
shopping_agent_runner = ShoppingAgentRunner(shopping_agent)
