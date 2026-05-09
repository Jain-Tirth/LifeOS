from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator, model_validator
import re

class DietaryPreferences(BaseModel):
    type: str = Field(
        'omnivore',
        pattern=r'^(vegetarian|vegan|omnivore|pescatarian)$'
    )
    allergies: List[str] = Field(default_factory=list, max_length=10)
    cuisine: List[str] = Field(default_factory=list, max_length=10)

    @validator('allergies', 'cuisine', pre=True)
    def sanitize_lists(cls, v):
        if not isinstance(v, list):
            raise ValueError('Must be list')
        return [str(item).strip()[:100] for item in v]

class WorkHours(BaseModel):
    start: str = Field(pattern=r'^\d{2}:\d{2}$')
    end: str = Field(pattern=r'^\d{2}:\d{2}$')
    days: List[str] = Field(
        default=['Mon', 'Tue', 'Wed', 'Thu', 'Fri'],
        max_length=7
    )

class Goal(BaseModel):
    goal: str = Field(max_length=200)
    deadline: Optional[str] = Field(None, pattern=r'^\d{4}-\d{2}-\d{2}$')
    category: str = Field(pattern=r'^(wellness|productivity|learning|finance)$')

class UserContextSchema(BaseModel):
    """
    Validated schema for user context injected into agents.
    Prevents prompt injection, SQL injection, buffer overflows.
    """
    name: str = Field(default='', max_length=150)
    timezone: str = Field(
        default='Asia/Kolkata',
        pattern=r'^[A-Za-z_/]+$'  # Valid IANA timezone format
    )
    dietary_preferences: Optional[DietaryPreferences] = None
    fitness_level: str = Field(
        default='intermediate',
        pattern=r'^(beginner|intermediate|advanced)$'
    )
    health_conditions: List[str] = Field(
        default_factory=list,
        max_length=20
    )
    work_hours: Optional[WorkHours] = None
    learning_style: str = Field(
        default='visual',
        pattern=r'^(visual|auditory|reading|kinesthetic)$'
    )
    goals: List[Goal] = Field(default_factory=list, max_length=10)
    about_me: str = Field(default='', max_length=1000)

    @validator('name', 'about_me', pre=True)
    def sanitize_text(cls, v):
        if not isinstance(v, str):
            return ''
        # Remove control characters
        v = ''.join(c for c in v if ord(c) >= 32 or c in '\n\t')
        return v.strip()

    @validator('health_conditions', pre=True)
    def sanitize_health_conditions(cls, v):
        if not isinstance(v, list):
            return []
        return [str(item).strip()[:100] for item in v]

    @model_validator(mode='after')
    def no_injection_patterns(self):
        """Detect common prompt/SQL injection patterns"""
        dangerous_patterns = [
            r'<script',
            r'javascript:',
            r'on\w+\s*=',  # onclick= onerror=
            r'--\s*$',      # SQL comment
            r';\s*DROP',    # SQL DROP
            r'\*\/.*\/\*',  # SQL comment block
            r'__import__',  # Python injection
            r'eval\s*\(',   # Python eval
        ]

        values = self.model_dump()
        for field_name, field_value in values.items():
            if isinstance(field_value, str):
                for pattern in dangerous_patterns:
                    if re.search(pattern, field_value, re.IGNORECASE):
                        raise ValueError(
                            f"Detected injection pattern in {field_name}: {pattern}"
                        )
            elif isinstance(field_value, list):
                for item in field_value:
                    if isinstance(item, str):
                        for pattern in dangerous_patterns:
                            if re.search(pattern, item, re.IGNORECASE):
                                raise ValueError(
                                    f"Detected injection pattern in {field_name}: {pattern}"
                                )

        return self

class ContextValidator:
    """Singleton context validator"""

    @staticmethod
    def validate(context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate user context.
        Raises ValueError if invalid.
        Returns sanitized context.
        """
        try:
            validated = UserContextSchema(**context)
            return validated.model_dump(exclude_none=True)
        except Exception as e:
            raise ValueError(f"Invalid user context: {str(e)}")

# Global instance
context_validator = ContextValidator()
