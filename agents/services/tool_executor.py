"""
Tool Executor - Forces LLM to use structured function calling.
This bridges the gap between "chat" and "actionable agent".

Key Features:
- Tool definitions with strict Pydantic schemas
- Forced tool selection when user requests actions
- Mock provider for reliable demos (swap with real APIs later)
- Execution trace for transparency UI
"""
from typing import Dict, Any, List, Optional, Callable, Type
from pydantic import BaseModel, Field
import json
import logging
from datetime import datetime, timedelta
import random

logger = logging.getLogger(__name__)


# =============================================================================
# TOOL DEFINITIONS WITH PYDANTIC SCHEMAS
# =============================================================================

class CreateTaskParams(BaseModel):
    title: str = Field(..., description="Clear, actionable task title")
    description: str = Field(default="", description="Optional details")
    priority: str = Field(default="medium", enum=["low", "medium", "high", "urgent"])
    due_date: Optional[str] = Field(None, description="YYYY-MM-DD format")


class CreateMealPlanParams(BaseModel):
    meal_name: str = Field(..., description="Name of the meal")
    date: str = Field(..., description="YYYY-MM-DD format")
    meal_type: str = Field(default="dinner", enum=["breakfast", "lunch", "dinner", "snack"])
    ingredients: Optional[List[str]] = Field(None, description="List of ingredients")
    instructions: Optional[str] = Field(None, description="Cooking instructions")


class CreateStudySessionParams(BaseModel):
    subject: str = Field(..., description="Subject to study")
    topic: Optional[str] = Field(None, description="Specific topic")
    duration: int = Field(..., description="Duration in minutes")
    notes: Optional[str] = Field(None, description="Study notes")


class CreateWellnessActivityParams(BaseModel):
    activity_type: str = Field(..., enum=["exercise", "meditation", "sleep", "hydration", "mood"])
    duration: Optional[int] = Field(None, description="Duration in minutes")
    intensity: Optional[str] = Field(None, description="Low/Medium/High")
    notes: Optional[str] = Field(None, description="Activity notes")


class CheckBankBalanceParams(BaseModel):
    account_type: str = Field(default="checking", enum=["checking", "savings", "credit"])


class GetCalendarEventsParams(BaseModel):
    start_date: str = Field(..., description="YYYY-MM-DD format")
    end_date: Optional[str] = Field(None, description="YYYY-MM-DD format")


class CreateCalendarEventParams(BaseModel):
    title: str = Field(..., description="Event title")
    start_time: str = Field(..., description="ISO datetime")
    end_time: str = Field(..., description="ISO datetime")
    description: Optional[str] = Field(None, description="Event details")
    location: Optional[str] = Field(None, description="Event location")


# =============================================================================
# MOCK DATA PROVIDER (FOR DEMOS - SWAP WITH REAL APIS LATER)
# =============================================================================

class MockDataProvider:
    """
    Provides deterministic mock data for demos.
    Swap with real API adapters (Google, Outlook, Plaid, etc.) in production.
    """
    
    @staticmethod
    def get_bank_balance(account_type: str = "checking") -> Dict[str, Any]:
        """Mock bank balance - replace with Plaid/Stripe API"""
        balances = {
            "checking": {"balance": 4250.75, "currency": "USD"},
            "savings": {"balance": 12500.00, "currency": "USD"},
            "credit": {"balance": -850.30, "currency": "USD", "limit": 5000},
        }
        return balances.get(account_type, {"balance": 0})
    
    @staticmethod
    def get_calendar_events(start_date: str, end_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """Mock calendar events - replace with Google Calendar API"""
        return [
            {
                "title": "Team Standup",
                "start": "2025-01-15T09:00:00",
                "end": "2025-01-15T09:30:00",
                "location": "Zoom"
            },
            {
                "title": "Doctor Appointment",
                "start": "2025-01-16T14:00:00",
                "end": "2025-01-16T15:00:00",
                "location": "Medical Center"
            },
            {
                "title": "Gym Session",
                "start": "2025-01-15T18:00:00",
                "end": "2025-01-15T19:00:00",
                "location": "Fitness First"
            }
        ]
    
    @staticmethod
    def get_health_metrics() -> Dict[str, Any]:
        """Mock health data - replace with Apple Health/Fitbit API"""
        return {
            "sleep_hours": 6.5,
            "steps": 8420,
            "heart_rate": 72,
            "water_intake_ml": 1200,
            "last_workout": "2025-01-14T18:00:00"
        }
    
    @staticmethod
    def get_recent_transactions(limit: int = 5) -> List[Dict[str, Any]]:
        """Mock transactions - replace with banking API"""
        return [
            {"merchant": "Whole Foods", "amount": -85.30, "date": "2025-01-14", "category": "groceries"},
            {"merchant": "Shell Gas Station", "amount": -45.00, "date": "2025-01-13", "category": "transport"},
            {"merchant": "Netflix", "amount": -15.99, "date": "2025-01-12", "category": "entertainment"},
            {"merchant": "Salary Deposit", "amount": 3500.00, "date": "2025-01-10", "category": "income"},
            {"merchant": "Amazon", "amount": -127.50, "date": "2025-01-09", "category": "shopping"},
        ]


# =============================================================================
# TOOL REGISTRY
# =============================================================================

class ToolDefinition:
    def __init__(
        self,
        name: str,
        description: str,
        params_model: Type[BaseModel],
        handler: Callable,
        requires_auth: bool = True
    ):
        self.name = name
        self.description = description
        self.params_model = params_model
        self.handler = handler
        self.requires_auth = True
    
    def to_openai_format(self) -> Dict[str, Any]:
        """Convert to OpenAI/Groq function calling format"""
        schema = self.params_model.model_json_schema()
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": schema
            }
        }


