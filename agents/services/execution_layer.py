"""
Enhanced execution layer with retry logic, observability, and error handling.

This layer wraps the execution agent with:
- Automatic JSON parsing and validation retry
- Structured logging
- Invalid output tracking
- Retry metrics
- Tool usage metrics
"""
import json
import logging
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass, field, asdict
from datetime import datetime
import asyncio

from .action_models import AgentResponse, Action, parse_agent_response
from .validation_layer import validate_action, ValidationResult

logger = logging.getLogger(__name__)


@dataclass
class ExecutionMetrics:
    """Metrics for execution session."""
    session_id: str
    agent_name: str
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Parsing metrics
    parse_attempts: int = 0
    parse_failures: int = 0
    json_parse_errors: List[str] = field(default_factory=list)
    validation_errors: List[str] = field(default_factory=list)
    
    # Action metrics
    actions_requested: int = 0
    actions_valid: int = 0
    actions_invalid: int = 0
    actions_executed: int = 0
    
    # Retry metrics
    total_retries: int = 0
    successful_after_retry: int = 0
    
    # Validation metrics
    validation_warnings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for logging."""
        data = asdict(self)
        data["timestamp"] = data["timestamp"].isoformat()
        return data


@dataclass
class ExecutionResult:
    """Result of execution attempt."""
    success: bool
    actions: List[Action]
    metrics: ExecutionMetrics
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    raw_response: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "success": self.success,
            "actions": [a.dict() for a in self.actions],
            "metrics": self.metrics.to_dict(),
            "errors": self.errors,
            "warnings": self.warnings,
        }


class ExecutionLayer:
    """
    Deterministic execution layer that wraps the Groq execution agent.
    
    Responsibilities:
    - Parse and validate LLM output
    - Retry on invalid JSON
    - Track metrics
    - Enforce schema constraints
    - Separate business logic validation
    """
    
    MAX_RETRIES = 3
    RETRY_DELAY = 0.5  # seconds
    
    def __init__(self, session_id: str = "default", agent_name: str = "ExecutionAgent"):
        self.session_id = session_id
        self.agent_name = agent_name
        self.metrics = ExecutionMetrics(session_id=session_id, agent_name=agent_name)
    
    async def execute_with_retry(
        self,
        raw_response: str,
        user_id: Optional[int] = None,
        validation_context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Parse, validate, and execute agent response with retry logic.
        
        Args:
            raw_response: Raw text from LLM execution agent
            user_id: User ID for permission checks
            validation_context: Additional context for validation
            
        Returns:
            ExecutionResult with actions or errors
        """
        self.metrics.raw_response = raw_response
        
        # Attempt to parse with retries
        agent_response = await self._parse_with_retry(raw_response)
        
        if agent_response is None:
            return ExecutionResult(
                success=False,
                actions=[],
                metrics=self.metrics,
                errors=self.metrics.json_parse_errors,
            )
        
        # Validate each action
        validated_actions = []
        validation_warnings = []
        action_errors = []
        
        for action in agent_response.actions:
            self.metrics.actions_requested += 1
            
            # Schema validation (already done by parse_agent_response)
            # Now do backend business logic validation
            validation_result = validate_action(
                action.action,
                action.data,
                user_id=user_id,
                **(validation_context or {})
            )
            
            if not validation_result.valid:
                self.metrics.actions_invalid += 1
                action_errors.extend(validation_result.errors)
                logger.warning(
                    f"Action '{action.action}' failed validation: {validation_result.errors}"
                )
                continue
            
            self.metrics.actions_valid += 1
            validation_warnings.extend(validation_result.warnings)
            
            # Update action data with normalized values if provided
            if validation_result.normalized_data:
                action.data.update(validation_result.normalized_data)
            
            validated_actions.append(action)
        
        self.metrics.validation_warnings.extend(validation_warnings)
        
        # Determine overall success
        success = len(validated_actions) > 0 and len(action_errors) == 0
        
        return ExecutionResult(
            success=success,
            actions=validated_actions,
            metrics=self.metrics,
            errors=action_errors,
            warnings=validation_warnings,
            raw_response=raw_response,
        )
    
    async def _parse_with_retry(self, raw_response: str) -> Optional[AgentResponse]:
        """
        Attempt to parse response as JSON with retry logic.
        
        Returns:
            Parsed AgentResponse or None if parsing failed
        """
        for attempt in range(self.MAX_RETRIES):
            self.metrics.parse_attempts += 1
            
            try:
                agent_response = parse_agent_response(raw_response)
                logger.info(
                    f"Successfully parsed agent response (attempt {attempt + 1}): "
                    f"{len(agent_response.actions)} actions"
                )
                return agent_response
            
            except ValueError as e:
                error_msg = str(e)
                logger.warning(
                    f"Parse attempt {attempt + 1} failed: {error_msg}"
                )
                self.metrics.parse_failures += 1
                self.metrics.json_parse_errors.append(error_msg)
                
                # Wait before retry (except on last attempt)
                if attempt < self.MAX_RETRIES - 1:
                    self.metrics.total_retries += 1
                    await asyncio.sleep(self.RETRY_DELAY)
            
            except Exception as e:
                error_msg = f"Unexpected parse error: {str(e)}"
                logger.error(error_msg)
                self.metrics.json_parse_errors.append(error_msg)
                break
        
        logger.error(
            f"Failed to parse response after {self.MAX_RETRIES} attempts"
        )
        return None
    
    def log_execution(self, result: ExecutionResult) -> None:
        """Log execution details for observability."""
        logger.info(
            f"Execution complete - "
            f"success={result.success}, "
            f"actions={result.metrics.actions_valid}/{result.metrics.actions_requested}, "
            f"warnings={len(result.warnings)}, "
            f"retries={result.metrics.total_retries}"
        )
        
        if result.errors:
            logger.error(f"Execution errors: {result.errors}")
        
        if result.warnings:
            logger.warning(f"Execution warnings: {result.warnings}")
        
        # Log metrics
        logger.debug(f"Execution metrics: {result.metrics.to_dict()}")


