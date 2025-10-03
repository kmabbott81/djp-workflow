"""
Workflow Adapter - Maps workflow references to callable functions.

Shims to existing example workflows, returning small payloads.
File writes from original workflows are preserved.
"""

from typing import Callable


def inbox_drive_sweep_adapter(params: dict) -> dict:
    """
    Adapter for inbox/drive sweep workflow.

    Args:
        params: Input parameters

    Returns:
        Dict with summary of prioritized items
    """
    # Minimal shim - in real impl, would call actual workflow
    return {
        "summary": "Prioritized 15 items: 5 high, 7 medium, 3 low",
        "high_priority_count": 5,
        "action_items": ["Budget approval", "Sprint planning", "Q4 roadmap"],
    }


def weekly_report_pack_adapter(params: dict) -> dict:
    """
    Adapter for weekly report generation.

    Args:
        params: Input parameters (may include upstream outputs)

    Returns:
        Dict with report summary
    """
    # Can access upstream via namespaced keys like "sweep__summary"
    upstream_summary = params.get("sweep__summary", "No upstream data")

    return {
        "summary": f"Generated weekly report. Incorporated: {upstream_summary}",
        "sections": ["Executive Summary", "Accomplishments", "Metrics", "Next Week"],
        "word_count": 1200,
    }


def meeting_transcript_brief_adapter(params: dict) -> dict:
    """
    Adapter for meeting transcript briefing.

    Args:
        params: Input parameters

    Returns:
        Dict with brief summary
    """
    return {
        "summary": "Generated meeting brief with 8 action items",
        "action_items": 8,
        "decisions": 3,
        "follow_ups": ["Schedule Q4 planning", "Review budget", "Update roadmap"],
    }


# Workflow registry - maps workflow_ref strings to callable functions
WORKFLOW_MAP: dict[str, Callable[[dict], dict]] = {
    "inbox_drive_sweep": inbox_drive_sweep_adapter,
    "weekly_report_pack": weekly_report_pack_adapter,
    "meeting_transcript_brief": meeting_transcript_brief_adapter,
}
