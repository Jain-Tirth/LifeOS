"""
Pydantic models for strict schema enforcement of agent outputs.

These models ensure all agent actions are type-safe, validated, and compatible
with the backend execution layer.
"""
from typing import Any, Dict, List, Optional, Literal
from datetime import datetime
from pydantic import BaseModel, Field, validator, root_validator
import json


# ============================================================================
# CORE ACTION MODELS
# ============================================================================

class ActionData(BaseModel):
    """Base class for action data payloads."""
    
    class Config:
        extra = "forbid"  # Reject unknown fields


class CreateTaskData(ActionData):
    """Schema for create_task action."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Literal["low", "medium", "high", "urgent"] = Field("medium")
    status: Literal["todo", "in_progress", "completed", "cancelled"] = Field("todo")
    due_date: Optional[str] = Field(None)  # ISO datetime, validated later
    
    @validator("title")
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError("title cannot be empty or whitespace")
        return v.strip()
    
    @validator("due_date")
    def validate_due_date(cls, v):
        if v is None:
            return None
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError(f"Invalid ISO datetime: {v}")


class UpdateTaskData(ActionData):
    """Schema for update_task action."""
    task_id: Optional[str] = Field(None)
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    priority: Optional[Literal["low", "medium", "high", "urgent"]] = None
    status: Optional[Literal["todo", "in_progress", "completed", "cancelled"]] = None
    due_date: Optional[str] = Field(None)
    
    @validator("title")
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError("title cannot be empty or whitespace")
        return v.strip()
    
    @validator("due_date")
    def validate_due_date(cls, v):
        if v is None:
            return None
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError(f"Invalid ISO datetime: {v}")


class CreateEventData(ActionData):
    """Schema for create_event action."""
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    start_time: str = Field(...)  # ISO datetime
    end_time: str = Field(...)    # ISO datetime
    location: Optional[str] = Field(None, max_length=500)
    attendees: Optional[List[str]] = Field(None)
    
    @validator("title")
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError("title cannot be empty or whitespace")
        return v.strip()
    
    @validator("start_time", "end_time")
    def validate_datetime(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError(f"Invalid ISO datetime: {v}")
    
    @validator("attendees")
    def validate_attendees(cls, v):
        if v is None:
            return None
        if not isinstance(v, list):
            raise ValueError("attendees must be a list")
        # Basic email format check
        for email in v:
            if "@" not in email or "." not in email:
                raise ValueError(f"Invalid email format: {email}")
        return v
    
    @root_validator
    def validate_times(cls, values):
        start = values.get("start_time")
        end = values.get("end_time")
        if start and end:
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            if end_dt <= start_dt:
                raise ValueError("end_time must be after start_time")
        return values


class UpdateEventData(ActionData):
    """Schema for update_event action."""
    event_id: Optional[str] = None
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=2000)
    start_time: str = Field(...)
    end_time: str = Field(...)
    location: Optional[str] = Field(None, max_length=500)
    attendees: Optional[List[str]] = None
    
    @validator("title")
    def validate_title(cls, v):
        if not v.strip():
            raise ValueError("title cannot be empty or whitespace")
        return v.strip()
    
    @validator("start_time", "end_time")
    def validate_datetime(cls, v):
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError(f"Invalid ISO datetime: {v}")
    
    @root_validator
    def validate_times(cls, values):
        start = values.get("start_time")
        end = values.get("end_time")
        if start and end:
            start_dt = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_dt = datetime.fromisoformat(end.replace('Z', '+00:00'))
            if end_dt <= start_dt:
                raise ValueError("end_time must be after start_time")
        return values


class DraftEmailData(ActionData):
    """Schema for draft_email action."""
    subject: str = Field(..., min_length=1, max_length=100)
    body: str = Field(..., min_length=1, max_length=10000)
    to_address: str = Field(...)
    from_address: Optional[str] = None
    
    @validator("subject", "body")
    def validate_content(cls, v):
        if not v.strip():
            raise ValueError("content cannot be empty or whitespace")
        return v.strip()
    
    @validator("to_address", "from_address")
    def validate_email(cls, v):
        if v is None:
            return None
        if "@" not in v or "." not in v:
            raise ValueError(f"Invalid email format: {v}")
        return v.strip()


class CreateHabitData(ActionData):
    """Schema for create_habit action."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    category: Literal[
        "health", "productivity", "mindfulness", "learning",
        "social", "self_care", "finance", "other"
    ] = "other"
    frequency: Literal["daily", "weekdays", "weekends", "weekly", "custom"] = "daily"
    target_count: int = Field(1, ge=1)
    icon: Optional[str] = Field("✅", max_length=2)
    color: Optional[str] = Field("#8B5CF6")
    
    @validator("name")
    def validate_name(cls, v):
        if not v.strip():
            raise ValueError("name cannot be empty or whitespace")
        return v.strip()
    
    @validator("color")
    def validate_color(cls, v):
        if v and not v.startswith("#"):
            raise ValueError("color must be hex format (#RRGGBB)")
        return v


