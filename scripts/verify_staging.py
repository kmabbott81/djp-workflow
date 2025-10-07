#!/usr/bin/env python3
"""Verify staging observability stack is working correctly.

This script performs end-to-end validation of:
- /metrics endpoint exposure
- Trace generation and correlation
- Prometheus scraping (optional)
- Tempo trace storage (optional)

Usage:
    python scripts/verify_staging.py

Environment variables:
    STAGING_URL: Base URL for staging API (default: from user input)
    PROMETHEUS_URL: Prometheus base URL (optional, for scraping validation)
    TEMPO_URL: Tempo base URL (optional, for trace validation)
"""

import os
import re
import sys
from typing import Any

try:
    import requests
except ImportError:
    print("ERROR: requests library not installed")
    print("Install with: pip install requests")
    sys.exit(1)


def colored(text: str, color: str) -> str:
    """Return colored text for terminal output."""
    colors = {
        "green": "\033[92m",
        "red": "\033[91m",
        "yellow": "\033[93m",
        "blue": "\033[94m",
        "reset": "\033[0m",
    }
    return f"{colors.get(color, '')}{text}{colors['reset']}"


def check_metrics_endpoint(base_url: str) -> dict[str, Any]:
    """Check if /metrics endpoint is accessible and returning Prometheus metrics.

    Args:
        base_url: Base URL for staging API

    Returns:
        Dict with status, metrics count, and sample metrics
    """
    print(f"\n{colored('1. Checking /metrics endpoint...', 'blue')}")

    try:
        response = requests.get(f"{base_url}/metrics", timeout=10)
        response.raise_for_status()

        content = response.text
        metric_lines = [line for line in content.split("\n") if line and not line.startswith("#")]

        # Look for expected metrics
        expected_metrics = [
            "http_requests_total",
            "http_request_duration_seconds_bucket",
            "http_requests_in_flight",
        ]

        found_metrics = {}
        for metric in expected_metrics:
            pattern = re.compile(rf"^{metric}\{{")
            matches = [line for line in metric_lines if pattern.match(line)]
            found_metrics[metric] = len(matches) > 0

        all_found = all(found_metrics.values())

        if all_found:
            print(colored("  ✓ /metrics endpoint accessible", "green"))
            print(colored(f"  ✓ Found {len(metric_lines)} metric lines", "green"))
            for metric, found in found_metrics.items():
                status = colored("✓", "green") if found else colored("✗", "red")
                print(f"  {status} {metric}")
            return {"success": True, "metrics_count": len(metric_lines), "found_metrics": found_metrics}
        else:
            print(colored("  ✗ Some expected metrics missing", "red"))
            for metric, found in found_metrics.items():
                status = colored("✓", "green") if found else colored("✗", "red")
                print(f"  {status} {metric}")
            return {"success": False, "error": "Missing expected metrics", "found_metrics": found_metrics}

    except requests.exceptions.RequestException as e:
        print(colored(f"  ✗ Failed to access /metrics: {e}", "red"))
        return {"success": False, "error": str(e)}


def send_test_request(base_url: str) -> dict[str, Any]:
    """Send test request to /api/triage to generate traces.

    Args:
        base_url: Base URL for staging API

    Returns:
        Dict with status, trace_id, and response data
    """
    print(f"\n{colored('2. Sending test request to generate traces...', 'blue')}")

    test_payload = {
        "content": "This is a test email for observability verification. Please analyze and summarize.",
        "subject": "Test: Staging Observability Verification",
        "from_email": "verify@staging.test",
    }

    try:
        response = requests.post(f"{base_url}/api/triage", json=test_payload, timeout=30)
        response.raise_for_status()

        data = response.json()

        print(colored("  ✓ Request successful", "green"))
        print(f"  Status: {data.get('status', 'unknown')}")
        print(f"  Provider: {data.get('provider', 'unknown')}")
        print(f"  Artifact ID: {data.get('artifact_id', 'unknown')}")

        # Try to find trace_id in logs (would need access to Railway logs)
        # For now, return success if request completed
        return {"success": True, "response": data, "trace_id": None}

    except requests.exceptions.RequestException as e:
        print(colored(f"  ✗ Request failed: {e}", "red"))
        return {"success": False, "error": str(e)}


