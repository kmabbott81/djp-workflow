"""Slack connector for posting notifications."""

import json
import os
from typing import Optional
from urllib import request
from urllib.error import URLError


def post_message(
    text: str,
    channel: Optional[str] = None,
    webhook_url: Optional[str] = None,
    username: str = "DJP Workflow",
    icon_emoji: str = ":robot_face:",
) -> bool:
    """
    Post message to Slack via webhook.

    Args:
        text: Message text (supports Slack markdown)
        channel: Channel override (e.g., "#general")
        webhook_url: Slack webhook URL (defaults to SLACK_WEBHOOK_URL env var)
        username: Bot username
        icon_emoji: Bot emoji icon

    Returns:
        Success status

    Environment Variables:
        SLACK_WEBHOOK_URL: Incoming webhook URL from Slack

    Example:
        >>> post_message(
        ...     text="Approval required for template output",
        ...     channel="#approvals"
        ... )
    """
    webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")

    if not webhook_url:
        print("Warning: SLACK_WEBHOOK_URL not configured. Skipping Slack post.")
        return False

    payload = {
        "text": text,
        "username": username,
        "icon_emoji": icon_emoji,
    }

    if channel:
        payload["channel"] = channel

    try:
        req = request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        with request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                print("Slack message posted successfully")
                return True
            else:
                print(f"Slack post failed: {response.status}")
                return False

    except URLError as e:
        print(f"Failed to post to Slack: {e}")
        return False


def post_approval_notification(
    template_name: str,
    preview_text: str,
    artifact_id: str,
    approval_url: Optional[str] = None,
    channel: Optional[str] = None,
    webhook_url: Optional[str] = None,
    interactive: bool = True,
) -> bool:
    """
    Post approval notification to Slack with interactive buttons.

    Args:
        template_name: Name of template
        preview_text: Preview of output
        artifact_id: Artifact identifier
        approval_url: Optional URL to approval UI
        channel: Slack channel
        webhook_url: Slack webhook URL (defaults to SLACK_WEBHOOK_URL env var)
        interactive: If True, include Approve/Reject buttons

    Returns:
        Success status
    """
    webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")

    if not webhook_url:
        print("Warning: SLACK_WEBHOOK_URL not configured. Skipping Slack post.")
        return False

    # Build Block Kit message with buttons
    blocks = [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": "⚠️ Approval Required", "emoji": True},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Template:*\n{template_name}"},
                {"type": "mrkdwn", "text": f"*Artifact ID:*\n`{artifact_id}`"},
            ],
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"*Preview:*\n```\n{preview_text[:300]}...\n```"},
        },
    ]

    if interactive:
        # Add interactive buttons
        blocks.append(
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "✅ Approve", "emoji": True},
                        "style": "primary",
                        "action_id": "approve_artifact",
                        "value": artifact_id,
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "❌ Reject", "emoji": True},
                        "style": "danger",
                        "action_id": "reject_artifact",
                        "value": artifact_id,
                    },
                ],
            }
        )
    elif approval_url:
        # Fallback to URL link if interactive disabled
        blocks.append({"type": "section", "text": {"type": "mrkdwn", "text": f"<{approval_url}|Review and Approve>"}})

    payload = {"blocks": blocks}

    if channel:
        payload["channel"] = channel

    try:
        req = request.Request(
            webhook_url,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
        )

        with request.urlopen(req, timeout=10) as response:
            if response.status == 200:
                print("Slack approval notification posted successfully")
                return True
            else:
                print(f"Slack post failed: {response.status}")
                return False

    except URLError as e:
        print(f"Failed to post to Slack: {e}")
        return False