# ACTION TYPE MAPPING
ACTION_TYPE_MAP = {
    "create_task": CreateTaskData,
    "update_task": UpdateTaskData,
    "create_event": CreateEventData,
    "update_event": UpdateEventData,
    "draft_email": DraftEmailData,
    "create_habit": CreateHabitData,
}


class Action(BaseModel):
    """Single executable action."""
    action: str = Field(..., description="Tool name")
    data: Dict[str, Any] = Field(default_factory=dict)
    
    @validator("action")
    def validate_action_type(cls, v):
        if v not in ACTION_TYPE_MAP:
            raise ValueError(
                f"Unknown action '{v}'. "
                f"Valid actions: {sorted(ACTION_TYPE_MAP.keys())}"
            )
        return v
    
    @root_validator
    def validate_action_data(cls, values):
        """Validate data against specific action schema."""
        action_type = values.get("action")
        data = values.get("data", {})
        
        if not action_type:
            return values
        
        # Get the appropriate Pydantic model for this action
        action_model = ACTION_TYPE_MAP.get(action_type)
        if action_model:
            try:
                # Validate data against the model
                validated_data = action_model(**data)
                # Replace with validated (and potentially normalized) data
                values["data"] = validated_data.dict()
            except Exception as e:
                raise ValueError(
                    f"Invalid data for action '{action_type}': {str(e)}"
                )
        return values


class AgentResponse(BaseModel):
    """Response from execution agent."""
    actions: List[Action] = Field(default_factory=list)
    
    @validator("actions")
    def validate_actions(cls, v):
        if not isinstance(v, list):
            raise ValueError("actions must be a list")
        return v


# ============================================================================
# PARSING & VALIDATION
# ============================================================================

def parse_agent_response(response_text: str) -> AgentResponse:
    """
    Parse and validate raw LLM response into typed AgentResponse.
    
    Args:
        response_text: Raw text from LLM
        
    Returns:
        Validated AgentResponse
        
    Raises:
        ValueError: If parsing or validation fails
    """
    # Extract JSON if wrapped in markdown
    response_text = response_text.strip()
    if response_text.startswith("```"):
        # Remove markdown code blocks
        response_text = response_text.split("```")[1]
        if response_text.startswith("json"):
            response_text = response_text[4:]
        response_text = response_text.strip()
    
    try:
        data = json.loads(response_text)
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse JSON: {str(e)}\nResponse: {response_text}")
    
    try:
        return AgentResponse(**data)
    except Exception as e:
        raise ValueError(f"Response validation failed: {str(e)}\nData: {data}")


def validate_action_for_execution(action: Action) -> Action:
    """
    Validate action is ready for backend execution.
    
    This is called AFTER the execution agent emits actions,
    before they're sent to the tool executor.
    
    Args:
        action: Action to validate
        
    Returns:
        Validated action
        
    Raises:
        ValueError: If validation fails
    """
    # Re-validate using the model (this is redundant but defensive)
    try:
        validated_action = Action(**action.dict())
        return validated_action
    except Exception as e:
        raise ValueError(f"Action failed execution validation: {str(e)}")
