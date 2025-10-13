"""AI Orchestrator v0.1 Plan Schemas.

Strict JSON schemas for AI planning with cost control and validation.
"""

from typing import Any, Optional

from pydantic import BaseModel, Field


class PlannedAction(BaseModel):
    """Single action in execution plan."""

    provider: str = Field(..., description="Provider name (e.g., google, microsoft)")
    action: str = Field(..., description="Action ID (e.g., gmail.send, outlook.send)")
    params: dict[str, Any] = Field(..., description="Action parameters matching adapter schema")
    client_request_id: Optional[str] = Field(None, description="Idempotency key for execution")


class PlanResult(BaseModel):
    """Complete action plan from AI planner."""

    intent: str = Field(..., description="Extracted user intent")
    confidence: float = Field(..., description="Confidence score (0.0-1.0)", ge=0.0, le=1.0)
    actions: list[PlannedAction] = Field(..., description="Ordered list of actions to execute")
    notes: Optional[str] = Field(None, description="Additional notes or warnings")
