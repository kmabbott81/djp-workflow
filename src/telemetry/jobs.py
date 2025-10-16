"""Job telemetry metrics - Sprint 58 Slice 6.

Prometheus metrics for job execution tracking:
- relay_jobs_total: counter by status (success/failed)
- relay_jobs_per_action_total: counter by action_id + status
- relay_job_latency_seconds: histogram of job duration
"""

from prometheus_client import Counter, Histogram

# Counters
relay_jobs_total = Counter(
    "relay_jobs_total",
    "Total jobs completed",
    labelnames=["status"],
)

relay_jobs_per_action_total = Counter(
    "relay_jobs_per_action_total",
    "Total jobs per action",
    labelnames=["action_id", "status"],
)

# Histogram (10 buckets: 0.01s to 100s)
relay_job_latency_seconds = Histogram(
    "relay_job_latency_seconds",
    "Job execution latency in seconds",
    labelnames=["action_id"],
    buckets=(0.01, 0.05, 0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 25.0, 100.0),
)


def inc_job(status: str) -> None:
    """Increment total job counter.

    Args:
        status: 'success' or 'failed'
    """
    relay_jobs_total.labels(status=status).inc()


def inc_job_by_action(action_id: str, status: str) -> None:
    """Increment per-action job counter.

    Args:
        action_id: Canonical action ID (provider.action)
        status: 'success' or 'failed'
    """
    relay_jobs_per_action_total.labels(action_id=action_id, status=status).inc()


def observe_job_latency(action_id: str, seconds: float) -> None:
    """Record job latency histogram.

    Args:
        action_id: Canonical action ID (provider.action)
        seconds: Execution time in seconds (non-negative)
    """
    relay_job_latency_seconds.labels(action_id=action_id).observe(seconds)
