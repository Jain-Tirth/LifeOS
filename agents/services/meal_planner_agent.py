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

meal_planner_agent = Agent(
    name="MealPlannerAgent",
    model=Gemini(model="gemini-2.0-flash-lite", retry_options=retry_config),
    description="A helpful assistant for meal planning, recipes, and nutritional guidance.",
    instruction="""You are a meal planning and nutrition agent. You help users:
    1. Create personalized meal plans (daily, weekly, or monthly)
    2. Suggest recipes based on preferences, dietary restrictions, and goals
    3. Provide nutritional information and balanced diet guidance
    4. Accommodate dietary restrictions (vegetarian, vegan, gluten-free, keto, etc.)
    5. Suggest meal prep strategies and cooking tips
    6. Plan meals for special occasions or events
    7. Optimize meals for specific goals (weight loss, muscle gain, energy, etc.)
    
    When planning meals, always inquire about:
    - Dietary preferences and restrictions
    - Number of people
    - Budget constraints (if relevant)
    - Cooking skill level
    - Time available for meal prep
    - Health or fitness goals
    
    Provide detailed recipes with:
    - Ingredient lists with quantities
    - Step-by-step cooking instructions
    - Prep and cook time
    - Nutritional information (calories, protein, carbs, fats)
    - Serving size
    
    Be creative, health-conscious, and culturally diverse in your suggestions.
    Use google_search when needed to find trending recipes or specific dietary information.""",
    tools=[google_search],
)

class MealPlannerAgentRunner:
    def __init__(self, agent: Agent):
        self.agent = agent
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=agent,
            app_name="MealPlannerAgentApp",
            memory_service=InMemoryMemoryService(),
            session_service=self.session_service,
        )

    async def run_agent(self, user_input: str, session_id: str = "default_user"):
        try:
            # Create session if it doesn't exist
            if not self.session_service.get_session(session_id=session_id, app_name="MealPlannerAgentApp", user_id=session_id):
                self.session_service.create_session(
                    session_id=session_id,
                    user_id=session_id,
                    app_name="MealPlannerAgentApp",
                )
            
            response_gen = self.runner.run(
                user_id=session_id,
                session_id=session_id,
                new_message=Content(role="user", parts=[Part(text=user_input)]),
            )

            # Collect response from generator
            result = ""
            for chunk in response_gen:
                if hasattr(chunk, "content") and chunk.content and hasattr(chunk.content, "parts"):
                    for part in chunk.content.parts:
                        if hasattr(part, "text"):
                            result += part.text

            return result

        except Exception as e:
            print(f"Error running meal planner agent: {e}")
            return None
    
    async def run_agent_stream(self, user_input: str, session_id: str = "default_user"):
        """Stream agent responses chunk by chunk"""
        try:
            print(f"[MEAL PLANNER] run_agent_stream called with: {user_input[:50]}")
            # Create session if it doesn't exist
            if not self.session_service.get_session(session_id=session_id, app_name="MealPlannerAgentApp", user_id=session_id):
                print(f"[MEAL PLANNER] Creating session: {session_id}")
                self.session_service.create_session(
                    session_id=session_id,
                    user_id=session_id,
                    app_name="MealPlannerAgentApp",
                )
            
            print(f"[MEAL PLANNER] Starting runner.run()")
            response_gen = self.runner.run(
                user_id=session_id,
                session_id=session_id,
                new_message=Content(role="user", parts=[Part(text=user_input)]),
            )

            # Yield chunks as they arrive
            chunk_count = 0
            print(f"[MEAL PLANNER] Starting to iterate over response_gen")
            for chunk in response_gen:
                chunk_count += 1
                print(f"[MEAL PLANNER] Raw chunk {chunk_count}: {type(chunk)}")
                # Extract text from Event.content.parts
                if hasattr(chunk, "content") and chunk.content and hasattr(chunk.content, "parts"):
                    for part in chunk.content.parts:
                        if hasattr(part, "text") and part.text:
                            print(f"[MEAL PLANNER] Text length: {len(part.text)}")
                            # Split text into smaller chunks for streaming effect
                            text = part.text
                            chunk_size = 50  # Characters per chunk
                            for i in range(0, len(text), chunk_size):
                                chunk_text = text[i:i+chunk_size]
                                print(f"[MEAL PLANNER] Yielding chunk: {chunk_text[:30]}...")
                                yield chunk_text
                else:
                    print(f"[MEAL PLANNER] Chunk has no content.parts")
            
            print(f"[MEAL PLANNER] Generator exhausted after {chunk_count} chunks")

        except Exception as e:
            print(f"[MEAL PLANNER] Error streaming: {e}")
            import traceback
            traceback.print_exc()
            yield None

# Create a singleton instance
meal_planner_agent_runner = MealPlannerAgentRunner(meal_planner_agent)