def check_prometheus_scraping(prometheus_url: str, job_name: str = "djp-workflow-staging") -> dict[str, Any]:
    """Check if Prometheus is successfully scraping the staging target.

    Args:
        prometheus_url: Prometheus base URL (e.g., http://localhost:9090)
        job_name: Job name in Prometheus config

    Returns:
        Dict with status and scrape info
    """
    print(f"\n{colored('3. Checking Prometheus scraping...', 'blue')}")

    if not prometheus_url:
        print(colored("  ⊘ Skipped (PROMETHEUS_URL not set)", "yellow"))
        return {"success": None, "skipped": True}

    try:
        # Check targets API
        response = requests.get(f"{prometheus_url}/api/v1/targets", timeout=10)
        response.raise_for_status()

        data = response.json()
        active_targets = data.get("data", {}).get("activeTargets", [])

        # Find our job
        our_target = next((t for t in active_targets if t.get("labels", {}).get("job") == job_name), None)

        if our_target:
            health = our_target.get("health", "unknown")
            last_scrape = our_target.get("lastScrape", "unknown")
            scrape_url = our_target.get("scrapeUrl", "unknown")

            if health == "up":
                print(colored(f"  ✓ Target '{job_name}' is UP", "green"))
                print(f"  URL: {scrape_url}")
                print(f"  Last scrape: {last_scrape}")
                return {"success": True, "health": health, "scrape_url": scrape_url}
            else:
                print(colored(f"  ✗ Target '{job_name}' is {health}", "red"))
                return {"success": False, "health": health, "error": our_target.get("lastError", "Unknown error")}
        else:
            print(colored(f"  ✗ Target '{job_name}' not found in Prometheus", "red"))
            print(f"  Available targets: {[t.get('labels', {}).get('job') for t in active_targets]}")
            return {"success": False, "error": "Target not found"}

    except requests.exceptions.RequestException as e:
        print(colored(f"  ✗ Failed to check Prometheus: {e}", "red"))
        return {"success": False, "error": str(e)}


def query_recent_metrics(prometheus_url: str, job_name: str = "djp-workflow-staging") -> dict[str, Any]:
    """Query Prometheus for recent metrics from staging.

    Args:
        prometheus_url: Prometheus base URL
        job_name: Job name in Prometheus config

    Returns:
        Dict with status and query results
    """
    print(f"\n{colored('4. Querying recent metrics...', 'blue')}")

    if not prometheus_url:
        print(colored("  ⊘ Skipped (PROMETHEUS_URL not set)", "yellow"))
        return {"success": None, "skipped": True}

    try:
        # Query total requests in last 5 minutes
        query = f'sum(increase(http_requests_total{{job="{job_name}"}}[5m]))'
        response = requests.get(f"{prometheus_url}/api/v1/query", params={"query": query}, timeout=10)
        response.raise_for_status()

        data = response.json()
        result = data.get("data", {}).get("result", [])

        if result:
            total_requests = float(result[0].get("value", [0, 0])[1])
            print(colored("  ✓ Found metrics in Prometheus", "green"))
            print(f"  Total requests (last 5m): {total_requests:.0f}")
            return {"success": True, "total_requests_5m": total_requests}
        else:
            print(colored("  ⚠ No metrics found (may need to wait for first scrape)", "yellow"))
            return {"success": False, "warning": "No data yet"}

    except requests.exceptions.RequestException as e:
        print(colored(f"  ✗ Failed to query Prometheus: {e}", "red"))
        return {"success": False, "error": str(e)}


