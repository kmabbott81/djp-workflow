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

    # Orchestrator section (Sprint 27C)
    st.markdown("### 🔀 Orchestrator (DAGs & Schedules)")
    _render_orchestrator()

    # Cost tracking section (always visible)
    st.markdown("---")
    st.markdown("### 💰 API Cost Tracking")
    _render_cost_tracking()

    # Cost governance section (Sprint 30)
    st.markdown("---")
    st.markdown("### 🎯 Cost Governance & Budgets")
    _render_cost_governance()

    # Approvals section (Sprint 31)
    st.markdown("---")
    st.markdown("### ✅ Checkpoint Approvals")
    _render_approvals()

    # Storage lifecycle section
    st.markdown("---")
    st.markdown("### 💾 Storage Lifecycle")
    _render_storage_lifecycle()

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


def _render_cost_governance():
    """Render cost governance section with budget status and anomalies (Sprint 30)."""
    try:
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.cost.anomaly import detect_anomalies
        from src.cost.budgets import get_global_budget
        from src.cost.ledger import load_cost_events, rollup, window_sum

        # Load cost events
        events = load_cost_events(window_days=31)

        if not events:
            st.info("No cost data available. Run workflows to see budget status here.")
            return

        # Global budget status
        st.markdown("#### Global Budget Status")

        global_budget = get_global_budget()
        global_daily = window_sum(events, tenant=None, days=1)
        global_monthly = window_sum(events, tenant=None, days=30)

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            daily_pct = (global_daily / global_budget["daily"] * 100) if global_budget["daily"] > 0 else 0
            st.metric("Daily Spend", f"${global_daily:.2f}", f"{daily_pct:.1f}% of budget")

        with col2:
            st.metric("Daily Budget", f"${global_budget['daily']:.2f}")

        with col3:
            monthly_pct = (global_monthly / global_budget["monthly"] * 100) if global_budget["monthly"] > 0 else 0
            st.metric("Monthly Spend", f"${global_monthly:.2f}", f"{monthly_pct:.1f}% of budget")

        with col4:
            st.metric("Monthly Budget", f"${global_budget['monthly']:.2f}")

        # Top tenants by spend
        st.markdown("#### Top Tenants by Spend (Last 30 Days)")

        tenant_rollup = rollup(events, by=("tenant",))[:10]  # Top 10

        if tenant_rollup:
            import pandas as pd

            from src.cost.budgets import get_tenant_budget, is_over_budget

            table_data = []
            for record in tenant_rollup:
                tenant = record["tenant"]
                daily_spend = window_sum(events, tenant=tenant, days=1)
                monthly_spend = window_sum(events, tenant=tenant, days=30)

                budget = get_tenant_budget(tenant)
                status = is_over_budget(tenant, daily_spend, monthly_spend)

                status_icon = "✅" if not (status["daily"] or status["monthly"]) else "🚨"

                table_data.append(
                    {
                        "Tenant": tenant,
                        "Daily": f"${daily_spend:.2f}",
                        "Monthly": f"${monthly_spend:.2f}",
                        "Budget (D/M)": f"${budget['daily']:.0f} / ${budget['monthly']:.0f}",
                        "Status": status_icon,
                    }
                )

            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

        # Cost anomalies
        st.markdown("#### Cost Anomalies")

        anomalies = detect_anomalies()

        if anomalies:
            st.warning(f"⚠️ {len(anomalies)} cost anomalies detected today")

            import pandas as pd

            anomaly_data = []
            for anom in anomalies[:10]:  # Top 10
                anomaly_data.append(
                    {
                        "Tenant": anom["tenant"],
                        "Today": f"${anom['today_spend']:.2f}",
                        "Baseline": f"${anom['baseline_mean']:.2f}",
                        "Threshold": f"${anom['threshold']:.2f}",
                        "Sigma": f"{anom['sigma']}σ",
                    }
                )

            df = pd.DataFrame(anomaly_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.success("✅ No cost anomalies detected")

        # Governance events
        st.markdown("#### Recent Governance Events")

        governance_log_path = Path("logs/governance_events.jsonl")

        if governance_log_path.exists():
            gov_events = []
            with open(governance_log_path) as f:
                for line in f:
                    if line.strip():
                        gov_events.append(json.loads(line))

            if gov_events:
                recent_gov = gov_events[-10:]  # Last 10

                import pandas as pd

                gov_data = []
                for event in reversed(recent_gov):
                    gov_data.append(
                        {
                            "Timestamp": event.get("timestamp", "")[:19],
                            "Event": event.get("event", ""),
                            "Tenant": event.get("tenant", ""),
                            "Reason": event.get("reason", ""),
                        }
                    )

                df = pd.DataFrame(gov_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No governance events recorded yet")
        else:
            st.info("No governance events recorded yet")

    except Exception as e:
        st.error(f"Error loading cost governance data: {e}")
        st.caption("Make sure cost governance system is initialized and accessible")


def _render_approvals():
    """Render approvals section with pending checkpoints and recent actions (Sprint 31)."""
    try:
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.orchestrator.checkpoints import list_checkpoints

        # Pending checkpoints
        st.markdown("#### Pending Checkpoints")

        pending = list_checkpoints(status="pending")

        if pending:
            import pandas as pd

            table_data = []
            for cp in pending[:20]:  # Top 20
                table_data.append(
                    {
                        "Checkpoint ID": cp["checkpoint_id"][:20] + "...",
                        "DAG Run": cp["dag_run_id"][:20] + "...",
                        "Task": cp["task_id"],
                        "Prompt": cp["prompt"][:50],
                        "Role": cp["required_role"],
                        "Created": cp["created_at"][:19],
                        "Expires": cp["expires_at"][:19],
                    }
                )

            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)

            # CLI command hints
            st.markdown("**CLI Commands:**")
            st.code(
                """# List pending checkpoints
python scripts/approvals.py list

# Approve a checkpoint
python scripts/approvals.py approve <checkpoint_id> --kv key=value

# Reject a checkpoint
python scripts/approvals.py reject <checkpoint_id> --reason "Not ready"

# Resume DAG after approval
python scripts/run_dag_min.py --dag <path> --resume <dag_run_id>""",
                language="bash",
            )
        else:
            st.info("✅ No pending checkpoints")

        # Recent approvals/rejections
        st.markdown("#### Recent Approvals & Rejections")

        approved = list_checkpoints(status="approved")
        rejected = list_checkpoints(status="rejected")
        expired = list_checkpoints(status="expired")

        recent = (approved + rejected + expired)[:20]  # Last 20

        if recent:
            import pandas as pd

            table_data = []
            for cp in recent:
                status_icon = {
                    "approved": "✅",
                    "rejected": "🚫",
                    "expired": "⏰",
                }.get(cp["status"], "•")

                action_by = cp.get("approved_by") or cp.get("rejected_by") or "-"
                action_at = cp.get("approved_at") or cp.get("rejected_at") or cp["created_at"]

                table_data.append(
                    {
                        "Status": status_icon,
                        "Task": cp["task_id"],
                        "DAG Run": cp["dag_run_id"][:20] + "...",
                        "Prompt": cp["prompt"][:40],
                        "Action By": action_by,
                        "Action At": action_at[:19],
                    }
                )

            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No approval/rejection history")

    except Exception as e:
        st.error(f"Error loading approvals data: {e}")
        st.caption("Make sure checkpoints system is initialized and accessible")


def _render_storage_lifecycle():
    """Render storage lifecycle section with tier stats and recent events."""
    try:
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
        from storage.lifecycle import get_last_lifecycle_job, get_recent_lifecycle_events
        from storage.tiered_store import get_all_tier_stats

        # Tier statistics
        st.markdown("#### Artifact Distribution by Tier")

        stats = get_all_tier_stats()

        col1, col2, col3 = st.columns(3)

        with col1:
            hot_stats = stats["hot"]
            st.metric("🔥 Hot Tier", hot_stats["artifact_count"], f"{hot_stats['total_bytes'] / (1024 * 1024):.1f} MB")
            st.caption(f"{hot_stats['tenant_count']} tenants")

        with col2:
            warm_stats = stats["warm"]
            st.metric(
                "🌡️ Warm Tier", warm_stats["artifact_count"], f"{warm_stats['total_bytes'] / (1024 * 1024):.1f} MB"
            )
            st.caption(f"{warm_stats['tenant_count']} tenants")

        with col3:
            cold_stats = stats["cold"]
            st.metric(
                "❄️ Cold Tier", cold_stats["artifact_count"], f"{cold_stats['total_bytes'] / (1024 * 1024):.1f} MB"
            )
            st.caption(f"{cold_stats['tenant_count']} tenants")

        # Last lifecycle job
        st.markdown("#### Last Lifecycle Job")

        last_job = get_last_lifecycle_job()

        if last_job:
            job_col1, job_col2, job_col3, job_col4 = st.columns(4)

            with job_col1:
                timestamp = last_job.get("timestamp", "N/A")[:19]
                st.caption("**Timestamp**")
                st.text(timestamp)

            with job_col2:
                mode = "🧪 DRY RUN" if last_job.get("dry_run") else "✅ LIVE"
                st.caption("**Mode**")
                st.text(mode)

            with job_col3:
                promoted = last_job.get("promoted_to_warm", 0) + last_job.get("promoted_to_cold", 0)
                st.caption("**Promoted**")
                st.text(f"{promoted}")

            with job_col4:
                purged = last_job.get("purged", 0)
                st.caption("**Purged**")
                st.text(f"{purged}")

            if last_job.get("total_errors", 0) > 0:
                st.warning(f"⚠️ Last job had {last_job['total_errors']} errors")
        else:
            st.info("No lifecycle jobs have been run yet")

        # Recent lifecycle events
        st.markdown("#### Recent Lifecycle Events (Last 20)")

        events = get_recent_lifecycle_events(limit=20)

        if events:
            import pandas as pd

            table_data = []
            for event in reversed(events):  # Most recent first
                event_type = event.get("event_type", "unknown")
                timestamp = event.get("timestamp", "")[:19]

                # Format event details
                details = []
                if "artifact_id" in event:
                    details.append(f"artifact={event['artifact_id'][:20]}")
                if "tenant_id" in event:
                    details.append(f"tenant={event['tenant_id'][:15]}")
                if "promoted_to_warm" in event:
                    details.append(f"warm={event['promoted_to_warm']}")
                if "promoted_to_cold" in event:
                    details.append(f"cold={event['promoted_to_cold']}")
                if "purged" in event:
                    details.append(f"purged={event['purged']}")
                if "from_tier" in event and "to_tier" in event:
                    details.append(f"{event['from_tier']}→{event['to_tier']}")

                table_data.append(
                    {
                        "Timestamp": timestamp,
                        "Event Type": event_type[:30],
                        "Details": ", ".join(details)[:50],
                    }
                )

            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No lifecycle events recorded yet")

        # Quick actions
        st.markdown("#### Quick Actions")

        action_col1, action_col2 = st.columns(2)

        with action_col1:
            if st.button("🔄 Run Lifecycle Job (Dry Run)"):
                st.info("To run lifecycle job, use: `python scripts/lifecycle_run.py --dry-run`")

        with action_col2:
            if st.button("📊 View Full Statistics"):
                st.info("To view full statistics, use: `python scripts/lifecycle_run.py --summary`")

    except Exception as e:
        st.error(f"Error loading storage lifecycle data: {e}")
        st.caption("Make sure storage system is initialized and accessible")


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
            [
                {"Workflow": k, "Total Cost": f"${v:.6f}", "Requests": sum(1 for e in events if e.get("workflow") == k)}
                for k, v in sorted(workflow_costs.items(), key=lambda x: x[1], reverse=True)
            ]
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


def _render_queue_stats():
    """Render queue statistics (Sprint 28)."""
    try:
        import os
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent))

        # Get queue backend
        backend_type = os.getenv("QUEUE_BACKEND", "memory")

        if backend_type == "memory":
            st.info("Using in-memory queue (non-persistent). Set QUEUE_BACKEND=redis for persistence.")
            return

        # Try to get Redis queue stats
        try:
            import redis

            from src.queue.backends.redis import RedisQueue
            from src.queue.persistent_queue import JobStatus

            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
            client = redis.from_url(redis_url, decode_responses=False)
            queue = RedisQueue(client, key_prefix="orch:queue")

            # Get counts
            pending = queue.count(JobStatus.PENDING)
            running = queue.count(JobStatus.RUNNING)
            success = queue.count(JobStatus.SUCCESS)
            failed = queue.count(JobStatus.FAILED)

            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric("⏳ Pending", pending)

            with col2:
                st.metric("🔄 Running", running)

            with col3:
                st.metric("✅ Success", success)

            with col4:
                st.metric("❌ Failed", failed)

            # Recent jobs
            if pending > 0 or running > 0:
                st.markdown("**Recent Jobs:**")
                recent_jobs = queue.list_jobs(limit=5)

                if recent_jobs:
                    import pandas as pd

                    job_data = []
                    for job in recent_jobs:
                        status_icon = {
                            "pending": "⏳",
                            "running": "🔄",
                            "success": "✅",
                            "failed": "❌",
                            "retry": "⟳",
                        }.get(job.status.value, "❓")

                        job_data.append(
                            {
                                "Status": f"{status_icon} {job.status.value}",
                                "Job ID": job.id[:16] + "...",
                                "Schedule": job.schedule_id or "N/A",
                                "Tenant": job.tenant_id[:20],
                                "Enqueued": job.enqueued_at[:19] if job.enqueued_at else "N/A",
                            }
                        )

                    df = pd.DataFrame(job_data)
                    st.dataframe(df, use_container_width=True, hide_index=True)

        except Exception as e:
            st.warning(f"Could not connect to Redis queue: {e}")
            st.caption("Set REDIS_URL environment variable to connect to Redis")

    except Exception as e:
        st.error(f"Error loading queue stats: {e}")


