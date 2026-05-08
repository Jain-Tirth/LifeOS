"""
Integrated execution handler - ties all production components together.

This module orchestrates:
1. Planner Agent → generates structured intent
2. Execution Agent → converts to tool calls
3. Execution Layer → validates and retries
4. Validation Layer → enforces business rules
5. Tool Executor → applies actions

Usage:
    handler = ExecutionHandler(user_id=123, session_id="session_456")
    result = await handler.handle(raw_agent_response, planning_context)
"""
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from .execution_layer import (
    get_execution_orchestrator,
    ExecutionResult,
)
from .action_models import Action

logger = logging.getLogger(__name__)


@dataclass
class ExecutionContext:
    """Context for execution."""
    user_id: Optional[int] = None
    session_id: str = "default"
    check_calendar_conflicts: bool = True
    check_email_deliverability: bool = True
    auto_retry: bool = True
    log_metrics: bool = True


class ExecutionHandler:
    """
    High-level execution handler that coordinates all layers.
    
    This is the recommended entry point for executing agent outputs.
    """
    
    def __init__(self, context: Optional[ExecutionContext] = None):
        """Initialize handler with execution context."""
        self.context = context or ExecutionContext()
        self.orchestrator = get_execution_orchestrator()
    
    async def handle(
        self,
        raw_response: str,
        planning_context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Handle raw execution agent response end-to-end.
        
        Args:
            raw_response: Raw text from execution agent
            planning_context: Context from planning phase (optional constraints, goals)
            
        Returns:
            ExecutionResult with validated actions or errors
        """
        logger.info(
            f"Handling execution for user={self.context.user_id}, "
            f"session={self.context.session_id}"
        )
        
        # Build validation context
        validation_context = {
            "check_conflicts": self.context.check_calendar_conflicts,
        }
        
        if planning_context:
            validation_context.update(planning_context)
        
        # Execute with retry and validation
        result = await self.orchestrator.execute_agent_response(
            session_id=self.context.session_id,
            raw_response=raw_response,
            user_id=self.context.user_id,
            validation_context=validation_context,
        )
        
        # Log results if enabled
        if self.context.log_metrics:
            self._log_detailed_results(result)
        
        return result
    
    def _log_detailed_results(self, result: ExecutionResult) -> None:
        """Log detailed execution results."""
        logger.info(f"Execution result: {result.success}")
        
        if result.actions:
            logger.info(f"Valid actions: {len(result.actions)}")
            for action in result.actions:
                logger.info(f"  - {action.action}")
        
        if result.errors:
            logger.error(f"Execution errors ({len(result.errors)}):")
            for error in result.errors:
                logger.error(f"  - {error}")
        
        if result.warnings:
            logger.warning(f"Execution warnings ({len(result.warnings)}):")
            for warning in result.warnings:
                logger.warning(f"  - {warning}")
        
        # Log metrics
        m = result.metrics
        logger.info(
            f"Metrics: "
            f"parse_attempts={m.parse_attempts}, "
            f"parse_failures={m.parse_failures}, "
            f"actions_valid={m.actions_valid}/{m.actions_requested}, "
            f"retries={m.total_retries}"
        )


class ToolExecutor:
    """
    Executes validated actions against external services.
    
    This is a placeholder for the actual tool execution logic that would
    interact with:
    - Task database
    - Google Calendar API
    - Email service
    - Habit tracker
    """
    
    def __init__(self, user_id: Optional[int] = None):
        self.user_id = user_id
    
    async def execute_actions(self, actions: List[Action]) -> Dict[str, Any]:
        """
        Execute all validated actions.
        
        Args:
            actions: List of validated Action objects
            
        Returns:
            Results from each action execution
        """
        results = {
            "total": len(actions),
            "successful": 0,
            "failed": 0,
            "details": [],
        }
        
        for action in actions:
            try:
                result = await self._execute_single_action(action)
                results["successful"] += 1
                results["details"].append(result)
            except Exception as e:
                logger.error(f"Failed to execute action '{action.action}': {str(e)}")
                results["failed"] += 1
                results["details"].append({
                    "action": action.action,
                    "error": str(e),
                })
        
        return results
    
    async def _execute_single_action(self, action: Action) -> Dict[str, Any]:
        """Execute a single action against its corresponding service."""
        action_type = action.action
        
        if action_type == "create_task":
            return await self._execute_create_task(action.data)
        elif action_type == "update_task":
            return await self._execute_update_task(action.data)
        elif action_type == "create_event":
            return await self._execute_create_event(action.data)
        elif action_type == "update_event":
            return await self._execute_update_event(action.data)
        elif action_type == "draft_email":
            return await self._execute_draft_email(action.data)
        elif action_type == "create_habit":
            return await self._execute_create_habit(action.data)
        else:
            raise ValueError(f"Unknown action type: {action_type}")
    
    async def _execute_create_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute create_task action."""
        # TODO: Implement actual task creation
        logger.info(f"[STUB] Creating task: {data.get('title')}")
        return {
            "action": "create_task",
            "status": "stub",
            "message": "Task creation not yet implemented"
        }
    
    async def _execute_update_task(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute update_task action."""
        logger.info(f"[STUB] Updating task: {data.get('title')}")
        return {
            "action": "update_task",
            "status": "stub",
        }
    
    async def _execute_create_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute create_event action."""
        logger.info(f"[STUB] Creating event: {data.get('title')}")
        return {
            "action": "create_event",
            "status": "stub",
        }
    
    async def _execute_update_event(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute update_event action."""
        logger.info(f"[STUB] Updating event: {data.get('title')}")
        return {
            "action": "update_event",
            "status": "stub",
        }
    
    async def _execute_draft_email(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute draft_email action."""
        logger.info(f"[STUB] Drafting email to: {data.get('to_address')}")
        return {
            "action": "draft_email",
            "status": "stub",
        }
    
    async def _execute_create_habit(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute create_habit action."""
        logger.info(f"[STUB] Creating habit: {data.get('name')}")
        return {
            "action": "create_habit",
            "status": "stub",
        }


async def execute_agent_response_end_to_end(
    raw_response: str,
    user_id: Optional[int] = None,
    session_id: str = "default",
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Complete end-to-end execution flow.
    
    Flow:
    1. Parse & validate LLM output → typed actions
    2. Enforce business rules → normalized actions
    3. Execute against services → results
    
    Args:
        raw_response: Raw text from execution agent
        user_id: User ID
        session_id: Session identifier
        context: Additional context (planning goals, constraints)
        
    Returns:
        Complete execution result including tool execution
    """
    # Step 1: Parse and validate with execution layer
    exec_context = ExecutionContext(
        user_id=user_id,
        session_id=session_id,
    )
    handler = ExecutionHandler(exec_context)
    execution_result = await handler.handle(raw_response, context)
    
    # Step 2: Execute actions if validation succeeded
    tool_results = {}
    if execution_result.success and execution_result.actions:
        executor = ToolExecutor(user_id=user_id)
        tool_results = await executor.execute_actions(execution_result.actions)
    
    # Step 3: Return comprehensive result
    return {
        "execution_successful": execution_result.success,
        "actions_validated": execution_result.metrics.actions_valid,
        "actions_requested": execution_result.metrics.actions_requested,
        "valid_actions": [a.dict() for a in execution_result.actions],
        "validation_errors": execution_result.errors,
        "validation_warnings": execution_result.warnings,
        "tool_execution_results": tool_results,
        "metrics": execution_result.metrics.to_dict(),
    }


__all__ = [
    "ExecutionContext",
    "ExecutionHandler",
    "ToolExecutor",
    "execute_agent_response_end_to_end",
]
