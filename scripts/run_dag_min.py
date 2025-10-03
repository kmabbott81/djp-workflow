#!/usr/bin/env python3
"""
Minimal DAG Runner CLI

Loads a DAG from YAML, validates, and executes (or dry-runs).

Usage:
    python scripts/run_dag_min.py --dag configs/dags/weekly_ops_chain.min.yaml
    python scripts/run_dag_min.py --dag configs/dags/weekly_ops_chain.min.yaml --dry-run
    python scripts/run_dag_min.py --dag configs/dags/weekly_ops_chain.min.yaml --tenant acme_corp
"""

import argparse
import sys
from pathlib import Path

import yaml

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator.graph import DAG, Task  # noqa: E402
from src.orchestrator.runner import RunnerError, run_dag  # noqa: E402


def load_dag_from_yaml(path: str) -> DAG:
    """Load DAG from YAML file."""
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    tasks = [
        Task(
            id=t["id"],
            workflow_ref=t["workflow_ref"],
            params=t.get("params", {}),
            retries=t.get("retries", 0),
            depends_on=t.get("depends_on", []),
        )
        for t in data["tasks"]
    ]

    return DAG(name=data["name"], tasks=tasks, tenant_id=data.get("tenant_id", "local-dev"))


def main():
    parser = argparse.ArgumentParser(
        description="Run a DAG from YAML configuration", formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--dag", required=True, help="Path to DAG YAML file")
    parser.add_argument("--dry-run", action="store_true", help="Print execution plan without running")
    parser.add_argument("--tenant", default=None, help="Override tenant ID")

    args = parser.parse_args()

    # Load DAG
    try:
        dag = load_dag_from_yaml(args.dag)
    except Exception as e:
        print(f"Error loading DAG: {e}")
        return 1

    # Override tenant if specified
    if args.tenant:
        dag.tenant_id = args.tenant

    # Execute
    try:
        result = run_dag(dag, tenant=dag.tenant_id, dry_run=args.dry_run, max_retries_default=0)

        if args.dry_run:
            print(f"\nDry run complete. {result['tasks_planned']} tasks would execute.")
        else:
            print("\n" + "=" * 60)
            print("DAG EXECUTION COMPLETE")
            print("=" * 60)
            print(f"DAG: {result['dag_name']}")
            print(f"Tasks Succeeded: {result['tasks_succeeded']}")
            print(f"Tasks Failed: {result['tasks_failed']}")
            print(f"Duration: {result['duration_seconds']:.2f}s")
            print("=" * 60)

            # Show task outputs
            if result.get("task_outputs"):
                print("\nTask Outputs:")
                for task_id, output in result["task_outputs"].items():
                    print(f"  {task_id}: {output.get('summary', output)}")

        return 0

    except RunnerError as e:
        print(f"\nError executing DAG: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
