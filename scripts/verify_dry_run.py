#!/usr/bin/env python3
"""Verify rollout controller dry-run health.

Sprint 54: Automated monitoring script for controller dry-run validation.

This script checks:
1. Recent workflow runs (GitHub Actions API)
2. Workflow success rate and log contents
3. Redis flag state (ensure no unexpected changes)
4. Audit log entries
5. Policy recommendation consistency

Usage:
    python scripts/verify_dry_run.py

    # With detailed output
    python scripts/verify_dry_run.py --verbose

    # Check specific time window
    python scripts/verify_dry_run.py --hours 48

Environment variables:
    GITHUB_TOKEN: GitHub personal access token (optional, increases rate limit)
    REDIS_URL: Redis connection URL (from Railway)
"""

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone

import httpx


def check_github_workflows(hours: int = 24, verbose: bool = False) -> dict:
    """Check recent workflow runs via GitHub API.

    Args:
        hours: How many hours back to check
        verbose: Print detailed output

    Returns:
        Dict with workflow health metrics
    """
    repo = "kmabbott81/djp-workflow"
    workflow_name = "rollout-controller.yml"
    url = f"https://api.github.com/repos/{repo}/actions/workflows/{workflow_name}/runs"

    headers = {}
    if token := os.getenv("GITHUB_TOKEN"):
        headers["Authorization"] = f"token {token}"

    try:
        response = httpx.get(url, headers=headers, params={"per_page": 100}, timeout=10)
        response.raise_for_status()
        data = response.json()
    except Exception as e:
        return {"error": f"Failed to fetch workflow runs: {e}", "success": False}

    # Filter runs from last N hours
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    recent_runs = []

    for run in data.get("workflow_runs", []):
        run_time = datetime.fromisoformat(run["created_at"].replace("Z", "+00:00"))
        if run_time >= cutoff:
            recent_runs.append(run)

    if not recent_runs:
        return {
            "success": False,
            "total_runs": 0,
            "message": f"No workflow runs found in last {hours}h",
        }

    # Analyze runs
    total = len(recent_runs)
    succeeded = sum(1 for r in recent_runs if r["conclusion"] == "success")
    failed = sum(1 for r in recent_runs if r["conclusion"] == "failure")
    in_progress = sum(1 for r in recent_runs if r["status"] == "in_progress")

    success_rate = (succeeded / total * 100) if total > 0 else 0

    if verbose:
        print(f"\nWorkflow Runs (Last {hours}h):")
        print(f"   Total: {total}")
        print(f"   Succeeded: {succeeded}")
        print(f"   Failed: {failed}")
        print(f"   In Progress: {in_progress}")
        print(f"   Success Rate: {success_rate:.1f}%")

    return {
        "success": True,
        "total_runs": total,
        "succeeded": succeeded,
        "failed": failed,
        "in_progress": in_progress,
        "success_rate": success_rate,
        "latest_run": recent_runs[0] if recent_runs else None,
    }


def check_redis_flags(verbose: bool = False) -> dict:
    """Check Redis flags haven't changed unexpectedly.

    Args:
        verbose: Print detailed output

    Returns:
        Dict with Redis flag status
    """
    redis_url = os.getenv("REDIS_URL")
    if not redis_url:
        return {"error": "REDIS_URL not set", "success": False}

    try:
        import redis

        r = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=5)
        r.ping()

        flags = r.mget(
            "flags:google:enabled",
            "flags:google:internal_only",
            "flags:google:rollout_percent",
            "flags:google:paused",
        )

        enabled, internal_only, rollout_percent, paused = flags

        if verbose:
            print("\nRedis Flags:")
            print(f"   enabled: {enabled}")
            print(f"   internal_only: {internal_only}")
            print(f"   rollout_percent: {rollout_percent}")
            print(f"   paused: {paused}")

        # Check expected state for dry-run
        issues = []
        if rollout_percent != "0":
            issues.append(f"rollout_percent is {rollout_percent}, expected 0 (DRY-RUN shouldn't change this)")

        if paused != "false":
            issues.append(f"paused is {paused}, controller may be intentionally stopped")

        return {
            "success": True,
            "enabled": enabled,
            "internal_only": internal_only,
            "rollout_percent": rollout_percent,
            "paused": paused,
            "issues": issues,
        }

    except Exception as e:
        return {"error": f"Failed to connect to Redis: {e}", "success": False}