class ExecutionOrchestrator:
    """
    Orchestrates the complete flow from planning through execution.
    
    Flow:
    Planning Agent → Structured Intent
    → Execution Agent → Raw JSON Response
    → Execution Layer → Typed Actions
    → Validation Layer → Normalized Actions
    → Tool Executor → Results
    """
    
    def __init__(self):
        self.execution_layers: Dict[str, ExecutionLayer] = {}
    
    def get_execution_layer(self, session_id: str) -> ExecutionLayer:
        """Get or create execution layer for session."""
        if session_id not in self.execution_layers:
            self.execution_layers[session_id] = ExecutionLayer(
                session_id=session_id,
                agent_name="ExecutionAgent"
            )
        return self.execution_layers[session_id]
    
    async def execute_agent_response(
        self,
        session_id: str,
        raw_response: str,
        user_id: Optional[int] = None,
        validation_context: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Execute the complete workflow from raw response to validated actions.
        
        Args:
            session_id: Session identifier
            raw_response: Raw text from execution agent
            user_id: User ID for permission checks
            validation_context: Additional validation context
            
        Returns:
            ExecutionResult with validated actions or errors
        """
        execution_layer = self.get_execution_layer(session_id)
        
        logger.info(
            f"Starting execution for session {session_id}, "
            f"response_length={len(raw_response)}"
        )
        
        # Execute with retry and validation
        result = await execution_layer.execute_with_retry(
            raw_response,
            user_id=user_id,
            validation_context=validation_context,
        )
        
        # Log execution
        execution_layer.log_execution(result)
        
        return result
    
    def get_session_metrics(self, session_id: str) -> Optional[ExecutionMetrics]:
        """Get metrics for a session."""
        layer = self.execution_layers.get(session_id)
        return layer.metrics if layer else None


# Global orchestrator instance
_ORCHESTRATOR: Optional[ExecutionOrchestrator] = None


def get_execution_orchestrator() -> ExecutionOrchestrator:
    """Get or create the global execution orchestrator."""
    global _ORCHESTRATOR
    if _ORCHESTRATOR is None:
        _ORCHESTRATOR = ExecutionOrchestrator()
    return _ORCHESTRATOR
