"""
Study Agent - Supports learning and knowledge management
"""
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
        
        # Ensure GOOGLE_API_KEY is set for ADK components
        os.environ["GOOGLE_API_KEY"] = GEMINI_API_KEY
        return GEMINI_API_KEY
    except Exception as e:
        print(f"Error setting up AI key: {e}")

setup_ai_key()

# Configure retry options
retry_config = types.HttpRetryOptions(
    attempts=8,
    exp_base=10,
    initial_delay=3,
    max_delay=60,
    http_status_codes=[429, 500, 503, 504],
)

study_agent = Agent(
    name="StudyAgent",
    model=Gemini(model="gemini-2.0-flash-lite", retry_options=retry_config),
    description="A helpful assistant for learning, study planning, and knowledge management.",
    instruction="""You are a study and learning agent. You help users:
    1. Organize study goals into manageable milestones
    2. Break down complex topics into key concepts
    3. Create study schedules and revision plans
    4. Summarize notes and highlight important points
    5. Suggest effective learning strategies
    6. Prepare for exams with topic breakdowns
    7. Track learning progress
    
    Be encouraging, pedagogical, and structured. Help users learn effectively by:
    - Breaking complex topics into digestible chunks
    - Creating actionable study plans
    - Providing clear explanations
    - Suggesting resources when helpful
    - Adapting to different learning styles
    
    When a user asks for help with studying, ask about:
    - What subject/topic they're studying
    - Their timeline (exam dates, deadlines)
    - Current knowledge level
    - Preferred learning style
    - Specific challenges they're facing""",
    tools=[google_search],
)

class StudyAgentRunner():
    def __init__(self, agent: Agent):
        self.agent = agent
        self.session_service = InMemorySessionService()
        self.runner = Runner(
            agent=agent,
            app_name="StudyAgentApp",
            memory_service=InMemoryMemoryService(),
            session_service=self.session_service,
        )
    
    async def run_agent(self, user_input: str, session_id: str = "default_user"):
        try:
            # Create session if it doesn't exist
            if not self.session_service.get_session(session_id=session_id, app_name="StudyAgentApp", user_id=session_id):
                self.session_service.create_session(
                    session_id=session_id,
                    app_name="StudyAgentApp",
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
            print(f"Error running study agent: {e}")
            return None
    
    async def run_agent_stream(self, user_input: str, session_id: str = "default_user"):
        """Stream agent responses chunk by chunk"""
        try:
            print(f"[STUDY AGENT] run_agent_stream called with: {user_input[:50]}")
            # Create session if it doesn't exist
            if not self.session_service.get_session(session_id=session_id, app_name="StudyAgentApp", user_id=session_id):
                print(f"[STUDY AGENT] Creating session: {session_id}")
                self.session_service.create_session(
                    session_id=session_id,
                    app_name="StudyAgentApp",
                    user_id=session_id,
                )
            
            print(f"[STUDY AGENT] Starting runner.run()")
            response_gen = self.runner.run(
                user_id=session_id,
                session_id=session_id,
                new_message=Content(role="user", parts=[Part(text=user_input)]),
            )

            # Yield chunks as they arrive
            chunk_count = 0
            print(f"[STUDY AGENT] Starting to iterate over response_gen")
            for chunk in response_gen:
                chunk_count += 1
                print(f"[STUDY AGENT] Raw chunk {chunk_count}: {type(chunk)}")
                # Extract text from Event.content.parts
                if hasattr(chunk, "content") and chunk.content and hasattr(chunk.content, "parts"):
                    for part in chunk.content.parts:
                        if hasattr(part, "text") and part.text:
                            print(f"[STUDY AGENT] Text length: {len(part.text)}")
                            # Split text into smaller chunks for streaming effect
                            text = part.text
                            chunk_size = 50  # Characters per chunk
                            for i in range(0, len(text), chunk_size):
                                chunk_text = text[i:i+chunk_size]
                                print(f"[STUDY AGENT] Yielding chunk: {chunk_text[:30]}...")
                                yield chunk_text
                else:
                    print(f"[STUDY AGENT] Chunk has no content.parts")
            
            print(f"[STUDY AGENT] Generator exhausted after {chunk_count} chunks")

        except Exception as e:
            print(f"[STUDY AGENT] Error streaming: {e}")
            import traceback
            traceback.print_exc()
            yield None
            print(f"Error streaming study agent: {e}")
            yield None

# Create a singleton instance
study_agent_runner = StudyAgentRunner(study_agent)
