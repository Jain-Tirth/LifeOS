"""
Dynamic tool registry for execution agent.

Replaces hardcoded tool descriptions with a centralized, maintainable registry
that can be used by both the execution agent and documentation systems.
"""
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
import json


@dataclass
class ToolParameter:
    """Definition of a single tool parameter."""
    name: str
    type: str
    required: bool = False
    description: str = ""
    default: Optional[Any] = None
    enum_values: Optional[List[str]] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        result = {
            "name": self.name,
            "type": self.type,
            "required": self.required,
            "description": self.description,
        }
        if self.default is not None:
            result["default"] = self.default
        if self.enum_values:
            result["enum"] = self.enum_values
        if self.min_length is not None:
            result["min_length"] = self.min_length
        if self.max_length is not None:
            result["max_length"] = self.max_length
        return result


@dataclass
class Tool:
    """Definition of a single executable tool."""
    name: str
    description: str
    category: str  # "task", "event", "communication", "habit"
    parameters: List[ToolParameter] = field(default_factory=list)
    examples: List[Dict[str, Any]] = field(default_factory=list)
    notes: str = ""
    
    def to_instruction_text(self) -> str:
        """Convert to plain text for inclusion in agent instruction."""
        params_text = ""
        for param in self.parameters:
            required_mark = "(required)" if param.required else "(optional)"
            params_text += f"  - {param.name} {required_mark}: {param.description}\n"
            if param.enum_values:
                enum_str = " | ".join(param.enum_values)
                params_text += f"    Options: {enum_str}\n"
        
        examples_text = ""
        if self.examples:
            examples_text = "\nExample:\n"
            for i, example in enumerate(self.examples, 1):
                examples_text += f"{json.dumps(example, indent=2)}\n"
        
        return f"""TOOL: {self.name}
Description: {self.description}

Parameters:
{params_text}
{examples_text}
{f"Notes: {self.notes}" if self.notes else ""}
"""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "category": self.category,
            "parameters": [p.to_dict() for p in self.parameters],
            "examples": self.examples,
            "notes": self.notes,
        }


