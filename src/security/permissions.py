"""AI Orchestrator v0.1 Permissions - Simple env-based allowlist.

Sprint 55 Week 3: Permission checking for AI-generated actions.
"""

import os


def can_execute(action: str) -> bool:
    """Check if action is allowed to execute.

    Args:
        action: Action ID (e.g., "gmail.send", "outlook.send")

    Returns:
        True if action is allowed, False otherwise
    """
    # Get allowlist from environment (comma-separated)
    allowlist_str = os.getenv("ALLOW_ACTIONS_DEFAULT", "gmail.send,outlook.send")
    allowed_actions = [a.strip() for a in allowlist_str.split(",")]

    return action in allowed_actions


def get_allowed_actions() -> list[str]:
    """Get list of allowed actions.

    Returns:
        List of allowed action IDs
    """
    allowlist_str = os.getenv("ALLOW_ACTIONS_DEFAULT", "gmail.send,outlook.send")
    return [a.strip() for a in allowlist_str.split(",")]
