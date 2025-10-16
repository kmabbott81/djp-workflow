"""AI Orchestrator with permissions guards + job tracking - Sprint 58 Slice 6.

Manages action plan execution with role-based permission filtering and job lifecycle tracking.
"""

from typing import Any, Optional
from uuid import uuid4

from src.ai.job_store import JobStore, get_job_store
from src.schemas.ai_plan import PlanResult
from src.schemas.permissions import RBACRegistry, default_rbac


class AIOrchestrator:
    """Orchestrator for AI-planned action execution with RBAC + job tracking."""

    def __init__(self, rbac: Optional[RBACRegistry] = None, job_store: Optional[JobStore] = None):
        """Initialize orchestrator with optional RBAC registry and job store.

        Args:
            rbac: RBAC registry (defaults to built-in roles if None)
            job_store: Job store (defaults to global singleton if None; useful for testing)
        """
        self.rbac = rbac or default_rbac()
        self.job_store = job_store or get_job_store()

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
        """Generate and guard action plan with job correlation ID.

        Args:
            user_id: User UUID
            prompt: Natural language prompt
            planner: ActionPlanner instance
            context: Optional execution context

        Returns:
            Filtered plan respecting user permissions (includes plan_id for correlation)
        """
        # Assign correlation ID for job tracking (internal; no API change)
        plan_id = str(uuid4())

        # Generate plan
        plan = await planner.plan(prompt, context)

        # Guard: filter disallowed steps
        guarded_plan = self._guard_plan_steps(user_id, plan)

        # Stash plan_id on plan for downstream job tracking
        guarded_plan._plan_id = plan_id  # type: ignore

        return guarded_plan

    async def execute_plan(
        self,
        user_id: str,
        plan: PlanResult,
        executor: Any,  # src.actions.execution.ActionExecutor
        workspace_id: str = "default",
    ) -> dict[str, Any]:
        """Execute plan with pre-execute permission re-check + job tracking.

        Args:
            user_id: User UUID
            plan: Action plan (should be pre-guarded)
            executor: ActionExecutor instance
            workspace_id: Workspace UUID

        Returns:
            Execution results per step with job IDs
        """
        # Re-guard: final permission check before execute
        guarded_plan = self._guard_plan_steps(user_id, plan)

        # Retrieve plan_id from plan (set in plan() method)
        plan_id = getattr(plan, "_plan_id", str(uuid4()))

        # Check if plan is empty after filtering
        if not guarded_plan.steps:
            return {
                "success": False,
                "error": "No executable actions: all steps filtered by permissions",
                "steps_executed": 0,
                "steps_denied": len(plan.steps),
                "plan_id": plan_id,
            }

        # Execute guarded steps with job tracking
        results = []
        for idx, step in enumerate(guarded_plan.steps):
            # Create job record for this step
            job = await self.job_store.create(
                user_id=user_id,
                action_id=step.action_id,
                plan_id=plan_id,
            )

            try:
                # Mark job as running
                await self.job_store.start(job.job_id)

                # Execute step
                preview = executor.preview(step.action_id, step.params)
                result = await executor.execute(
                    preview_id=preview.preview_id,
                    workspace_id=workspace_id,
                    actor_id=user_id,
                )

                # Mark job as success (result should be pre-redacted by executor)
                # Store result only if it's a dict; otherwise skip (will be redacted at API layer)
                result_data = result if isinstance(result, dict) else None
                await self.job_store.finish_ok(job.job_id, result=result_data)

                results.append(
                    {
                        "step_index": idx,
                        "action_id": step.action_id,
                        "job_id": job.job_id,
                        "status": result.status.value if hasattr(result, "status") else "success",
                        "result": result.result if hasattr(result, "result") else result,
                    }
                )
            except Exception as e:
                # Mark job as failed (error message should be redacted if it contains PII)
                error_msg = str(e)
                await self.job_store.finish_err(job.job_id, error=error_msg)

                results.append(
                    {
                        "step_index": idx,
                        "action_id": step.action_id,
                        "job_id": job.job_id,
                        "status": "failed",
                        "error": error_msg,
                    }
                )

        return {
            "success": True,
            "steps_executed": len(results),
            "results": results,
            "plan_id": plan_id,
        }


# Global orchestrator instance
_orchestrator: Optional[AIOrchestrator] = None


def get_orchestrator(rbac: Optional[RBACRegistry] = None) -> AIOrchestrator:
    """Get or create global orchestrator instance."""
    global _orchestrator
    if _orchestrator is None:
        _orchestrator = AIOrchestrator(rbac)
    return _orchestrator
