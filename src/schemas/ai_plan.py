"""AI Action Plan Schemas - Sprint 58 Slice 5 Foundations.

Pydantic schemas for AI action planning with strict validation.
These schemas define the structure for:
- Natural language → structured action plans (PlannedAction, PlanResult)
- Action execution results and dependency tracking
- Multi-step workflow orchestration

Sprint 58 Foundations: Extracted from src.ai.planner for reusability and testing.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field, field_validator


class PlannedAction(BaseModel):
    """Single action in a multi-step plan.

    Represents one atomic step in an AI-generated action plan.
    Actions can depend on previous actions via depends_on indices.

    Example:
        action = PlannedAction(
            action_id="gmail.send",
            description="Send thank you email to John",
            params={"to": "john@example.com", "subject": "Thank you"},
            depends_on=None
        )
    """

    action_id: str = Field(
        ..., description="Action identifier (e.g., 'gmail.send', 'calendar.create_event')", min_length=1
    )
    description: str = Field(..., description="Human-readable explanation of what this action does", min_length=1)
    params: dict[str, Any] = Field(..., description="Action parameters extracted from user prompt")
    depends_on: Optional[list[int]] = Field(None, description="List of step indices this action depends on (0-indexed)")

    @field_validator("action_id")
    @classmethod
    def validate_action_id_format(cls, v: str) -> str:
        """Validate action_id follows 'provider.action' format."""
        if "." not in v:
            raise ValueError(f"action_id must follow 'provider.action' format, got: {v}")
        parts = v.split(".")
        if len(parts) != 2:
            raise ValueError(f"action_id must have exactly one dot separator, got: {v}")
        if not all(part.isidentifier() or "_" in part for part in parts):
            raise ValueError(f"action_id parts must be valid identifiers, got: {v}")
        return v

    @field_validator("depends_on")
    @classmethod
    def validate_depends_on(cls, v: Optional[list[int]]) -> Optional[list[int]]:
        """Validate depends_on indices are non-negative."""
        if v is not None:
            if any(idx < 0 for idx in v):
                raise ValueError("depends_on indices must be non-negative")
        return v


class PlanResult(BaseModel):
    """Structured plan generated from natural language prompt.

    The complete output of the AI planner, including:
    - Original prompt and extracted intent
    - Ordered list of actions to execute
    - Confidence score and explanation

    Example:
        plan = PlanResult(
            prompt="Send thank you email to John",
            intent="send_email",
            steps=[PlannedAction(...)],
            confidence=0.95,
            explanation="Clear request with all required info"
        )
    """

    prompt: str = Field(..., description="Original user prompt", min_length=1)
    intent: str = Field(..., description="Extracted intent (e.g., 'send_email_and_schedule')", min_length=1)
    steps: list[PlannedAction] = Field(..., description="Ordered action steps to execute")
    confidence: float = Field(..., description="Confidence in plan accuracy (0.0-1.0)", ge=0.0, le=1.0)
    explanation: str = Field(..., description="Why the AI chose this plan", min_length=1)

    @field_validator("steps")
    @classmethod
    def validate_steps_dependencies(cls, v: list[PlannedAction]) -> list[PlannedAction]:
        """Validate that all depends_on indices are valid."""
        for i, step in enumerate(v):
            if step.depends_on:
                for dep_idx in step.depends_on:
                    if dep_idx >= i:
                        raise ValueError(
                            f"Step {i} depends on step {dep_idx}, but dependencies must reference earlier steps"
                        )
                    if dep_idx >= len(v):
                        raise ValueError(f"Step {i} depends on step {dep_idx}, but only {len(v)} steps exist")
        return v


# Legacy aliases for backward compatibility with src.ai.planner
ActionStep = PlannedAction
ActionPlan = PlanResult
