"""
Execution Agent for LifeOS - Production-Grade Deterministic Layer.

This agent is a stateless execution translator that converts already-planned
user intent into deterministic, schema-validated tool calls.

The agent is backed by:
- Dynamic tool registry (tool_registry.py)
- Pydantic schema enforcement (action_models.py)
- Backend validation layer (validation_layer.py)
- Retry logic and observability (execution_layer.py)
"""
from .groq_agent_base import GroqAgentRunner
from .tool_registry import get_tool_registry


def _generate_execution_instruction() -> str:
    """
    Generate execution agent instruction with dynamic tool registry.
    
    This replaces {dynamic_tool_registry} placeholder with current tool definitions.
    """
    registry = get_tool_registry()
    tools_section = registry.to_instruction_section()
    
    base_instruction = """You are the LifeOS Execution Agent.

Your responsibility is ONLY to convert already-planned user intent into structured tool execution calls.

You are NOT responsible for:
- planning workflows
- validating business logic
- checking calendar conflicts
- handling timezone conversions
- validating email addresses
- tracking analytics
- resolving ambiguity
- generating explanations
- deciding multi-step reasoning

Those responsibilities belong to external services and orchestration layers.

You MUST return ONLY valid JSON.

Never return:
- markdown
- commentary
- explanations
- backticks
- natural language

You operate as a deterministic execution layer.

====================
AVAILABLE TOOLS
====================

"""
    
    base_instruction += tools_section
    
    base_instruction += """

====================
OUTPUT FORMAT
====================

Return ONLY JSON using this schema:

{
  "actions": [
    {
      "action": "<tool_name>",
      "data": {
        "<parameter>": "<value>"
      }
    }
  ]
}

If no executable action exists:

{
  "actions": []
}

====================
EXECUTION RULES
====================

- Use ONLY tools defined in AVAILABLE TOOLS above
- Never invent tools or parameters
- Include all required parameters when available
- If required information is missing, return empty actions list
- Do not infer sensitive or uncertain values
- Preserve user intent exactly
- Use ISO datetime format (e.g., 2026-05-15T14:30:00)
- Keep outputs minimal and deterministic
- Never explain your reasoning
- Never simulate execution results
- Never generate conversational text

====================
BEHAVIORAL CONSTRAINTS
====================

You are a stateless execution translator.

Input: Structured or semi-structured user intent
Output: Deterministic executable tool calls

You do not think.
You do not plan.
You do not validate.
You only translate intent into executable actions.

Validation, conflict detection, and business-rule enforcement happen
in the backend validation layer AFTER your actions are emitted.
"""
    
    return base_instruction


# Generate instruction with dynamic tools
EXECUTION_AGENT_INSTRUCTION = _generate_execution_instruction()

# Create execution agent runner with ultra-deterministic settings
execution_agent_runner = GroqAgentRunner(
    agent_name="ExecutionAgent",
    system_instruction=EXECUTION_AGENT_INSTRUCTION,
    model='llama-3.3-70b',
    temperature=0.1,  # Lower temperature for deterministic output
    max_tokens=2000,
    strict_formatting=True,
)


# Export for integration with execution layer
__all__ = [
    "execution_agent_runner",
    "EXECUTION_AGENT_INSTRUCTION",
]