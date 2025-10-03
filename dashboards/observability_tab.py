"""Observability tab with per-region metrics, cost tracking, and failover events.

Shows health status, error rates, deployment events, and API cost tracking.
"""

import json
import os
from datetime import datetime
from pathlib import Path

import streamlit as st


def render_observability_tab():
    """Render observability dashboard with region tiles and cost tracking."""
    st.subheader("📊 Observability")

    # Cost tracking section (always visible)
    st.markdown("### 💰 API Cost Tracking")
    _render_cost_tracking()

    # Multi-region observability
    st.markdown("---")
    st.markdown("### 🌍 Multi-Region Status")

    # Check if multi-region enabled
    feature_multi_region = os.getenv("FEATURE_MULTI_REGION", "false").lower() == "true"

    if not feature_multi_region:
        st.info("Multi-region observability disabled. Set FEATURE_MULTI_REGION=true to enable.")
    else:
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
        st.markdown("#### Region Health")

        cols = st.columns(min(len(regions), 3))  # Max 3 columns

        for idx, region in enumerate(regions):
            col = cols[idx % len(cols)]

            with col:
                _render_region_tile(region, region == primary)

        # Recent failover events
        st.markdown("---")
        st.markdown("#### Recent Failover Events")

        _render_failover_events()

        # Deployment audit log
        st.markdown("---")
        st.markdown("#### Recent Deployments")

        _render_deployment_log()


def _render_cost_tracking():
    """Render cost tracking section with recent API usage."""
    cost_log_path = Path("logs/cost_events.jsonl")

    if not cost_log_path.exists():
        st.info("No cost data recorded yet. Run workflows to see API costs here.")
        return

    try:
        # Read cost events
        events = []
        with open(cost_log_path) as f:
            for line in f:
                if line.strip():
                    events.append(json.loads(line))

        if not events:
            st.info("No cost data recorded yet. Run workflows to see API costs here.")
            return

        # Get last 20 events
        recent_events = events[-20:]

        # Calculate totals
        total_cost = sum(event.get("cost_estimate", 0.0) for event in events)
        total_tokens_in = sum(event.get("tokens_in", 0) for event in events)
        total_tokens_out = sum(event.get("tokens_out", 0) for event in events)

        # Summary metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Requests", len(events))

        with col2:
            st.metric("Total Cost", f"${total_cost:.4f}")

        with col3:
            st.metric("Input Tokens", f"{total_tokens_in:,}")

        with col4:
            st.metric("Output Tokens", f"{total_tokens_out:,}")

        # Recent events table
        st.markdown("#### Recent API Calls (Last 20)")

        # Prepare data for table
        import pandas as pd

        table_data = []
        for event in reversed(recent_events):  # Most recent first
            table_data.append(
                {
                    "Timestamp": event.get("timestamp", "")[:19],  # Trim milliseconds
                    "Tenant": event.get("tenant", ""),
                    "Workflow": event.get("workflow", ""),
                    "Model": event.get("model", ""),
                    "Tokens In": event.get("tokens_in", 0),
                    "Tokens Out": event.get("tokens_out", 0),
                    "Cost": f"${event.get('cost_estimate', 0.0):.6f}",
                }
            )

        df = pd.DataFrame(table_data)
        st.dataframe(df, use_container_width=True, hide_index=True)

        # Cost breakdown by workflow
        st.markdown("#### Cost by Workflow")

        workflow_costs = {}
        for event in events:
            workflow = event.get("workflow", "unknown")
            cost = event.get("cost_estimate", 0.0)
            workflow_costs[workflow] = workflow_costs.get(workflow, 0.0) + cost

        workflow_df = pd.DataFrame(
            [{"Workflow": k, "Total Cost": f"${v:.6f}", "Requests": sum(1 for e in events if e.get("workflow") == k)} for k, v in sorted(workflow_costs.items(), key=lambda x: x[1], reverse=True)]
        )

        st.dataframe(workflow_df, use_container_width=True, hide_index=True)

        # Export option
        if st.button("📥 Export Cost Data (CSV)"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="Download CSV",
                data=csv,
                file_name=f"cost_events_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
            )

    except Exception as e:
        st.error(f"Error loading cost data: {e}")


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