# Register all available tools
TOOL_REGISTRY: Dict[str, ToolDefinition] = {}

def register_tool(name: str, description: str, params_model: Type[BaseModel]):
    """Decorator to register a tool"""
    def decorator(func: Callable):
        tool = ToolDefinition(
            name=name,
            description=description,
            params_model=params_model,
            handler=func
        )
        TOOL_REGISTRY[name] = tool
        return func
    return decorator


# Register tools with mock handlers
@register_tool(
    "create_task",
    "Create a new task in the user's todo list. Use when user wants to add, schedule, or remember a task.",
    CreateTaskParams
)
def handle_create_task(params: CreateTaskParams) -> Dict[str, Any]:
    """Handler returns data for save_task()"""
    return {
        "action": "create_task",
        "data": {
            "title": params.title,
            "description": params.description,
            "priority": params.priority,
            "due_date": params.due_date,
            "status": "todo"
        }
    }


@register_tool(
    "create_meal_plan",
    "Create a meal plan or recipe suggestion. Use when user asks about food, meals, or diet.",
    CreateMealPlanParams
)
def handle_create_meal_plan(params: CreateMealPlanParams) -> Dict[str, Any]:
    return {
        "action": "create_meal_plan",
        "data": {
            "meal_name": params.meal_name,
            "date": params.date,
            "meal_type": params.meal_type,
            "ingredients": params.ingredients or [],
            "instructions": params.instructions or ""
        }
    }


@register_tool(
    "create_study_session",
    "Schedule a study session. Use when user wants to plan learning or study time.",
    CreateStudySessionParams
)
def handle_create_study_session(params: CreateStudySessionParams) -> Dict[str, Any]:
    return {
        "action": "create_study_session",
        "data": {
            "subject": params.subject,
            "topic": params.topic or "",
            "duration": params.duration,
            "notes": params.notes or ""
        }
    }


@register_tool(
    "create_wellness_activity",
    "Log or schedule a wellness activity (exercise, meditation, sleep tracking).",
    CreateWellnessActivityParams
)
def handle_create_wellness_activity(params: CreateWellnessActivityParams) -> Dict[str, Any]:
    return {
        "action": "create_wellness_activity",
        "data": {
            "activity_type": params.activity_type,
            "duration": params.duration,
            "intensity": params.intensity,
            "notes": params.notes,
            "recorded_at": datetime.now().isoformat()
        }
    }


@register_tool(
    "check_bank_balance",
    "Check the user's bank account balance. Use when user asks about money, funds, or affordability.",
    CheckBankBalanceParams
)
def handle_check_bank_balance(params: CheckBankBalanceParams) -> Dict[str, Any]:
    balance_data = MockDataProvider.get_bank_balance(params.account_type)
    return {
        "tool_result": "bank_balance",
        "data": {
            "account_type": params.account_type,
            "balance": balance_data["balance"],
            "currency": balance_data.get("currency", "USD")
        }
    }


