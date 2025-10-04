"""Webhook ingestion for connector events.

Normalizes events from various connector sources.
"""

from datetime import datetime

from .metrics import record_call


def ingest_event(connector_type: str, payload: dict) -> dict:
    """Ingest and normalize webhook event.

    Args:
        connector_type: Source connector (teams, slack, etc.)
        payload: Raw webhook payload

    Returns:
        Normalized event structure
    """
    # Record ingestion metric
    record_call(f"{connector_type}-webhook", "ingest", "success", 5.0)

    if connector_type == "teams":
        return _normalize_teams_event(payload)
    elif connector_type == "slack":
        return _normalize_slack_event(payload)
    else:
        raise ValueError(f"Unknown connector type: {connector_type}")


def _normalize_teams_event(payload: dict) -> dict:
    """Normalize Microsoft Teams webhook event.

    Args:
        payload: Teams webhook payload

    Returns:
        Normalized event
    """
    # Teams webhook structure varies by subscription type
    # Common fields: changeType, resource, resourceData

    event_type = payload.get("changeType", "unknown")
    resource = payload.get("resource", "")

    # Determine resource type from URL pattern
    if "/teams/" in resource and "/channels/" in resource and "/messages/" in resource:
        resource_type = "message"
    elif "/teams/" in resource and "/channels/" in resource:
        resource_type = "channel"
    elif "/teams/" in resource:
        resource_type = "team"
    else:
        resource_type = "unknown"

    # Extract resource data
    resource_data = payload.get("resourceData", {})

    return {
        "connector_type": "teams",
        "event_type": event_type,
        "resource_type": resource_type,
        "resource_id": resource_data.get("id", ""),
        "timestamp": payload.get("subscriptionExpirationDateTime", datetime.now().isoformat()),
        "data": resource_data,
        "raw_payload": payload,
    }


def _normalize_slack_event(payload: dict) -> dict:
    """Normalize Slack Events API event.

    Args:
        payload: Slack Events API payload

    Returns:
        Normalized event

    Note:
        Slack Events API structure:
        {
            "type": "event_callback",
            "event": {
                "type": "message.channels",
                "channel": "C123456",
                "user": "U123456",
                "text": "Hello",
                "ts": "1234567890.123456"
            }
        }

        Optional signature verification via SLACK_SIGNING_SECRET:
        - Check X-Slack-Signature header
        - Compare HMAC SHA256 of request body
        - Verify timestamp within 5 minutes
        - Not enforced by default (documented only)
    """
    # Extract event data
    event_type = payload.get("type", "unknown")

    # Handle URL verification challenge
    if event_type == "url_verification":
        return {
            "connector_type": "slack",
            "event_type": "url_verification",
            "resource_type": "challenge",
            "resource_id": "",
            "timestamp": datetime.now().isoformat(),
            "data": {"challenge": payload.get("challenge", "")},
            "raw_payload": payload,
        }

    # Handle event callbacks
    if event_type == "event_callback":
        event = payload.get("event", {})
        event_subtype = event.get("type", "unknown")

        # Determine resource type from event type
        if "message" in event_subtype:
            resource_type = "message"
            resource_id = event.get("ts", "")
        elif "channel" in event_subtype:
            resource_type = "channel"
            resource_id = event.get("channel", "")
        elif "user" in event_subtype:
            resource_type = "user"
            resource_id = event.get("user", "")
        else:
            resource_type = "unknown"
            resource_id = ""

        return {
            "connector_type": "slack",
            "event_type": event_subtype,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "timestamp": event.get("event_ts", datetime.now().isoformat()),
            "data": event,
            "raw_payload": payload,
        }

    # Default for unknown event types
    return {
        "connector_type": "slack",
        "event_type": event_type,
        "resource_type": "unknown",
        "resource_id": "",
        "timestamp": datetime.now().isoformat(),
        "data": payload,
        "raw_payload": payload,
    }
