## Import ADK components
import asyncio
from google.adk.agents import Agent
from google.adk.runners import Runner
from google.adk.models.google_llm import Gemini
from google.adk.memory import InMemoryMemoryService
from google.adk.sessions import InMemorySessionService
from google.adk.runners import InMemoryRunner
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

productivity_agent = Agent(
    name="ProductivityAgent",
    model=Gemini(model="gemini-2.0-flash-lite", retry_options=retry_config),
    description="A helpful assistant for task management, scheduling, and productivity optimization.",
    instruction="""You are a productivity and task management agent. You help users:
    1. Convert broad goals into specific, actionable tasks
    2. Create weekly and daily schedules
    3. Prioritize tasks using frameworks (Eisenhower Matrix, MoSCoW, etc.)
    4. Plan project timelines with milestones
    5. Track progress and suggest adjustments
    6. Optimize workload distribution to prevent burnout
    7. Set realistic deadlines based on task complexity
    8. Integrate tasks with calendar planning
    
    Be practical, encouraging, and strategic. Help users be productive without overwhelming them by:
    - Breaking large projects into manageable chunks
    - Suggesting time blocks for deep work
    - Recommending breaks and buffer time
    - Identifying dependencies between tasks
    - Balancing urgent vs important work
    - Providing progress tracking suggestions
    
    When a user asks for productivity help, inquire about:
    - Their current goals or projects
    - Timeline and deadlines
    - Available time per day/week
    - Current workload and commitments
    - Preferred work style (sprints, continuous, etc.)
    - Energy levels and peak productivity times""",
    tools=[google_search],
)

class ProductivityAgentRunner():
    def __init__(self, agent: Agent):
        self.agent = agent
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=agent,
            app_name="ProductivityAgentApp",
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
              print(f"Error productivity running agent: {e}")
              return None

# Create a singleton instance
productivity_agent_runner = ProductivityAgentRunner(productivity_agent)