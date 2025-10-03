"""
Approvals CLI (Sprint 31)

Manage human-in-the-loop checkpoints via command line.
"""

import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.orchestrator.checkpoints import (  # noqa: E402
    approve_checkpoint,
    get_checkpoint,
    list_checkpoints,
    reject_checkpoint,
)
from src.security.rbac_check import can_approve  # noqa: E402


def list_command(tenant: str | None = None) -> int:
    """
    List pending checkpoints.

    Args:
        tenant: Filter by tenant (None for all)

    Returns:
        Exit code
    """
    checkpoints = list_checkpoints(tenant=tenant, status="pending")

    if not checkpoints:
        print("No pending checkpoints.")
        return 0

    print(f"{'Checkpoint ID':<40} {'Task':<20} {'DAG Run ID':<40} {'Prompt':<50} {'Role':<15} {'Created':<20}")
    print("=" * 195)

    for cp in checkpoints:
        print(
            f"{cp['checkpoint_id']:<40} "
            f"{cp['task_id']:<20} "
            f"{cp['dag_run_id']:<40} "
            f"{cp['prompt'][:47]:<50} "
            f"{cp['required_role']:<15} "
            f"{cp['created_at'][:19]:<20}"
        )

    print(f"\nTotal: {len(checkpoints)} pending checkpoint(s)")

    return 0


def approve_command(checkpoint_id: str, kv: dict[str, str] | None = None) -> int:
    """
    Approve a checkpoint.

    Args:
        checkpoint_id: Checkpoint identifier
        kv: Key-value approval data

    Returns:
        Exit code
    """
    # Get user role from env
    user_role = os.getenv("USER_RBAC_ROLE", "Viewer")

    # Get checkpoint to check required role
    checkpoint = get_checkpoint(checkpoint_id)

    if not checkpoint:
        print(f"Error: Checkpoint {checkpoint_id} not found")
        return 1

    if checkpoint["status"] != "pending":
        print(f"Error: Checkpoint {checkpoint_id} is {checkpoint['status']}, cannot approve")
        return 1

    # Check RBAC
    required_role = checkpoint.get("required_role", "Operator")

    if not can_approve(user_role, required_role):
        print(f"Error: User role '{user_role}' cannot approve checkpoint requiring '{required_role}'")
        print("Set USER_RBAC_ROLE environment variable to a role with sufficient privileges")
        return 1

    # Approve
    try:
        updated = approve_checkpoint(checkpoint_id, approved_by=user_role, approval_data=kv or {})

        print(f"✅ Checkpoint {checkpoint_id} approved by {user_role}")
        print(f"Task: {updated['task_id']}")
        print(f"DAG Run: {updated['dag_run_id']}")

        if kv:
            print(f"Approval data: {kv}")

        print("\nTo resume DAG execution:")
        print(f"  python scripts/run_dag_min.py --resume {updated['dag_run_id']}")

        return 0

    except Exception as e:
        print(f"Error approving checkpoint: {e}")
        return 1


def reject_command(checkpoint_id: str, reason: str) -> int:
    """
    Reject a checkpoint.

    Args:
        checkpoint_id: Checkpoint identifier
        reason: Rejection reason

    Returns:
        Exit code
    """
    # Get user role from env
    user_role = os.getenv("USER_RBAC_ROLE", "Viewer")

    # Get checkpoint to check required role
    checkpoint = get_checkpoint(checkpoint_id)

    if not checkpoint:
        print(f"Error: Checkpoint {checkpoint_id} not found")
        return 1

    if checkpoint["status"] != "pending":
        print(f"Error: Checkpoint {checkpoint_id} is {checkpoint['status']}, cannot reject")
        return 1

    # Check RBAC
    required_role = checkpoint.get("required_role", "Operator")

    if not can_approve(user_role, required_role):
        print(f"Error: User role '{user_role}' cannot reject checkpoint requiring '{required_role}'")
        print("Set USER_RBAC_ROLE environment variable to a role with sufficient privileges")
        return 1

    # Reject
    try:
        updated = reject_checkpoint(checkpoint_id, rejected_by=user_role, reason=reason)

        print(f"🚫 Checkpoint {checkpoint_id} rejected by {user_role}")
        print(f"Task: {updated['task_id']}")
        print(f"DAG Run: {updated['dag_run_id']}")
        print(f"Reason: {reason}")

        return 0

    except Exception as e:
        print(f"Error rejecting checkpoint: {e}")
        return 1


def main() -> int:
    """CLI entrypoint."""
    parser = argparse.ArgumentParser(description="Manage checkpoint approvals")

    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # List command
    list_parser = subparsers.add_parser("list", help="List pending checkpoints")
    list_parser.add_argument("--tenant", help="Filter by tenant")

    # Approve command
    approve_parser = subparsers.add_parser("approve", help="Approve a checkpoint")
    approve_parser.add_argument("checkpoint_id", help="Checkpoint ID")
    approve_parser.add_argument(
        "--kv",
        nargs="*",
        help="Key-value pairs for approval data (e.g., signoff_text='Approved by John')",
    )

    # Reject command
    reject_parser = subparsers.add_parser("reject", help="Reject a checkpoint")
    reject_parser.add_argument("checkpoint_id", help="Checkpoint ID")
    reject_parser.add_argument("--reason", required=True, help="Rejection reason")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    if args.command == "list":
        return list_command(tenant=args.tenant)

    elif args.command == "approve":
        # Parse key-value pairs
        kv_data = {}
        if args.kv:
            for item in args.kv:
                if "=" in item:
                    key, value = item.split("=", 1)
                    kv_data[key] = value
                else:
                    print(f"Warning: Ignoring invalid key-value pair: {item}")

        return approve_command(args.checkpoint_id, kv=kv_data)

    elif args.command == "reject":
        return reject_command(args.checkpoint_id, reason=args.reason)

    return 1


if __name__ == "__main__":
    sys.exit(main())