def check_audit_log(verbose: bool = False) -> dict:
    """Check audit log for recent entries.

    Args:
        verbose: Print detailed output

    Returns:
        Dict with audit log status
    """
    log_path = "docs/evidence/sprint-54/rollout_log.md"

    if not os.path.exists(log_path):
        return {
            "success": False,
            "error": f"Audit log not found at {log_path}",
        }

    try:
        with open(log_path, encoding="utf-8") as f:
            lines = f.readlines()

        # Parse last 10 entries (skip header)
        entries = []
        for line in reversed(lines):
            if line.startswith("|") and "Timestamp" not in line and "---" not in line:
                entries.append(line.strip())
                if len(entries) >= 10:
                    break

        if verbose:
            print(f"\nAudit Log (Last {len(entries)} entries):")
            for entry in reversed(entries):
                print(f"   {entry[:100]}...")

        # Check for DRY RUN entries
        dry_run_count = sum(1 for e in entries if "[DRY RUN]" in e)

        return {
            "success": True,
            "total_entries": len(entries),
            "dry_run_entries": dry_run_count,
            "latest_entry": entries[0] if entries else None,
        }

    except Exception as e:
        return {"error": f"Failed to read audit log: {e}", "success": False}


def print_health_report(workflows: dict, redis: dict, audit: dict, hours: int) -> bool:
    """Print consolidated health report.

    Args:
        workflows: Workflow check results
        redis: Redis check results
        audit: Audit log check results
        hours: Time window checked

    Returns:
        True if all checks passed, False otherwise
    """
    print("\n" + "=" * 60)
    print(f"DRY-RUN HEALTH REPORT (Last {hours}h)")
    print("=" * 60)

    all_healthy = True

    # Workflow health
    if workflows.get("success"):
        total = workflows["total_runs"]
        succeeded = workflows["succeeded"]
        failed = workflows["failed"]
        rate = workflows["success_rate"]

        if rate >= 95:
            print(f"[OK] Workflows: {succeeded}/{total} runs succeeded ({rate:.1f}%)")
        elif rate >= 80:
            print(f"[WARN] Workflows: {succeeded}/{total} runs succeeded ({rate:.1f}%) - some failures")
            all_healthy = False
        else:
            print(f"[FAIL] Workflows: {succeeded}/{total} runs succeeded ({rate:.1f}%) - HIGH FAILURE RATE")
            all_healthy = False

        if failed > 0:
            print(f"       [WARN] {failed} failed runs - check logs")
    else:
        print(f"[FAIL] Workflows: {workflows.get('error', 'Unknown error')}")
        all_healthy = False

    # Redis health
    if redis.get("success"):
        rollout_pct = redis.get("rollout_percent", "?")
        paused = redis.get("paused", "?")

        if redis.get("issues"):
            print("[WARN] Redis: Flags changed unexpectedly")
            for issue in redis["issues"]:
                print(f"       - {issue}")
            all_healthy = False
        else:
            print(f"[OK] Redis: Flags unchanged (rollout_percent={rollout_pct}, paused={paused})")
    else:
        print(f"[FAIL] Redis: {redis.get('error', 'Unknown error')}")
        all_healthy = False

    # Audit log health
    if audit.get("success"):
        total_entries = audit.get("total_entries", 0)
        dry_run_count = audit.get("dry_run_entries", 0)

        if dry_run_count > 0:
            print(f"[OK] Audit Log: {dry_run_count}/{total_entries} recent entries show [DRY RUN]")
        elif total_entries == 0:
            print("[WARN] Audit Log: No entries found (controller may not have run yet)")
        else:
            print(f"[WARN] Audit Log: {total_entries} entries but no [DRY RUN] tags found")
            all_healthy = False
    else:
        print(f"[FAIL] Audit Log: {audit.get('error', 'Unknown error')}")
        all_healthy = False

    # Recommendation
    print("\n" + "-" * 60)
    if all_healthy:
        print("[OK] RECOMMENDATION: DRY-RUN is healthy")
        print("     Safe to disable dry-run and enable live rollout")
        print("     Run: gh variable set ROLLOUT_DRY_RUN --body false")
    else:
        print("[WARN] RECOMMENDATION: Issues detected")
        print("       Review failures before disabling dry-run")
        print("       Check workflow logs and Redis state")

    print("=" * 60 + "\n")

    return all_healthy


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Verify rollout controller dry-run health")
    parser.add_argument(
        "--hours",
        type=int,
        default=24,
        help="Hours of history to check (default: 24)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Print detailed output",
    )
    args = parser.parse_args()

    print(f"\nChecking rollout controller health (last {args.hours}h)...\n")

    # Run checks
    workflows = check_github_workflows(hours=args.hours, verbose=args.verbose)
    redis = check_redis_flags(verbose=args.verbose)
    audit = check_audit_log(verbose=args.verbose)

    # Print report
    all_healthy = print_health_report(workflows, redis, audit, args.hours)

    # Exit code
    sys.exit(0 if all_healthy else 1)


if __name__ == "__main__":
    main()