def _render_orchestrator():
    """Render orchestrator observability section (Sprint 27C + Sprint 28 update)."""
    try:
        import sys

        sys.path.insert(0, str(Path(__file__).parent.parent))
        from src.orchestrator.analytics import (
            get_events_path,
            get_state_path,
            load_events,
            per_tenant_load,
            summarize_dags,
            summarize_schedules,
            summarize_tasks,
        )

        # Load events
        events_path = get_events_path()
        state_path = get_state_path()

        events = load_events(events_path, limit=5000)
        state_events = load_events(state_path, limit=5000)

        if not events and not state_events:
            st.info(
                "No orchestrator data yet. Run DAGs with `python scripts/run_dag_min.py` "
                "or start scheduler with `python -m src.orchestrator.scheduler --serve`"
            )
            return

        # Queue stats (Sprint 28)
        st.markdown("#### Queue Status")
        _render_queue_stats()

        # Task KPIs (last 24h)
        st.markdown("#### Task Metrics (Last 24 Hours)")

        task_stats = summarize_tasks(events, window_hours=24)
        recent = task_stats.get("last_24h", {})

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("✅ Tasks OK", recent.get("tasks_ok", 0))

        with col2:
            st.metric("❌ Tasks Failed", recent.get("tasks_fail", 0))

        with col3:
            avg_dur = recent.get("avg_duration", 0)
            st.metric("⏱️ Avg Duration", f"{avg_dur:.2f}s" if avg_dur > 0 else "N/A")

        with col4:
            error_rate = recent.get("error_rate", 0)
            st.metric("📊 Error Rate", f"{error_rate * 100:.1f}%")

        # Recent DAG runs
        st.markdown("#### Recent DAG Runs")

        dag_runs = summarize_dags(events, limit=15)

        if dag_runs:
            import pandas as pd

            table_data = []
            for run in dag_runs:
                status_icon = "✅" if run["status"] == "completed" else "🔄"
                table_data.append(
                    {
                        "Status": f"{status_icon} {run['status']}",
                        "DAG": run["dag_name"],
                        "Started": run["start"][:19] if run.get("start") else "N/A",
                        "Duration": f"{run.get('duration', 0):.1f}s",
                        "Tasks OK": run.get("tasks_ok", 0),
                        "Tasks Failed": run.get("tasks_fail", 0),
                    }
                )

            df = pd.DataFrame(table_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No DAG runs recorded yet")

        # Schedules
        if state_events:
            st.markdown("#### Schedules")

            schedules = summarize_schedules(state_events)

            if schedules:
                import pandas as pd

                sched_data = []
                for sched in schedules:
                    status_icon = (
                        "✅"
                        if sched.get("last_status") == "success"
                        else "❌"
                        if sched.get("last_status") == "failed"
                        else "⏸️"
                    )

                    sched_data.append(
                        {
                            "Schedule ID": sched["schedule_id"],
                            "Last Run": sched.get("last_run", "Never")[:19] if sched.get("last_run") else "Never",
                            "Status": f"{status_icon} {sched.get('last_status', 'N/A')}",
                            "Enqueued": sched.get("enqueued_count", 0),
                            "Success": sched.get("success_count", 0),
                            "Failed": sched.get("failed_count", 0),
                        }
                    )

                df = pd.DataFrame(sched_data)
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("No schedules tracked yet")

        # Per-tenant load
        st.markdown("#### Per-Tenant Load (Last 24 Hours)")

        tenant_stats = per_tenant_load(events, window_hours=24)

        if tenant_stats:
            import pandas as pd

            tenant_data = []
            for tenant in tenant_stats:
                tenant_data.append(
                    {
                        "Tenant": tenant["tenant"],
                        "Runs": tenant["runs"],
                        "Tasks": tenant["tasks"],
                        "Error Rate": f"{tenant['error_rate'] * 100:.1f}%",
                        "Avg Latency": f"{tenant['avg_latency']:.2f}s" if tenant["avg_latency"] > 0 else "N/A",
                    }
                )

            df = pd.DataFrame(tenant_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("No tenant activity in last 24 hours")

        # Quick links
        st.markdown("#### Quick Links")

        link_col1, link_col2 = st.columns(2)

        with link_col1:
            if st.button("📁 Open Logs Folder"):
                st.info(f"Events: {events_path}\nState: {state_path}")

        with link_col2:
            if st.button("📖 View Documentation"):
                st.info("See docs/ORCHESTRATION.md for full guide")

    except Exception as e:
        st.error(f"Error loading orchestrator data: {e}")
        st.caption("Make sure orchestrator is initialized and logs are accessible")
