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
    attempts=8,
    exp_base=10,
    initial_delay=3,
    max_delay=60,
    http_status_codes=[429, 500, 503, 504],
)

wellness_agent = Agent(
    name="WellnessAgent",
    model=Gemini(model="gemini-2.0-flash-lite", retry_options=retry_config),
    description="A helpful assistant for wellness, health tracking, and habit formation.",
    instruction="""You are a wellness and health agent. You help users:
    1. Build and maintain healthy habits and routines
    2. Track wellness activities (exercise, meditation, sleep)
    3. Monitor mood and mental health
    4. Create sustainable wellness plans
    5. Suggest habit streaks and milestones
    6. Balance work and rest for optimal wellbeing
    7. Provide personalized health recommendations
    8. Track progress and celebrate achievements
    
    Be supportive, holistic, and balanced. Help users improve their wellbeing by:
    - Starting with small, achievable habits
    - Focusing on consistency over perfection
    - Celebrating progress and streaks
    - Addressing both physical and mental health
    - Integrating wellness with daily life
    - Providing science-backed suggestions
    - Adapting to individual needs and preferences
    
    When a user asks for wellness help, inquire about:
    - Current health goals or concerns
    - Existing routines and habits
    - Sleep patterns and quality
    - Activity levels and exercise preferences
    - Stress levels and mood patterns
    - Available time for wellness activities
    - Any health conditions or restrictions""",
    tools=[google_search],
)

class WellnessAgentRunner():
    def __init__(self, agent: Agent):
        self.agent = agent
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=agent,
            app_name="WellnessAgentApp",
            memory_service=InMemoryMemoryService(),
            session_service=self.session_service,
        )
    
    async def run_agent(self, user_input: str, session_id: str = "default_user"):
        try:
            # Create session if it doesn't exist
            if not self.session_service.get_session(session_id):
                self.session_service.create_session(
                    session_id=session_id,
                    user_id=session_id,
                )
            
            response_gen = self.runner.run(
                user_id=session_id,
                session_id=session_id,
                new_message=Content(role="user", parts=[Part(text=user_input)]),
            )

            # Collect response from generator
            result = ""
            for chunk in response_gen:
                if hasattr(chunk, "text"):
                    result += chunk.text
                else:
                    result += str(chunk)

            return result

        except Exception as e:
            print(f"Error running wellness agent: {e}")
            return None
    
    async def run_agent_stream(self, user_input: str, session_id: str = "default_user"):
        """Stream agent responses chunk by chunk"""
        try:
            # Create session if it doesn't exist
            if not self.session_service.get_session(session_id=session_id, app_name="WellnessAgentApp", user_id=session_id):
                self.session_service.create_session(
                    session_id=session_id,
                    app_name="WellnessAgentApp",
                    user_id=session_id,
                )
            
            response_gen = self.runner.run(
                user_id=session_id,
                session_id=session_id,
                new_message=Content(role="user", parts=[Part(text=user_input)]),
            )

            # Yield chunks as they arrive
            for chunk in response_gen:
                # Extract text from Event.content.parts
                if hasattr(chunk, "content") and chunk.content and hasattr(chunk.content, "parts"):
                    for part in chunk.content.parts:
                        if hasattr(part, "text") and part.text:
                            yield part.text

        except Exception as e:
            print(f"Error streaming wellness agent: {e}")
            yield None
# Create a singleton instance
wellness_agent_runner = WellnessAgentRunner(wellness_agent)
    

    