"""Observability tab with per-region metrics and failover events.

Shows health status, error rates, and deployment events for multi-region setup.
"""

import json
import os
from pathlib import Path

import streamlit as st


def render_observability_tab():
    """Render observability dashboard with region tiles."""
    st.subheader("📊 Observability")

    # Check if multi-region enabled
    feature_multi_region = os.getenv("FEATURE_MULTI_REGION", "false").lower() == "true"

    if not feature_multi_region:
        st.info("Multi-region observability disabled. Set FEATURE_MULTI_REGION=true to enable.")
        return

    # Get region configuration
    try:
        from src.deploy.regions import active_regions, get_primary_region

        regions = active_regions()
        primary = get_primary_region()
    except Exception as e:
        st.error(f"Error loading region configuration: {e}")
        return

    st.caption(f"**Primary Region:** {primary}")
    st.caption(f"**Active Regions:** {', '.join(regions)}")

    # Region health tiles
    st.markdown("### Region Health")

    cols = st.columns(min(len(regions), 3))  # Max 3 columns

    for idx, region in enumerate(regions):
        col = cols[idx % len(cols)]

        with col:
            _render_region_tile(region, region == primary)

    # Recent failover events
    st.markdown("---")
    st.markdown("### Recent Failover Events")

    _render_failover_events()

    # Deployment audit log
    st.markdown("---")
    st.markdown("### Recent Deployments")

    _render_deployment_log()


def _render_region_tile(region: str, is_primary: bool):
    """
    Render health tile for a region.

    Args:
        region: Region identifier
        is_primary: Whether this is the primary region
    """
    badge = "🏠 PRIMARY" if is_primary else ""

    st.markdown(f"**{region}** {badge}")

    # In production, this would hit the actual region endpoint
    # For now, show placeholder status
    ready = True  # Placeholder

    if ready:
        st.success("✅ Ready")
    else:
        st.error("❌ Not Ready")

    # Show placeholder metrics
    st.metric("Error Rate", "0.2%", delta="-0.1%", delta_color="inverse")
    st.metric("P95 Latency", "245ms", delta="+12ms", delta_color="inverse")


def _render_failover_events():
    """Render recent failover events from region_events.jsonl."""
    events_path = Path("logs/region_events.jsonl")

    if not events_path.exists():
        st.info("No failover events recorded yet.")
        return

    try:
        # Read last 10 events
        events = []
        with open(events_path) as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))

        events = events[-10:]  # Last 10

        if not events:
            st.info("No failover events recorded yet.")
            return

        # Display as table
        for event in reversed(events):  # Most recent first
            timestamp = event.get("timestamp", "unknown")
            from_region = event.get("from_region", "unknown")
            to_region = event.get("to_region", "unknown")
            reason = event.get("reason", "unknown")

            col1, col2, col3, col4 = st.columns([2, 2, 2, 4])

            with col1:
                st.caption(timestamp)
            with col2:
                st.caption(f"From: {from_region}")
            with col3:
                st.caption(f"To: {to_region}")
            with col4:
                st.caption(f"Reason: {reason}")

    except Exception as e:
        st.error(f"Error loading failover events: {e}")


def _render_deployment_log():
    """Render recent deployment events from deploy_audit.log."""
    audit_path = Path("logs/deploy_audit.log")

    if not audit_path.exists():
        st.info("No deployment events recorded yet.")
        return

    try:
        # Read last 10 events
        events = []
        with open(audit_path) as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))

        events = events[-10:]  # Last 10

        if not events:
            st.info("No deployment events recorded yet.")
            return

        # Display as table
        for event in reversed(events):  # Most recent first
            timestamp = event.get("timestamp", "unknown")
            action = event.get("action", "unknown")
            state = event.get("state", "unknown")
            green_image = event.get("green_image", "")
            canary_weight = event.get("canary_weight", 0)

            col1, col2, col3, col4 = st.columns([2, 2, 2, 4])

            with col1:
                st.caption(timestamp)
            with col2:
                st.caption(f"Action: {action}")
            with col3:
                st.caption(f"State: {state}")
            with col4:
                if green_image:
                    st.caption(f"Green: {green_image} ({canary_weight}%)")
                else:
                    st.caption("-")

    except Exception as e:
        st.error(f"Error loading deployment log: {e}")
