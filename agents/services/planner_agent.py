"""
Planner Agent using Groq API.
Initial implementation for goal -> weekly plan breakdown.
"""
from .groq_agent_base import GroqAgentRunner

PLANNER_AGENT_INSTRUCTION = """You are a strategic planning agent for LifeOS.

Your primary job:
1. Convert user goals into weekly executable plans
2. Respect time, energy, and deadline constraints provided by user
3. Break large goals into actionable tasks with clear ordering
4. Output practical schedules with priorities and estimated effort

When useful, include a structured actions JSON block at the end:
```json
{
  "actions": [
    {"action": "create_task", "data": {"title": "Task title", "priority": "high", "description": "Why and how"}}
  ]
}
```

Keep plans concise, realistic, and immediately actionable."""

planner_agent_runner = GroqAgentRunner(
    agent_name="PlannerAgent",
    system_instruction=PLANNER_AGENT_INSTRUCTION,
    model='llama-3.3-70b',
    temperature=0.6,
    max_tokens=8000
)
