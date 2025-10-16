"""AI Orchestrator with permissions guards - Sprint 58 Slice 5.

Manages action plan execution with role-based permission filtering.
"""

from typing import Any, Optional

from src.schemas.ai_plan import PlanResult
from src.schemas.permissions import RBACRegistry, default_rbac


class AIOrchestrator:
    """Orchestrator for AI-planned action execution with RBAC."""

    def __init__(self, rbac: Optional[RBACRegistry] = None):
        """Initialize orchestrator with optional RBAC registry.

        Args:
            rbac: RBAC registry (defaults to built-in roles if None)
        """
        self.rbac = rbac or default_rbac()

    def _guard_plan_steps(self, user_id: str, plan: PlanResult) -> PlanResult:
        """Filter plan steps based on user permissions.

        Removes disallowed actions and returns filtered plan.
        If all steps are filtered, returns empty plan with explanation.

        Args:
            user_id: User UUID
            plan: Original plan from AI planner

        Returns:
            Filtered plan with only allowed actions
        """
        # Get user permissions
        user_perms = self.rbac.get_user_permissions(user_id)

        # Filter steps
        allowed_steps = [step for step in plan.steps if user_perms.can_execute(step.action_id)]

        # Return filtered plan (or original if all allowed)
        if len(allowed_steps) == len(plan.steps):
            return plan

        # Create new plan with allowed steps only
        return PlanResult(
            prompt=plan.prompt,
            intent=plan.intent,
            steps=allowed_steps,
            confidence=plan.confidence * (len(allowed_steps) / len(plan.steps)) if plan.steps else 0.0,
            explanation=f"{plan.explanation} (filtered by permissions: {len(plan.steps) - len(allowed_steps)} steps removed)",
        )

    async def plan(
        self,
        user_id: str,
        prompt: str,
        planner: Any,  # src.ai.planner.ActionPlanner
        context: Optional[dict[str, Any]] = None,
    ) -> PlanResult:
        """Generate and guard action plan.

        Args:
            user_id: User UUID
            prompt: Natural language prompt
            planner: ActionPlanner instance
            context: Optional execution context

        Returns:
            Filtered plan respecting user permissions
        """
        # Generate plan
        plan = await planner.plan(prompt, context)

        # Guard: filter disallowed steps
        guarded_plan = self._guard_plan_steps(user_id, plan)

        return guarded_plan

    async def execute_plan(
        self,
        user_id: str,
        plan: PlanResult,
        executor: Any,  # src.actions.execution.ActionExecutor
        workspace_id: str = "default",
    ) -> dict[str, Any]:
        """Execute plan with pre-execute permission re-check.

        Args:
            user_id: User UUID
            plan: Action plan (should be pre-guarded)
            executor: ActionExecutor instance
            workspace_id: Workspace UUID

        Returns:
            Execution results per step
        """
        # Re-guard: final permission check before execute
        guarded_plan = self._guard_plan_steps(user_id, plan)

        # Check if plan is empty after filtering
        if not guarded_plan.steps:
            return {
                "success": False,
                "error": "No executable actions: all steps filtered by permissions",
                "steps_executed": 0,
                "steps_denied": len(plan.steps),
            }

        # Execute guarded steps
        results = []
        for step in guarded_plan.steps:
            try:
                preview = executor.preview(step.action_id, step.params)
                result = await executor.execute(
                    preview_id=preview.preview_id,
                    workspace_id=workspace_id,
                    actor_id=user_id,
                )
                results.append(
                    {
                        "step_index": guarded_plan.steps.index(step),
                        "action_id": step.action_id,
                        "status": result.status.value,
                        "result": result.result,
                        "error": result.error,
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "step_index": guarded_plan.steps.index(step),
                        "action_id": step.action_id,
                        "status": "failed",
                        "error": str(e),
                    }
                )

        return {
            "success": True,
            "steps_executed": len(results),
            "results": results,
        }


# Global orchestrator instance
_orchestrator: Optional[AIOrchestrator] = None


def get_orchestrator(rbac: Optional[RBACRegistry] = None) -> AIOrchestrator:
    """Get or create global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AIOrchestrator(rbac)
    return _orchestrator
