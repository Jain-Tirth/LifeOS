## Import ADK components
import asyncio
from google.adk.agents import Agent
from google.adk.models.google_llm import Gemini
from google.adk.runners import Runner, InMemoryRunner
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.adk.tools import google_search
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

# Memory & Session Services
memory_service = InMemoryMemoryService()
session_service = InMemorySessionService()

# Configure retry options
retry_config = types.HttpRetryOptions(
    attempts=8,  # Maximum retry attempts
    exp_base=10,  # Delay multiplier
    initial_delay=3,
    max_delay=60,
    http_status_codes=[429, 500, 503, 504],  # Retry on these HTTP errors
)

meal_planner_agent = Agent(
    name="MealPlanner",
    model=Gemini(model="gemini-2.0-flash-lite", retry_options=retry_config),
    description="A helpful assistant for planning and tracking meal activities.",
    memory_service=memory_service,
    session_service=session_service,
    instruction="""You are meal agent. You have to provide the best food to user based on the preference of user if provided or else ask them there preference. """,
    tools=[google_search],
)

class MealAgentRunner():
    def __init__(self, agent: Agent):
        self.agent = agent
        self.runner = InMemoryRunner(agent=agent, app_name="MealPlannerApp")
    
    async def run_agent(self, user_input: str, session_id: str = None):
        """Run the meal planner agent with user input"""
        try:
            response = await self.runner.run(user_input, session_id=session_id)
            return response
        except Exception as e:
            print(f"Error running agent: {e}")
            return None

# Create a singleton instance
meal_agent_runner = MealAgentRunner(meal_planner_agent)
