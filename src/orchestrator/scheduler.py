"""
Lightweight Scheduler for Sprint 27B

Cron-like scheduler for DAG execution with YAML config and JSONL state tracking.
Single-process, simple, and testable.
"""

import argparse
import os
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from .graph import DAG, Task
from .runner import run_dag
from .state_store import record_event


def parse_cron(expr: str) -> callable:
    """
    Parse minimal cron expression and return matcher function.

    Supports:
    - */n for every n minutes (*/5 = every 5 minutes)
    - * for any value

    Args:
        expr: Cron expression (minute hour day month weekday format)

    Returns:
        Function that takes datetime and returns bool

    Example:
        >>> matcher = parse_cron("*/5 * * * *")
        >>> matcher(datetime(2025, 10, 3, 14, 5))  # minute % 5 == 0
        True
    """
    parts = expr.split()
    if len(parts) != 5:
        raise ValueError(f"Invalid cron expression: {expr} (expected 5 fields)")

    minute, hour, day, month, weekday = parts

    def matches(now: datetime) -> bool:
        # Minute field
        if minute.startswith("*/"):
            interval = int(minute[2:])
            if now.minute % interval != 0:
                return False
        elif minute != "*":
            if now.minute != int(minute):
                return False

        # Hour field
        if hour != "*":
            if now.hour != int(hour):
                return False

        # Day field
        if day != "*":
            if now.day != int(day):
                return False

        # Month field
        if month != "*":
            if now.month != int(month):
                return False

        # Weekday field (0=Monday, 6=Sunday)
        if weekday != "*":
            if now.weekday() != int(weekday):
                return False

        return True

    return matches


def load_schedules(schedules_dir: str) -> list[dict[str, Any]]:
    """
    Load all schedule YAML files from a directory.

    Args:
        schedules_dir: Path to schedules directory

    Returns:
        List of schedule configuration dictionaries
    """
    schedules = []
    schedules_path = Path(schedules_dir)

    if not schedules_path.exists():
        return []

    for yaml_file in schedules_path.glob("*.yaml"):
        try:
            with open(yaml_file, encoding="utf-8") as f:
                config = yaml.safe_load(f)
                if isinstance(config, list):
                    schedules.extend(config)
                elif isinstance(config, dict):
                    schedules.append(config)
        except Exception as e:
            print(f"Warning: Failed to load {yaml_file}: {e}")

    return schedules


def load_dag_from_yaml(path: str) -> DAG:
    """Load DAG from YAML file."""
    with open(path, encoding="utf-8") as f:
        config = yaml.safe_load(f)

    tasks = [
        Task(
            id=t["id"],
            workflow_ref=t["workflow_ref"],
            params=t.get("params", {}),
            depends_on=t.get("depends_on", []),
            retries=t.get("retries", 0),
        )
        for t in config.get("tasks", [])
    ]

    return DAG(name=config["name"], tasks=tasks)


def tick_once(now: datetime, schedules: list[dict[str, Any]], run_queue: list[dict[str, Any]]) -> None:
    """
    Process one scheduler tick.

    Enqueues runs for any schedules matching the current time.
    De-duplicates by {schedule_id, minute} to prevent double-enqueue.

    Args:
        now: Current datetime
        schedules: List of schedule configurations
        run_queue: Queue to append runs to (mutated)
    """
    current_minute = now.strftime("%Y-%m-%d %H:%M")
    enqueued_keys = {(r["schedule_id"], r["minute"]) for r in run_queue}

    for schedule in schedules:
        if not schedule.get("enabled", True):
            continue

        schedule_id = schedule["id"]
        cron_expr = schedule["cron"]

        try:
            matcher = parse_cron(cron_expr)
            if matcher(now):
                key = (schedule_id, current_minute)
                if key not in enqueued_keys:
                    run = {
                        "schedule_id": schedule_id,
                        "dag_path": schedule["dag"],
                        "tenant": schedule.get("tenant", "local-dev"),
                        "minute": current_minute,
                        "enqueued_at": now.isoformat(),
                    }
                    run_queue.append(run)
                    enqueued_keys.add(key)

                    record_event(
                        {
                            "event": "schedule_enqueued",
                            "schedule_id": schedule_id,
                            "dag_path": schedule["dag"],
                            "tenant": run["tenant"],
                            "minute": current_minute,
                        }
                    )

        except Exception as e:
            print(f"Warning: Failed to process schedule {schedule_id}: {e}")


