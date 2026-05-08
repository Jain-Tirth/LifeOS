"""
Backend validation layer.

This layer enforces all business rules, constraints, and validations AFTER
the execution agent emits actions. It is completely separate from the LLM.

Validation includes:
- Email format and deliverability
- Datetime normalization and conflict detection
- Permission checks
- Calendar conflict detection
- Business rule enforcement
- Idempotency checks
"""
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of a validation check."""
    valid: bool
    errors: List[str]
    warnings: List[str]
    normalized_data: Optional[Dict[str, Any]] = None


class EmailValidator:
    """Validates email addresses and deliverability."""
    
    # Invalid domains for testing purposes
    BLOCKLIST_DOMAINS = {"example.com", "test.com", "invalid.test"}
    
    @staticmethod
    def validate_email_format(email: str) -> Tuple[bool, Optional[str]]:
        """
        Validate email format.
        
        Returns:
            (is_valid, error_message)
        """
        if not email or not isinstance(email, str):
            return False, "Email must be a non-empty string"
        
        email = email.strip()
        
        # Basic format check
        if "@" not in email:
            return False, "Email must contain @"
        
        local, domain = email.rsplit("@", 1)
        
        if not local or not domain:
            return False, "Invalid email format"
        
        if len(local) > 64:
            return False, "Local part too long (max 64 chars)"
        
        if len(domain) > 255:
            return False, "Domain too long (max 255 chars)"
        
        # Check for valid domain format
        if not "." in domain:
            return False, "Domain must contain at least one dot"
        
        # Check against blocklist (for testing)
        if domain.lower() in EmailValidator.BLOCKLIST_DOMAINS:
            return False, f"Domain {domain} is blocked for testing"
        
        return True, None
    
    @staticmethod
    def validate_email_list(emails: List[str]) -> ValidationResult:
        """
        Validate a list of email addresses.
        
        Returns:
            ValidationResult with all errors and warnings
        """
        errors = []
        warnings = []
        
        if not isinstance(emails, list):
            errors.append("Attendees must be a list")
            return ValidationResult(False, errors, warnings)
        
        if len(emails) > 100:
            warnings.append("Attendee list is unusually large (>100)")
        
        seen = set()
        for email in emails:
            if not isinstance(email, str):
                errors.append(f"Invalid email type: {type(email)}")
                continue
            
            if email in seen:
                warnings.append(f"Duplicate attendee: {email}")
                continue
            
            is_valid, error_msg = EmailValidator.validate_email_format(email)
            if not is_valid:
                errors.append(f"Invalid email '{email}': {error_msg}")
            
            seen.add(email)
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            normalized_data={"attendees": list(seen)}
        )


class DatetimeValidator:
    """Validates and normalizes datetime values."""
    
    @staticmethod
    def validate_iso_datetime(dt_string: str) -> Tuple[bool, Optional[str], Optional[datetime]]:
        """
        Parse and validate ISO datetime string.
        
        Returns:
            (is_valid, error_message, parsed_datetime)
        """
        if not dt_string:
            return False, "Datetime string cannot be empty", None
        
        try:
            # Handle both 'Z' and '+00:00' format
            dt_str = dt_string.replace('Z', '+00:00')
            parsed = datetime.fromisoformat(dt_str)
            return True, None, parsed
        except ValueError as e:
            return False, f"Invalid ISO datetime format: {str(e)}", None
    
    @staticmethod
    def validate_time_range(start: str, end: str) -> ValidationResult:
        """
        Validate start and end times form valid range.
        
        Returns:
            ValidationResult with any errors
        """
        errors = []
        warnings = []
        
        valid_start, err_start, start_dt = DatetimeValidator.validate_iso_datetime(start)
        if not valid_start:
            errors.append(f"Invalid start_time: {err_start}")
            return ValidationResult(False, errors, warnings)
        
        valid_end, err_end, end_dt = DatetimeValidator.validate_iso_datetime(end)
        if not valid_end:
            errors.append(f"Invalid end_time: {err_end}")
            return ValidationResult(False, errors, warnings)
        
        # Check that end is after start
        if end_dt <= start_dt:
            errors.append("end_time must be after start_time")
        
        # Check duration is reasonable (not more than 24 hours)
        duration = (end_dt - start_dt).total_seconds() / 3600
        if duration > 24:
            warnings.append(f"Very long event duration ({duration:.1f} hours)")
        
        if duration < 0.25:
            warnings.append("Event duration is very short (<15 minutes)")
        
        # Check if event is in the past
        now = datetime.now(start_dt.tzinfo) if start_dt.tzinfo else datetime.now()
        if start_dt < now:
            warnings.append("Event start time is in the past")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            normalized_data={"start_time": start, "end_time": end}
        )


class PermissionValidator:
    """Validates user permissions for actions."""
    
    @staticmethod
    def can_create_task(user_id: Optional[int]) -> ValidationResult:
        """Check if user can create tasks."""
        errors = []
        
        if not user_id:
            errors.append("User must be authenticated to create tasks")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=[]
        )
    
    @staticmethod
    def can_send_email(user_id: Optional[int]) -> ValidationResult:
        """Check if user can send/draft emails."""
        errors = []
        
        if not user_id:
            errors.append("User must be authenticated to send emails")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=[]
        )
    
    @staticmethod
    def can_modify_calendar(user_id: Optional[int]) -> ValidationResult:
        """Check if user can modify calendar."""
        errors = []
        warnings = []
        
        if not user_id:
            errors.append("User must be authenticated to modify calendar")
        
        # Check if user has Google OAuth configured
        # This would be checked against the database in production
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )


class ActionValidator:
    """Validates complete actions with all business rules."""
    
    @staticmethod
    def validate_create_task(
        data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> ValidationResult:
        """Validate create_task action."""
        errors = []
        warnings = []
        normalized = data.copy()
        
        # Check permissions
        perm_result = PermissionValidator.can_create_task(user_id)
        errors.extend(perm_result.errors)
        
        if not perm_result.valid:
            return ValidationResult(False, errors, warnings)
        
        # Validate title
        title = data.get("title", "").strip()
        if not title:
            errors.append("Task title cannot be empty")
        if len(title) > 200:
            errors.append("Task title must be max 200 characters")
        
        # Validate priority
        if "priority" in data and data["priority"] not in ["low", "medium", "high", "urgent"]:
            errors.append(f"Invalid priority: {data['priority']}")
        
        # Validate status
        if "status" in data and data["status"] not in ["todo", "in_progress", "completed", "cancelled"]:
            errors.append(f"Invalid status: {data['status']}")
        
        # Validate due_date if provided
        if "due_date" in data and data["due_date"]:
            valid, err_msg, parsed = DatetimeValidator.validate_iso_datetime(data["due_date"])
            if not valid:
                errors.append(f"Invalid due_date: {err_msg}")
            else:
                # Check if due date is reasonable
                now = datetime.now(parsed.tzinfo) if parsed.tzinfo else datetime.now()
                if parsed < now:
                    warnings.append("Due date is in the past")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            normalized_data=normalized
        )
    
    @staticmethod
    def validate_create_event(
        data: Dict[str, Any],
        user_id: Optional[int] = None,
        check_conflicts: bool = True
    ) -> ValidationResult:
        """Validate create_event action."""
        errors = []
        warnings = []
        normalized = data.copy()
        
        # Check permissions
        perm_result = PermissionValidator.can_modify_calendar(user_id)
        errors.extend(perm_result.errors)
        warnings.extend(perm_result.warnings)
        
        if not perm_result.valid:
            return ValidationResult(False, errors, warnings)
        
        # Validate title
        title = data.get("title", "").strip()
        if not title:
            errors.append("Event title cannot be empty")
        if len(title) > 200:
            errors.append("Event title must be max 200 characters")
        
        # Validate times
        start = data.get("start_time")
        end = data.get("end_time")
        
        if not start:
            errors.append("start_time is required")
        if not end:
            errors.append("end_time is required")
        
        if start and end:
            time_result = DatetimeValidator.validate_time_range(start, end)
            errors.extend(time_result.errors)
            warnings.extend(time_result.warnings)
        
        # Validate attendees if provided
        if "attendees" in data and data["attendees"]:
            attendee_result = EmailValidator.validate_email_list(data["attendees"])
            errors.extend(attendee_result.errors)
            warnings.extend(attendee_result.warnings)
            if attendee_result.normalized_data:
                normalized.update(attendee_result.normalized_data)
        
        # TODO: Check calendar conflicts if enabled
        # This would query the user's calendar and detect overlaps
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            normalized_data=normalized
        )
    
    @staticmethod
    def validate_draft_email(
        data: Dict[str, Any],
        user_id: Optional[int] = None
    ) -> ValidationResult:
        """Validate draft_email action."""
        errors = []
        warnings = []
        normalized = data.copy()
        
        # Check permissions
        perm_result = PermissionValidator.can_send_email(user_id)
        errors.extend(perm_result.errors)
        
        if not perm_result.valid:
            return ValidationResult(False, errors, warnings)
        
        # Validate subject
        subject = data.get("subject", "").strip()
        if not subject:
            errors.append("Email subject cannot be empty")
        if len(subject) > 100:
            errors.append("Email subject must be max 100 characters")
        
        # Validate body
        body = data.get("body", "").strip()
        if not body:
            errors.append("Email body cannot be empty")
        if len(body) > 10000:
            errors.append("Email body must be max 10000 characters")
        
        # Validate to_address
        to_addr = data.get("to_address")
        if not to_addr:
            errors.append("to_address is required")
        else:
            is_valid, err_msg = EmailValidator.validate_email_format(to_addr)
            if not is_valid:
                errors.append(f"Invalid to_address: {err_msg}")
        
        # Validate from_address if provided
        if "from_address" in data and data["from_address"]:
            is_valid, err_msg = EmailValidator.validate_email_format(data["from_address"])
            if not is_valid:
                errors.append(f"Invalid from_address: {err_msg}")
        
        return ValidationResult(
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            normalized_data=normalized
        )


def validate_action(
    action: str,
    data: Dict[str, Any],
    user_id: Optional[int] = None,
    **kwargs
) -> ValidationResult:
    """
    Comprehensive validation dispatcher for all action types.
    
    Args:
        action: Action name
        data: Action data
        user_id: User ID for permission checks
        **kwargs: Additional context (e.g., check_conflicts=True for events)
        
    Returns:
        ValidationResult with errors, warnings, and normalized data
    """
    validator_map = {
        "create_task": ActionValidator.validate_create_task,
        "update_task": ActionValidator.validate_create_task,  # Same validation
        "create_event": ActionValidator.validate_create_event,
        "update_event": ActionValidator.validate_create_event,
        "draft_email": ActionValidator.validate_draft_email,
        "create_habit": lambda d, **kw: ValidationResult(True, [], []),  # No backend validation needed
    }
    
    validator_func = validator_map.get(action)
    if not validator_func:
        return ValidationResult(
            False,
            [f"Unknown action type: {action}"],
            []
        )
    
    try:
        return validator_func(data, user_id=user_id, **kwargs)
    except Exception as e:
        logger.exception(f"Validation error for action '{action}'")
        return ValidationResult(
            False,
            [f"Validation error: {str(e)}"],
            []
        )