@register_tool(
    "get_calendar_events",
    "Get upcoming calendar events. Use when user asks about schedule, meetings, or availability.",
    GetCalendarEventsParams
)
def handle_get_calendar_events(params: GetCalendarEventsParams) -> Dict[str, Any]:
    events = MockDataProvider.get_calendar_events(params.start_date, params.end_date)
    return {
        "tool_result": "calendar_events",
        "data": {"events": events}
    }


@register_tool(
    "create_calendar_event",
    "Create a new calendar event. Use when user wants to schedule a meeting or appointment.",
    CreateCalendarEventParams
)
def handle_create_calendar_event(params: CreateCalendarEventParams) -> Dict[str, Any]:
    # Note: This would integrate with Google Calendar API in production
    return {
        "action": "create_calendar_event",
        "data": {
            "title": params.title,
            "start_time": params.start_time,
            "end_time": params.end_time,
            "description": params.description,
            "location": params.location
        }
    }


@register_tool(
    "get_health_metrics",
    "Get recent health and fitness metrics (sleep, steps, heart rate).",
    BaseModel  # No params needed
)
def handle_get_health_metrics(params: BaseModel) -> Dict[str, Any]:
    metrics = MockDataProvider.get_health_metrics()
    return {
        "tool_result": "health_metrics",
        "data": metrics
    }


@register_tool(
    "get_recent_transactions",
    "Get recent financial transactions to analyze spending patterns.",
    BaseModel  # No params needed
)
def handle_get_recent_transactions(params: BaseModel) -> Dict[str, Any]:
    transactions = MockDataProvider.get_recent_transactions()
    return {
        "tool_result": "transactions",
        "data": {"transactions": transactions}
    }


# =============================================================================
# TOOL EXECUTOR
# =============================================================================

class ToolExecutor:
    """
    Executes tools based on LLM function calls.
    Returns structured actions for the action_applier to persist.
    """
    
    def __init__(self):
        self.tools = TOOL_REGISTRY
        self.mock_provider = MockDataProvider()
    
    def get_tool_definitions(self) -> List[Dict[str, Any]]:
        """Get all tools in OpenAI/Groq format"""
        return [tool.to_openai_format() for tool in self.tools.values()]
    
    async def execute_tool(
        self, 
        tool_name: str, 
        tool_args: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a tool by name with validated arguments.
        Returns result that can be passed to action_applier or shown to user.
        """
        if tool_name not in self.tools:
            return {
                "success": False,
                "error": f"Unknown tool: {tool_name}",
                "available_tools": list(self.tools.keys())
            }
        
        tool = self.tools[tool_name]
        
        try:
            # Validate arguments with Pydantic
            params = tool.params_model(**tool_args)
            
            # Execute handler
            result = tool.handler(params)
            
            logger.info(f"Tool executed: {tool_name} with args {tool_args}")
            return {
                "success": True,
                "tool_name": tool_name,
                "result": result
            }
            
        except Exception as e:
            logger.error(f"Tool execution failed: {tool_name} - {e}")
            return {
                "success": False,
                "error": str(e),
                "tool_name": tool_name
            }
    
    def extract_tool_calls_from_response(self, llm_response: str) -> List[Dict[str, Any]]:
        """
        Extract tool calls from LLM response text (fallback if not using native function calling).
        Looks for patterns like: {"tool": "create_task", "arguments": {...}}
        """
        import re
        
        tool_calls = []
        
        # Pattern 1: Fenced JSON with tool call
        pattern = r'```json\s*({\s*"tool"\s*:\s*"[^"]+"\s*,\s*"arguments"\s*:.*?})\s*```'
        matches = re.findall(pattern, llm_response, re.DOTALL)
        
        for match in matches:
            try:
                call = json.loads(match)
                if "tool" in call and "arguments" in call:
                    tool_calls.append({
                        "name": call["tool"],
                        "arguments": call["arguments"]
                    })
            except json.JSONDecodeError:
                continue
        
        # Pattern 2: Direct JSON object
        if llm_response.strip().startswith('{'):
            try:
                obj = json.loads(llm_response)
                if "tool" in obj and "arguments" in obj:
                    tool_calls.append({
                        "name": obj["tool"],
                        "arguments": obj["arguments"]
                    })
            except json.JSONDecodeError:
                pass
        
        return tool_calls


tool_executor = ToolExecutor()