def drain_queue(run_queue: list[dict[str, Any]], max_parallel: int = 3) -> list[dict[str, Any]]:
    """
    Drain the run queue by executing enqueued DAG runs.

    Launches up to max_parallel concurrent runs using ThreadPoolExecutor.
    Records run_started and run_finished events to state store.

    Args:
        run_queue: List of run dictionaries (will be cleared)
        max_parallel: Maximum concurrent runs

    Returns:
        List of run results
    """
    if not run_queue:
        return []

    results = []
    runs_to_execute = run_queue[:]
    run_queue.clear()

    events_path = os.getenv("ORCH_EVENTS_PATH", "logs/orchestrator_events.jsonl")

    def execute_run(run: dict[str, Any]) -> dict[str, Any]:
        """Execute a single DAG run."""
        start_time = datetime.now(UTC)

        record_event(
            {
                "event": "run_started",
                "schedule_id": run["schedule_id"],
                "dag_path": run["dag_path"],
                "tenant": run["tenant"],
                "minute": run["minute"],
            }
        )

        try:
            dag = load_dag_from_yaml(run["dag_path"])
            result = run_dag(dag, tenant=run["tenant"], dry_run=False, events_path=events_path)

            record_event(
                {
                    "event": "run_finished",
                    "schedule_id": run["schedule_id"],
                    "dag_path": run["dag_path"],
                    "tenant": run["tenant"],
                    "minute": run["minute"],
                    "status": "success",
                    "duration_seconds": result.get("duration_seconds", 0),
                }
            )

            return {"run": run, "status": "success", "result": result}

        except Exception as e:
            end_time = datetime.now(UTC)
            duration = (end_time - start_time).total_seconds()

            record_event(
                {
                    "event": "run_finished",
                    "schedule_id": run["schedule_id"],
                    "dag_path": run["dag_path"],
                    "tenant": run["tenant"],
                    "minute": run["minute"],
                    "status": "failed",
                    "error": str(e),
                    "duration_seconds": duration,
                }
            )

            return {"run": run, "status": "failed", "error": str(e)}

    # Execute runs in parallel
    with ThreadPoolExecutor(max_workers=max_parallel) as executor:
        futures = {executor.submit(execute_run, run): run for run in runs_to_execute}

        for future in as_completed(futures):
            try:
                result = future.result()
                results.append(result)
            except Exception as e:
                run = futures[future]
                print(f"Error executing run {run['schedule_id']}: {e}")
                results.append({"run": run, "status": "error", "error": str(e)})

    return results


def main():
    """CLI entrypoint for scheduler."""
    parser = argparse.ArgumentParser(description="DAG Scheduler - cron-like execution for workflows")

    parser.add_argument(
        "--dir",
        default="configs/schedules",
        help="Directory containing schedule YAML files (default: configs/schedules)",
    )

    mode_group = parser.add_mutually_exclusive_group(required=True)
    mode_group.add_argument("--once", action="store_true", help="Run single tick then drain queue (CI-safe)")
    mode_group.add_argument("--serve", action="store_true", help="Serve continuously until Ctrl+C")

    args = parser.parse_args()

    # Load schedules
    schedules = load_schedules(args.dir)
    if not schedules:
        print(f"No schedules found in {args.dir}")
        return 1

    print(f"Loaded {len(schedules)} schedule(s) from {args.dir}")

    # Get config
    tick_ms = int(os.getenv("SCHED_TICK_MS", "1000"))
    max_parallel = int(os.getenv("SCHED_MAX_PARALLEL", "3"))

    run_queue: list[dict[str, Any]] = []

    if args.once:
        # Single tick mode
        print("Running single tick...")
        now = datetime.now(UTC)
        tick_once(now, schedules, run_queue)
        print(f"Enqueued {len(run_queue)} run(s)")

        if run_queue:
            print("Draining queue...")
            results = drain_queue(run_queue, max_parallel=max_parallel)
            print(f"Completed {len(results)} run(s)")

            # Summary
            success = sum(1 for r in results if r["status"] == "success")
            failed = sum(1 for r in results if r["status"] == "failed")
            print(f"Success: {success}, Failed: {failed}")

        return 0

    else:
        # Serve mode
        print(f"Serving scheduler (tick={tick_ms}ms, max_parallel={max_parallel})...")
        print("Press Ctrl+C to stop")

        try:
            while True:
                now = datetime.now(UTC)
                tick_once(now, schedules, run_queue)

                if run_queue:
                    print(f"[{now.strftime('%H:%M:%S')}] Draining {len(run_queue)} run(s)...")
                    drain_queue(run_queue, max_parallel=max_parallel)

                time.sleep(tick_ms / 1000.0)

        except KeyboardInterrupt:
            print("\nShutting down...")
            if run_queue:
                print(f"Draining final {len(run_queue)} run(s)...")
                drain_queue(run_queue, max_parallel=max_parallel)
            return 0


if __name__ == "__main__":
    sys.exit(main())