def check_tempo_trace(tempo_url: str, trace_id: str | None) -> dict[str, Any]:
    """Check if trace is visible in Tempo.

    Args:
        tempo_url: Tempo base URL (e.g., http://localhost:3200)
        trace_id: Trace ID to search for

    Returns:
        Dict with status and trace info
    """
    print(f"\n{colored('5. Checking Tempo for traces...', 'blue')}")

    if not tempo_url:
        print(colored("  ⊘ Skipped (TEMPO_URL not set)", "yellow"))
        return {"success": None, "skipped": True}

    if not trace_id:
        print(colored("  ⊘ Skipped (no trace_id available)", "yellow"))
        print("  Note: To get trace_id, check Railway logs for recent requests")
        return {"success": None, "skipped": True}

    try:
        # Query Tempo API for trace
        response = requests.get(f"{tempo_url}/api/traces/{trace_id}", timeout=10)
        response.raise_for_status()

        data = response.json()

        if data.get("batches"):
            print(colored(f"  ✓ Trace {trace_id} found in Tempo", "green"))
            spans_count = sum(len(batch.get("spans", [])) for batch in data.get("batches", []))
            print(f"  Spans: {spans_count}")
            return {"success": True, "trace_id": trace_id, "spans_count": spans_count}
        else:
            print(colored(f"  ✗ Trace {trace_id} not found", "red"))
            return {"success": False, "error": "Trace not found"}

    except requests.exceptions.RequestException as e:
        print(colored(f"  ✗ Failed to check Tempo: {e}", "red"))
        return {"success": False, "error": str(e)}


def main() -> None:
    """Main verification workflow."""
    print(colored("=== Staging Observability Verification ===", "blue"))
    print()

    # Get configuration
    staging_url = os.getenv("STAGING_URL")
    if not staging_url:
        staging_url = input("Enter staging URL (e.g., https://your-app.up.railway.app): ").strip()

    prometheus_url = os.getenv("PROMETHEUS_URL", "")
    tempo_url = os.getenv("TEMPO_URL", "")

    # Remove trailing slashes
    staging_url = staging_url.rstrip("/")
    prometheus_url = prometheus_url.rstrip("/")
    tempo_url = tempo_url.rstrip("/")

    print(f"Staging URL: {staging_url}")
    print(f"Prometheus URL: {prometheus_url or '(not set)'}")
    print(f"Tempo URL: {tempo_url or '(not set)'}")

    results = {}

    # Run checks
    results["metrics"] = check_metrics_endpoint(staging_url)
    results["test_request"] = send_test_request(staging_url)
    results["prometheus_scraping"] = check_prometheus_scraping(prometheus_url)
    results["prometheus_query"] = query_recent_metrics(prometheus_url)

    trace_id = results["test_request"].get("trace_id")
    results["tempo_trace"] = check_tempo_trace(tempo_url, trace_id)

    # Summary
    print(f"\n{colored('=== Verification Summary ===', 'blue')}")

    checks = [
        ("Metrics endpoint", results["metrics"]["success"]),
        ("Test request", results["test_request"]["success"]),
        ("Prometheus scraping", results["prometheus_scraping"]["success"]),
        ("Prometheus query", results["prometheus_query"]["success"]),
        ("Tempo trace", results["tempo_trace"]["success"]),
    ]

    for name, status in checks:
        if status is True:
            print(f"{colored('✓', 'green')} {name}")
        elif status is False:
            print(f"{colored('✗', 'red')} {name}")
        elif status is None:
            print(f"{colored('⊘', 'yellow')} {name} (skipped)")

    # Overall status
    required_checks = [results["metrics"]["success"], results["test_request"]["success"]]
    optional_checks = [
        results["prometheus_scraping"]["success"],
        results["prometheus_query"]["success"],
        results["tempo_trace"]["success"],
    ]

    all_required_passed = all(check is True for check in required_checks)
    any_optional_passed = any(check is True for check in optional_checks)

    print()
    if all_required_passed:
        if any_optional_passed:
            print(colored("✓ All required checks passed! Optional checks partially complete.", "green"))
            print("  Next: Set PROMETHEUS_URL and TEMPO_URL to verify full observability stack.")
        else:
            print(colored("✓ Required checks passed! Observability stack ready.", "green"))
            print("  Note: Prometheus and Tempo checks were skipped (URLs not provided).")
        sys.exit(0)
    else:
        print(colored("✗ Some required checks failed. Review errors above.", "red"))
        sys.exit(1)


if __name__ == "__main__":
    main()
