"""
Durable Action Contracts (Sprint 2, Mission 2)

Centralised schema definitions and validation for every agent action.
Actions that don't match a registered schema are REJECTED with a clear
error message instead of silently dropped.

Usage:
    from agents.services.action_schema import validate_action, ActionValidationError

    try:
        validate_action({"action": "create_task", "data": {"title": "Do stuff"}})
    except ActionValidationError as e:
        print(e)   # human-readable rejection reason
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List, Optional, Set

# ---------------------------------------------------------------------------
# Exception
# ---------------------------------------------------------------------------


class ActionValidationError(Exception):
    """Raised when an action payload fails schema validation."""

    def __init__(self, action: str, errors: List[str]):
        self.action = action
        self.errors = errors
        msg = f"Action '{action}' rejected: " + "; ".join(errors)
        super().__init__(msg)


# ---------------------------------------------------------------------------
# Field spec helpers
# ---------------------------------------------------------------------------

def _is_non_empty_str(value: Any) -> bool:
    return isinstance(value, str) and len(value.strip()) > 0


def _is_optional_str(value: Any) -> bool:
    return value is None or isinstance(value, str)


def _is_positive_int(value: Any) -> bool:
    return isinstance(value, int) and value > 0


def _is_valid_priority(value: Any) -> bool:
    return value in ("low", "medium", "high", "urgent")


def _is_valid_status(value: Any) -> bool:
    return value in ("todo", "in_progress", "completed", "cancelled")


def _is_valid_meal_type(value: Any) -> bool:
    return value in ("breakfast", "lunch", "dinner", "snack")


def _is_valid_activity_type(value: Any) -> bool:
    return value in ("exercise", "meditation", "sleep", "hydration", "mood")


def _is_valid_frequency(value: Any) -> bool:
    return value in ("daily", "weekdays", "weekends", "weekly", "custom")


def _is_valid_category(value: Any) -> bool:
    return value in (
        "health", "productivity", "mindfulness", "learning",
        "social", "self_care", "finance", "other",
    )


def _is_iso_date(value: Any) -> bool:
    """Accept YYYY-MM-DD strings."""
    if not isinstance(value, str):
        return False
    try:
        datetime.strptime(value, "%Y-%m-%d")
        return True
    except ValueError:
        return False


def _is_hex_color(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    return bool(re.match(r"^#[0-9A-Fa-f]{6}$", value))


# ---------------------------------------------------------------------------
# Schema registry
# ---------------------------------------------------------------------------

class _FieldSpec:
    """Declarative field validator."""

    def __init__(
        self,
        *,
        required: bool = False,
        validator=None,
        label: str = "",
        default: Any = None,
    ):
        self.required = required
        self.validator = validator
        self.label = label
        self.default = default


# Maps action_name → {field_name → _FieldSpec}
ACTION_SCHEMAS: Dict[str, Dict[str, _FieldSpec]] = {
    "create_task": {
        "title": _FieldSpec(required=True, validator=_is_non_empty_str, label="non-empty string"),
        "description": _FieldSpec(validator=_is_optional_str, label="string or null"),
        "priority": _FieldSpec(validator=_is_valid_priority, label="low|medium|high|urgent", default="medium"),
        "status": _FieldSpec(validator=_is_valid_status, label="todo|in_progress|completed|cancelled", default="todo"),
        "due_date": _FieldSpec(validator=_is_optional_str, label="ISO datetime string or null"),
    },
    "create_meal_plan": {
        "meal_name": _FieldSpec(required=True, validator=_is_non_empty_str, label="non-empty string"),
        "date": _FieldSpec(required=True, validator=_is_iso_date, label="YYYY-MM-DD"),
        "meal_type": _FieldSpec(validator=_is_valid_meal_type, label="breakfast|lunch|dinner|snack", default="dinner"),
        "ingredients": _FieldSpec(label="list or null"),
        "instructions": _FieldSpec(validator=_is_optional_str, label="string or null"),
        "nutritional_info": _FieldSpec(label="dict or null"),
        "preferences": _FieldSpec(label="dict or null"),
    },
    "create_study_session": {
        "subject": _FieldSpec(required=True, validator=_is_non_empty_str, label="non-empty string"),
        "topic": _FieldSpec(validator=_is_optional_str, label="string or null"),
        "duration": _FieldSpec(required=True, validator=_is_positive_int, label="positive integer (minutes)"),
        "notes": _FieldSpec(validator=_is_optional_str, label="string or null"),
        "resources": _FieldSpec(label="list or null"),
    },
    "create_wellness_activity": {
        "activity_type": _FieldSpec(required=True, validator=_is_valid_activity_type, label="exercise|meditation|sleep|hydration|mood"),
        "duration": _FieldSpec(label="integer (minutes) or null"),
        "intensity": _FieldSpec(validator=_is_optional_str, label="string or null"),
        "notes": _FieldSpec(validator=_is_optional_str, label="string or null"),
        "recorded_at": _FieldSpec(validator=_is_optional_str, label="ISO datetime string or null"),
    },
    "create_habit": {
        "name": _FieldSpec(required=True, validator=_is_non_empty_str, label="non-empty string"),
        "description": _FieldSpec(validator=_is_optional_str, label="string or null"),
        "category": _FieldSpec(validator=_is_valid_category, label="health|productivity|...|other", default="other"),
        "frequency": _FieldSpec(validator=_is_valid_frequency, label="daily|weekdays|weekends|weekly|custom", default="daily"),
        "target_count": _FieldSpec(validator=_is_positive_int, label="positive integer", default=1),
        "icon": _FieldSpec(validator=_is_optional_str, label="emoji string", default="✅"),
        "color": _FieldSpec(validator=_is_hex_color, label="#RRGGBB hex color", default="#8B5CF6"),
    },
}

# Set of all registered action names (used by ActionApplier)
REGISTERED_ACTIONS: Set[str] = set(ACTION_SCHEMAS.keys())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_action(action_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate an action dict ``{"action": "...", "data": {...}}``.

    Returns:
        The *normalised* data dict with defaults applied for missing optional fields.

    Raises:
        ActionValidationError: If the action name is unknown or required fields are
            missing / malformed.
    """
    action_name = action_payload.get("action") or action_payload.get("type")
    data = action_payload.get("data", {})

    if not action_name:
        raise ActionValidationError("(unknown)", ["Missing 'action' field"])

    if action_name not in ACTION_SCHEMAS:
        raise ActionValidationError(
            action_name,
            [f"Unknown action '{action_name}'. Registered actions: {sorted(REGISTERED_ACTIONS)}"],
        )

    schema = ACTION_SCHEMAS[action_name]
    errors: List[str] = []
    normalised: Dict[str, Any] = {}

    for field_name, spec in schema.items():
        value = data.get(field_name)

        # Apply default when missing
        if value is None and spec.default is not None:
            value = spec.default

        # Required check
        if spec.required and value is None:
            errors.append(f"Missing required field '{field_name}' ({spec.label})")
            continue

        # Validator check
        if value is not None and spec.validator and not spec.validator(value):
            errors.append(
                f"Invalid value for '{field_name}': expected {spec.label}, got {type(value).__name__}={value!r}"
            )
            continue

        normalised[field_name] = value

    # Pass through any extra keys not in schema (forward-compatible)
    for k, v in data.items():
        if k not in normalised:
            normalised[k] = v

    if errors:
        raise ActionValidationError(action_name, errors)

    return normalised


def get_action_schema_summary() -> Dict[str, Any]:
    """Return a human-readable summary of all registered action schemas."""
    summary = {}
    for action_name, fields in ACTION_SCHEMAS.items():
        summary[action_name] = {
            fname: {
                "required": spec.required,
                "type": spec.label,
                "default": spec.default,
            }
            for fname, spec in fields.items()
        }
    return summary
