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
