"""
DAG Runner - Executes tasks in topological order with retries and event logging.
"""

import json
from datetime import datetime
from pathlib import Path

from .graph import DAG, merge_payloads, toposort, validate


class RunnerError(Exception):
    """Raised when DAG execution fails."""

    pass


def log_event(event: dict, events_path: str) -> None:
    """Log event to JSONL file."""
    Path(events_path).parent.mkdir(parents=True, exist_ok=True)
    with open(events_path, "a", encoding="utf-8") as f:
        f.write(json.dumps(event) + "\n")


def run_dag(
    dag: DAG,
    *,
    tenant: str = "local-dev",
    dry_run: bool = False,
    max_retries_default: int = 0,
    events_path: str = "logs/orchestrator_events.jsonl",
) -> dict:
    """
    Execute a DAG with retry support and event logging.

    Args:
        dag: DAG to execute
        tenant: Tenant ID
        dry_run: If True, print plan without executing
        max_retries_default: Default max retries per task
        events_path: Path to write events

    Returns:
        Dict with execution results

    Raises:
        RunnerError: If execution fails
    """
    # Validate DAG
    try:
        validate(dag)
    except Exception as e:
        raise RunnerError(f"DAG validation failed: {e}") from e

    # Get execution order
    try:
        ordered_tasks = toposort(dag)
    except Exception as e:
        raise RunnerError(f"Failed to sort DAG: {e}") from e

    if dry_run:
        print("=" * 60)
        print(f"DRY RUN: DAG '{dag.name}'")
        print("=" * 60)
        print(f"Tenant: {tenant}")
        print(f"Tasks: {len(ordered_tasks)}")
        print("\nExecution Plan:")
        for i, task in enumerate(ordered_tasks, 1):
            deps = ", ".join(task.depends_on) if task.depends_on else "none"
            print(f"  {i}. {task.id} (workflow: {task.workflow_ref}, depends_on: {deps})")
        print("=" * 60)
        return {"dry_run": True, "tasks_planned": len(ordered_tasks)}

    # Execute tasks
    start_time = datetime.utcnow()
    task_outputs = {}
    tasks_succeeded = 0
    tasks_failed = 0

    log_event(
        {
            "timestamp": start_time.isoformat(),
            "event": "dag_start",
            "dag_name": dag.name,
            "tenant": tenant,
            "task_count": len(ordered_tasks),
        },
        events_path,
    )

    for task in ordered_tasks:
        task_start = datetime.utcnow()

        log_event(
            {
                "timestamp": task_start.isoformat(),
                "event": "task_start",
                "dag_name": dag.name,
                "task_id": task.id,
                "workflow_ref": task.workflow_ref,
            },
            events_path,
        )

        # Merge upstream outputs into params
        upstream_outputs = {dep_id: task_outputs.get(dep_id, {}) for dep_id in task.depends_on}
        merged_params = {**task.params, **merge_payloads(upstream_outputs)}

        # Get workflow function
        try:
            from src.workflows.adapter import WORKFLOW_MAP

            workflow_fn = WORKFLOW_MAP.get(task.workflow_ref)
            if not workflow_fn:
                raise RunnerError(f"Unknown workflow: {task.workflow_ref}")
        except ImportError as e:
            raise RunnerError(f"Failed to import workflow adapter: {e}") from e

        # Execute with retries
        max_retries = task.retries if task.retries > 0 else max_retries_default

        for attempt in range(max_retries + 1):
            try:
                output = workflow_fn(merged_params)
                task_outputs[task.id] = output or {}

                log_event(
                    {
                        "timestamp": datetime.utcnow().isoformat(),
                        "event": "task_ok",
                        "dag_name": dag.name,
                        "task_id": task.id,
                        "attempt": attempt + 1,
                    },
                    events_path,
                )

                tasks_succeeded += 1
                break
            except Exception as e:
                if attempt < max_retries:
                    log_event(
                        {
                            "timestamp": datetime.utcnow().isoformat(),
                            "event": "task_retry",
                            "dag_name": dag.name,
                            "task_id": task.id,
                            "attempt": attempt + 1,
                            "error": str(e),
                        },
                        events_path,
                    )
                else:
                    log_event(
                        {
                            "timestamp": datetime.utcnow().isoformat(),
                            "event": "task_fail",
                            "dag_name": dag.name,
                            "task_id": task.id,
                            "error": str(e),
                        },
                        events_path,
                    )
                    tasks_failed += 1
                    raise RunnerError(f"Task '{task.id}' failed after {max_retries + 1} attempts: {e}") from e

    end_time = datetime.utcnow()
    duration = (end_time - start_time).total_seconds()

    log_event(
        {
            "timestamp": end_time.isoformat(),
            "event": "dag_done",
            "dag_name": dag.name,
            "tenant": tenant,
            "tasks_succeeded": tasks_succeeded,
            "tasks_failed": tasks_failed,
            "duration_seconds": duration,
        },
        events_path,
    )

    return {
        "dag_name": dag.name,
        "tasks_succeeded": tasks_succeeded,
        "tasks_failed": tasks_failed,
        "duration_seconds": duration,
        "task_outputs": task_outputs,
    }
