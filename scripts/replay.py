#!/usr/bin/env python3
"""
Replay helper for DJP workflow reproducibility.

Allows replaying any past run exactly as it was configured.
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any, Optional


def find_artifact_files(runs_dir: str = "runs") -> list[Path]:
    """Find all artifact files in the runs directory."""
    runs_path = Path(runs_dir)
    if not runs_path.exists():
        return []

    return sorted(runs_path.glob("*.json"), reverse=True)


def load_artifact(artifact_path: Path) -> dict[str, Any]:
    """Load an artifact file."""
    try:
        with open(artifact_path, encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        raise ValueError(f"Cannot load artifact {artifact_path}: {e}")


def extract_cli_args(artifact: dict[str, Any]) -> list[str]:
    """
    Extract CLI arguments from an artifact to reproduce the run.

    Args:
        artifact: Loaded artifact dictionary

    Returns:
        List of CLI arguments for python -m src.run_workflow
    """
    metadata = artifact.get("run_metadata", {})
    parameters = metadata.get("parameters", {})

    # Required arguments
    args = ["--task", metadata.get("task", ""), "--trace_name", metadata.get("trace_name", "replay-run")]

    # Add all parameters from the original run
    for key, value in parameters.items():
        if key == "allowed_models":
            # Skip this as it's handled by policy
            continue

        if key == "fastpath" and value:
            args.append("--fastpath")
        elif key != "fastpath":
            args.extend([f"--{key}", str(value)])

    return args


def list_recent_runs(limit: int = 10) -> None:
    """List recent runs with basic info."""
    artifact_files = find_artifact_files()

    if not artifact_files:
        print("No artifact files found in runs/ directory")
        return

    print(f"Recent runs (showing last {limit}):")
    print("=" * 70)

    for i, artifact_path in enumerate(artifact_files[:limit], 1):
        try:
            artifact = load_artifact(artifact_path)
            metadata = artifact.get("run_metadata", {})
            publish = artifact.get("publish", {})

            timestamp = metadata.get("timestamp", "Unknown")[:19]  # Remove microseconds
            task_preview = metadata.get("task", "")[:40] + ("..." if len(metadata.get("task", "")) > 40 else "")
            status = publish.get("status", "unknown")
            provider = publish.get("provider", "unknown")

            print(f"{i:2d}. {artifact_path.name}")
            print(f"    {timestamp} | Status: {status}")
            print(f"    Task: {task_preview}")
            print(f"    Provider: {provider}")
            print()

        except Exception as e:
            print(f"{i:2d}. {artifact_path.name} [ERROR: {e}]")
            print()


def show_run_details(artifact_path: Path) -> None:
    """Show detailed information about a specific run."""
    try:
        artifact = load_artifact(artifact_path)
        metadata = artifact.get("run_metadata", {})
        parameters = metadata.get("parameters", {})
        publish = artifact.get("publish", {})
        provenance = artifact.get("provenance", {})

        print(f"Run Details: {artifact_path.name}")
        print("=" * 50)
        print(f"Timestamp: {metadata.get('timestamp', 'Unknown')}")
        print(f"Task: {metadata.get('task', 'Unknown')}")
        print(f"Trace: {metadata.get('trace_name', 'Unknown')}")
        print(f"Status: {publish.get('status', 'unknown')}")
        print(f"Provider: {publish.get('provider', 'unknown')}")
        print(f"Duration: {provenance.get('duration_seconds', 'unknown')} seconds")

        print("\nParameters:")
        for key, value in parameters.items():
            print(f"  {key}: {value}")

        print("\nReplay Command:")
        args = extract_cli_args(artifact)
        cmd = ["python", "-m", "src.run_workflow"] + args
        print(f"  {' '.join(cmd)}")

        # Show text preview if available
        text = publish.get("text", "")
        if text:
            preview = text[:200] + ("..." if len(text) > 200 else "")
            print("\nOutput Preview:")
            print(f"  {preview}")

    except Exception as e:
        print(f"Error showing run details: {e}")


def replay_run(
    artifact_path: Path, new_task: Optional[str] = None, new_trace_name: Optional[str] = None, dry_run: bool = False
) -> int:
    """
    Replay a run with the same configuration.

    Args:
        artifact_path: Path to the artifact file
        new_task: Optional new task (uses original if not provided)
        new_trace_name: Optional new trace name
        dry_run: If True, just show the command without running it

    Returns:
        Exit code (0 for success)
    """
    try:
        artifact = load_artifact(artifact_path)
        args = extract_cli_args(artifact)

        # Override task and trace_name if provided
        if new_task:
            task_index = args.index("--task")
            args[task_index + 1] = new_task

        if new_trace_name:
            trace_index = args.index("--trace_name")
            args[trace_index + 1] = new_trace_name
        else:
            # Add replay suffix to distinguish from original
            trace_index = args.index("--trace_name")
            original_trace = args[trace_index + 1]
            args[trace_index + 1] = f"{original_trace}-replay"

        cmd = ["python", "-m", "src.run_workflow"] + args

        print(f"Replaying run from: {artifact_path.name}")
        print(f"Command: {' '.join(cmd)}")

        if dry_run:
            print("(Dry run - command not executed)")
            return 0

        print("\nExecuting replay...")
        print("-" * 50)

        # Execute the replay command
        result = subprocess.run(cmd, cwd=Path.cwd())
        return result.returncode

    except Exception as e:
        print(f"Error replaying run: {e}")
        return 1


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Replay DJP workflow runs for reproducibility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List recent runs
  python scripts/replay.py --list

  # Show details of a specific run
  python scripts/replay.py --show runs/2025.09.29-1445.json

  # Replay the most recent run
  python scripts/replay.py --latest

  # Replay a specific run
  python scripts/replay.py --replay runs/2025.09.29-1445.json

  # Replay with a different task
  python scripts/replay.py --replay runs/2025.09.29-1445.json --task "New task question"

  # Dry run (show command only)
  python scripts/replay.py --replay runs/2025.09.29-1445.json --dry-run
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)

    group.add_argument("--list", action="store_true", help="List recent runs")

    group.add_argument("--show", metavar="ARTIFACT_FILE", help="Show detailed information about a specific run")

    group.add_argument("--replay", metavar="ARTIFACT_FILE", help="Replay a specific run")

    group.add_argument("--latest", action="store_true", help="Replay the most recent run")

    parser.add_argument("--task", help="Override the original task with a new one")

    parser.add_argument("--trace-name", help="Override the trace name")

    parser.add_argument("--dry-run", action="store_true", help="Show the replay command without executing it")

    parser.add_argument("--limit", type=int, default=10, help="Number of recent runs to show (default: 10)")

    args = parser.parse_args()

    # Handle different modes
    if args.list:
        list_recent_runs(args.limit)
        return 0

    elif args.show:
        artifact_path = Path(args.show)
        if not artifact_path.exists():
            print(f"Error: Artifact file not found: {artifact_path}")
            return 1
        show_run_details(artifact_path)
        return 0

    elif args.replay:
        artifact_path = Path(args.replay)
        if not artifact_path.exists():
            print(f"Error: Artifact file not found: {artifact_path}")
            return 1
        return replay_run(artifact_path, args.task, args.trace_name, args.dry_run)

    elif args.latest:
        artifact_files = find_artifact_files()
        if not artifact_files:
            print("Error: No artifact files found")
            return 1
        latest_artifact = artifact_files[0]
        return replay_run(latest_artifact, args.task, args.trace_name, args.dry_run)

    return 0


if __name__ == "__main__":
    sys.exit(main())
