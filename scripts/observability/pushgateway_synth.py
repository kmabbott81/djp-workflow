#!/usr/bin/env python3
"""
Push small synthetic deltas to Pushgateway so we can validate alert routing.
Usage examples:
  python pushgateway_synth.py --scenario error-rate-warn --duration 5m
  python pushgateway_synth.py --scenario latency-crit --duration 3m
  python pushgateway_synth.py --scenario controller-stalled --duration 10m
"""
import argparse
import os
import time

import requests

PG = os.getenv("PUSHGATEWAY_URL", "http://localhost:9091")
JOB = "relay_synth"
LABELS = {"provider": "google", "action": "gmail.send"}


def push_counter(metric, labels, value):
    """Push a counter metric to Pushgateway using text exposition format."""
    labelstr = ",".join(f'{k}="{v}"' for k, v in labels.items())
    data = f"{metric}{{{labelstr}}} {value}\n"
    url = f"{PG}/metrics/job/{JOB}/instance/{int(time.time())}"
    try:
        requests.post(url, data=data, timeout=3)
    except Exception as e:
        print(f"Warning: Failed to push to Pushgateway: {e}")


def scenario_error_rate_warn(seconds):
    """Drive ~2% error while keeping exec rate > threshold (0.1 req/s)."""
    print(f"[error-rate-warn] Injecting 2% error rate for {seconds}s...")
    end = time.time() + seconds
    iteration = 0
    while time.time() < end:
        # Push 50 executions with 1 error = 2% error rate
        push_counter("action_exec_total", LABELS, 50)
        push_counter("action_error_total", LABELS, 1)
        iteration += 1
        if iteration % 6 == 0:  # Log every minute
            print(f"  [{int(time.time() - (end - seconds))}s] Pushed exec=50, error=1 (2% rate)")
        time.sleep(10)
    print("[error-rate-warn] Done. Alert should fire after ~10 minutes if threshold crossed.")


def scenario_error_rate_crit(seconds):
    """Drive ~6% error to trigger critical alert."""
    print(f"[error-rate-crit] Injecting 6% error rate for {seconds}s...")
    end = time.time() + seconds
    iteration = 0
    while time.time() < end:
        # Push 50 executions with 3 errors = 6% error rate
        push_counter("action_exec_total", LABELS, 50)
        push_counter("action_error_total", LABELS, 3)
        iteration += 1
        if iteration % 6 == 0:
            print(f"  [{int(time.time() - (end - seconds))}s] Pushed exec=50, error=3 (6% rate)")
        time.sleep(10)
    print("[error-rate-crit] Done. Critical alert should fire after ~10 minutes.")


def scenario_latency_crit(seconds):
    """Push latency buckets so P95 > 2s (critical threshold)."""
    print(f"[latency-crit] Injecting high P95 latency (>2s) for {seconds}s...")
    end = time.time() + seconds
    iteration = 0
    while time.time() < end:
        # Push histogram buckets where most requests are in high latency buckets
        # To get P95 > 2s, put 95% of requests in buckets > 2s
        for le, count in [("0.1", 1), ("0.5", 2), ("1", 2), ("2", 5), ("+Inf", 50)]:
            push_counter("action_latency_seconds_bucket", {**LABELS, "le": le}, count)
        iteration += 1
        if iteration % 6 == 0:
            print(f"  [{int(time.time() - (end - seconds))}s] Pushed latency histogram (P95 ~2.5s)")
        time.sleep(10)
    print("[latency-crit] Done. Latency critical alert should fire after ~10 minutes.")


def scenario_controller_stalled(seconds):
    """Stop pushing rollout_controller_runs_total to simulate stall."""
    print(f"[controller-stalled] Simulating controller stall for {seconds}s...")
    print("  (No metrics pushed; existing metrics will age out)")
    print("  Note: Alert fires after 60m of no successful runs + 5m for-period")
    time.sleep(seconds)
    print("[controller-stalled] Done. If this ran for 65+ minutes, stalled alert should fire.")