class ToolRegistry:
    """Centralized registry of all executable tools."""
    
    def __init__(self):
        self.tools: Dict[str, Tool] = {}
        self._initialize_tools()
    
    def _initialize_tools(self):
        """Initialize all available tools."""
        
        # ====== TASK MANAGEMENT TOOLS ======
        self.register_tool(Tool(
            name="create_task",
            description="Create a new task in the database",
            category="task",
            parameters=[
                ToolParameter("title", "string", required=True, 
                            description="Task title (1-200 chars)"),
                ToolParameter("description", "string", required=False,
                            description="Task description (optional, max 2000 chars)"),
                ToolParameter("priority", "string", required=False,
                            description="Task priority level",
                            default="medium",
                            enum_values=["low", "medium", "high", "urgent"]),
                ToolParameter("status", "string", required=False,
                            description="Initial task status",
                            default="todo",
                            enum_values=["todo", "in_progress", "completed", "cancelled"]),
                ToolParameter("due_date", "datetime", required=False,
                            description="ISO datetime string (e.g., 2026-05-15T09:00:00)"),
            ],
            examples=[
                {
                    "action": "create_task",
                    "data": {
                        "title": "Complete project proposal",
                        "priority": "high",
                        "due_date": "2026-05-20T17:00:00"
                    }
                }
            ],
            notes="Task is stored in database with full history tracking."
        ))
        
        self.register_tool(Tool(
            name="update_task",
            description="Update an existing task",
            category="task",
            parameters=[
                ToolParameter("task_id", "string", required=False,
                            description="ID of task to update"),
                ToolParameter("title", "string", required=True,
                            description="New task title"),
                ToolParameter("description", "string", required=False,
                            description="New task description"),
                ToolParameter("priority", "string", required=False,
                            description="New priority level",
                            enum_values=["low", "medium", "high", "urgent"]),
                ToolParameter("status", "string", required=False,
                            description="New task status",
                            enum_values=["todo", "in_progress", "completed", "cancelled"]),
                ToolParameter("due_date", "datetime", required=False,
                            description="New due date"),
            ],
            examples=[
                {
                    "action": "update_task",
                    "data": {
                        "task_id": "task_123",
                        "status": "in_progress",
                        "priority": "high"
                    }
                }
            ]
        ))
        
        # ====== CALENDAR EVENT TOOLS ======
        self.register_tool(Tool(
            name="create_event",
            description="Create a Google Calendar event",
            category="event",
            parameters=[
                ToolParameter("title", "string", required=True,
                            description="Event title (1-200 chars)"),
                ToolParameter("description", "string", required=False,
                            description="Event description"),
                ToolParameter("start_time", "datetime", required=True,
                            description="ISO datetime (e.g., 2026-05-10T14:00:00)"),
                ToolParameter("end_time", "datetime", required=True,
                            description="ISO datetime, must be after start_time"),
                ToolParameter("location", "string", required=False,
                            description="Event location"),
                ToolParameter("attendees", "list[email]", required=False,
                            description="List of attendee email addresses"),
            ],
            examples=[
                {
                    "action": "create_event",
                    "data": {
                        "title": "Team Meeting",
                        "start_time": "2026-05-10T14:00:00",
                        "end_time": "2026-05-10T15:00:00",
                        "location": "Conference Room A"
                    }
                }
            ],
            notes="Events sync with Google Calendar. Attendees are auto-invited."
        ))
        
        self.register_tool(Tool(
            name="update_event",
            description="Update an existing calendar event",
            category="event",
            parameters=[
                ToolParameter("event_id", "string", required=False,
                            description="ID of event to update"),
                ToolParameter("title", "string", required=True,
                            description="New event title"),
                ToolParameter("description", "string", required=False,
                            description="New description"),
                ToolParameter("start_time", "datetime", required=True,
                            description="New start time (ISO format)"),
                ToolParameter("end_time", "datetime", required=True,
                            description="New end time (ISO format)"),
                ToolParameter("location", "string", required=False,
                            description="New location"),
                ToolParameter("attendees", "list[email]", required=False,
                            description="Updated attendee list"),
            ]
        ))
        
        # ====== EMAIL TOOLS ======
        self.register_tool(Tool(
            name="draft_email",
            description="Draft a professional email",
            category="communication",
            parameters=[
                ToolParameter("subject", "string", required=True,
                            description="Email subject (1-100 chars)"),
                ToolParameter("body", "string", required=True,
                            description="Email body content (1-10000 chars)"),
                ToolParameter("to_address", "email", required=True,
                            description="Recipient email address"),
                ToolParameter("from_address", "email", required=False,
                            description="Sender email (defaults to user's email)"),
            ],
            examples=[
                {
                    "action": "draft_email",
                    "data": {
                        "subject": "Project Update",
                        "body": "Hi Sarah,\n\nHere's the status...",
                        "to_address": "sarah@company.com"
                    }
                }
            ],
            notes="Draft is stored in database. Not automatically sent."
        ))
        
        # ====== HABIT TOOLS ======
        self.register_tool(Tool(
            name="create_habit",
            description="Store a new habit or routine",
            category="habit",
            parameters=[
                ToolParameter("name", "string", required=True,
                            description="Habit name (1-100 chars)"),
                ToolParameter("description", "string", required=False,
                            description="Habit description (max 500 chars)"),
                ToolParameter("category", "string", required=False,
                            description="Habit category",
                            default="other",
                            enum_values=["health", "productivity", "mindfulness", "learning",
                                       "social", "self_care", "finance", "other"]),
                ToolParameter("frequency", "string", required=False,
                            description="How often the habit occurs",
                            default="daily",
                            enum_values=["daily", "weekdays", "weekends", "weekly", "custom"]),
                ToolParameter("target_count", "integer", required=False,
                            description="Target repetitions per period", default=1),
                ToolParameter("icon", "emoji", required=False,
                            description="Visual emoji (1-2 chars)", default="✅"),
                ToolParameter("color", "hex_color", required=False,
                            description="Hex color (#RRGGBB)", default="#8B5CF6"),
            ],
            examples=[
                {
                    "action": "create_habit",
                    "data": {
                        "name": "Morning meditation",
                        "category": "mindfulness",
                        "frequency": "daily",
                        "icon": "🧘"
                    }
                }
            ]
        ))
    
    def register_tool(self, tool: Tool) -> None:
        """Register a tool in the registry."""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> Optional[Tool]:
        """Get a tool by name."""
        return self.tools.get(name)
    
    def get_all_tools(self) -> Dict[str, Tool]:
        """Get all registered tools."""
        return self.tools.copy()
    
    def get_tool_names(self) -> List[str]:
        """Get all tool names."""
        return sorted(self.tools.keys())
    
    def get_tools_by_category(self, category: str) -> List[Tool]:
        """Get all tools in a category."""
        return [t for t in self.tools.values() if t.category == category]
    
    def to_instruction_section(self) -> str:
        """
        Generate tool registry section for agent instruction.
        
        This replaces {dynamic_tool_registry} placeholder in agent prompts.
        """
        sections = []
        
        # Group tools by category
        categories = {}
        for tool in self.tools.values():
            if tool.category not in categories:
                categories[tool.category] = []
            categories[tool.category].append(tool)
        
        # Generate instruction text for each category
        for category in sorted(categories.keys()):
            category_title = category.upper().replace("_", " ")
            sections.append(f"\n=== {category_title} TOOLS ===\n")
            
            for tool in categories[category]:
                sections.append(tool.to_instruction_text())
                sections.append("\n")
        
        return "".join(sections)
    
    def to_json_schema(self) -> Dict[str, Any]:
        """Export registry as JSON schema."""
        return {
            "tools": [t.to_dict() for t in self.tools.values()],
            "count": len(self.tools),
        }


# Global registry instance
_REGISTRY: Optional[ToolRegistry] = None


def get_tool_registry() -> ToolRegistry:
    """Get or create the global tool registry."""
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = ToolRegistry()
    return _REGISTRY