def scenario_validation_spike(seconds):
    """Push high structured error rate to trigger validation spike (>10% info alert)."""
    print(f"[validation-spike] Injecting 15% validation error rate for {seconds}s...")
    end = time.time() + seconds
    iteration = 0
    while time.time() < end:
        # Push high structured error count relative to traffic
        push_counter("action_exec_total", LABELS, 100)
        push_counter("structured_error_total", {**LABELS, "code": "INVALID_RECIPIENT", "source": "validation"}, 15)
        iteration += 1
        if iteration % 6 == 0:
            print(f"  [{int(time.time() - (end - seconds))}s] Pushed structured_error=15, exec=100 (15% rate)")
        time.sleep(10)
    print("[validation-spike] Done. Validation spike (info) alert should fire after ~10 minutes.")


def scenario_mime_slow(seconds):
    """Push MIME builder P95 > 500ms (warning threshold)."""
    print(f"[mime-slow] Injecting slow MIME build times (P95 ~600ms) for {seconds}s...")
    end = time.time() + seconds
    iteration = 0
    while time.time() < end:
        # Push MIME histogram with most requests in 0.5-1s bucket
        for le, count in [("0.1", 5), ("0.5", 20), ("1", 50), ("+Inf", 50)]:
            push_counter("gmail_mime_build_seconds_bucket", {"le": le}, count)
        iteration += 1
        if iteration % 6 == 0:
            print(f"  [{int(time.time() - (end - seconds))}s] Pushed MIME histogram (P95 ~600ms)")
        time.sleep(10)
    print("[mime-slow] Done. MIME slow performance alert should fire after ~10 minutes.")


def scenario_sanitization_spike(seconds):
    """Push high HTML sanitization rate (>50/sec) to trigger info alert."""
    print(f"[sanitization-spike] Injecting high sanitization activity (>50/sec) for {seconds}s...")
    end = time.time() + seconds
    iteration = 0
    while time.time() < end:
        # Push sanitization changes: 60 changes over 10s = 6/sec * 10 = 60 total
        # Rate over 5m window needs to exceed 50/sec, so push aggressively
        push_counter("gmail_html_sanitization_changes_total", {"change_type": "tag_removed"}, 300)
        push_counter("gmail_html_sanitization_changes_total", {"change_type": "attr_stripped"}, 300)
        iteration += 1
        if iteration % 6 == 0:
            print(f"  [{int(time.time() - (end - seconds))}s] Pushed sanitization=600 changes (60/sec)")
        time.sleep(10)
    print("[sanitization-spike] Done. Sanitization spike (info) alert should fire after ~5 minutes.")


SCENARIOS = {
    "error-rate-warn": scenario_error_rate_warn,
    "error-rate-crit": scenario_error_rate_crit,
    "latency-crit": scenario_latency_crit,
    "controller-stalled": scenario_controller_stalled,
    "validation-spike": scenario_validation_spike,
    "mime-slow": scenario_mime_slow,
    "sanitization-spike": scenario_sanitization_spike,
}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synthetic alert driver for testing Prometheus alerts")
    parser.add_argument("--scenario", choices=SCENARIOS.keys(), required=True, help="Alert scenario to simulate")
    parser.add_argument("--duration", default="5m", help="Duration to run scenario (e.g., 5m, 30s)")
    args = parser.parse_args()

    # Parse duration
    duration_str = args.duration
    if duration_str.endswith("m"):
        seconds = int(duration_str[:-1]) * 60
    elif duration_str.endswith("s"):
        seconds = int(duration_str[:-1])
    else:
        seconds = int(duration_str)  # Assume seconds if no suffix

    print("\n=== Pushgateway Synthetic Alert Driver ===")
    print(f"Scenario: {args.scenario}")
    print(f"Duration: {seconds}s")
    print(f"Pushgateway: {PG}")
    print(f"Job: {JOB}\n")

    SCENARIOS[args.scenario](seconds)

    print("\n=== Scenario complete ===")
    print("Check Prometheus /alerts page and Grafana dashboards for alert state.")
    print("Use Alertmanager /alerts page to verify routing and inhibition.")
