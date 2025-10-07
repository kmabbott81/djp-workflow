"""Prometheus metrics exporter for DJP Workflow.

Sprint 46: Phase 1 (Metrics) implementation.

This module provides Prometheus metrics collection behind the TELEMETRY_ENABLED flag.
All instrumentation is safe-by-default: if the flag is false or prometheus-client
is not installed, all operations become no-ops.

Metrics (SLIs):
- http_request_duration_seconds: HTTP endpoint latency histogram
- http_requests_total: Request count by method/endpoint/status
- queue_job_latency_seconds: Background job processing time
- queue_depth_total: Current queue depth gauge
- external_api_calls_total: External API call counter by service
- external_api_duration_seconds: External API latency histogram
"""

from __future__ import annotations

import logging
import os
import time
from typing import Any

_LOG = logging.getLogger(__name__)

# Lazy imports - only load prometheus_client if telemetry is enabled
_PROM_AVAILABLE = False
_METRICS_INITIALIZED = False

# Metric instances (populated on init)
_http_request_duration = None
_http_requests_total = None
_queue_job_latency = None
_queue_depth = None
_external_api_calls = None
_external_api_duration = None
# Sprint 49 Phase B: Action metrics
_action_exec_total = None
_action_latency_seconds = None
_action_error_total = None


def _is_enabled() -> bool:
    """Check if telemetry is enabled via environment variable."""
    return str(os.getenv("TELEMETRY_ENABLED", "false")).lower() in {"1", "true", "yes"}


def init_prometheus() -> None:
    """Initialize Prometheus metrics collection if enabled.

    Safe to call multiple times (idempotent). If TELEMETRY_ENABLED=false
    or prometheus-client is not installed, this becomes a no-op.
    """
    global _PROM_AVAILABLE, _METRICS_INITIALIZED
    global _http_request_duration, _http_requests_total
    global _queue_job_latency, _queue_depth
    global _external_api_calls, _external_api_duration
    global _action_exec_total, _action_latency_seconds, _action_error_total

    if not _is_enabled():
        _LOG.debug("Telemetry disabled, skipping Prometheus init")
        return

    if _METRICS_INITIALIZED:
        _LOG.debug("Prometheus metrics already initialized")
        return

    try:
        from prometheus_client import Counter, Gauge, Histogram

        _PROM_AVAILABLE = True

        # HTTP metrics
        _http_request_duration = Histogram(
            "http_request_duration_seconds",
            "HTTP request latency in seconds",
            ["method", "endpoint", "status_code"],
            buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0],
        )

        _http_requests_total = Counter(
            "http_requests_total",
            "Total HTTP requests by method, endpoint, and status code",
            ["method", "endpoint", "status_code"],
        )

        # Queue/worker metrics
        _queue_job_latency = Histogram(
            "queue_job_latency_seconds",
            "Background job processing time in seconds",
            ["job_type"],
            buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0, 120.0],
        )

        _queue_depth = Gauge(
            "queue_depth_total",
            "Current depth of background job queue",
            ["queue_name"],
        )

        # External API metrics
        _external_api_calls = Counter(
            "external_api_calls_total",
            "Total external API calls by service",
            ["service", "operation"],
        )

        _external_api_duration = Histogram(
            "external_api_duration_seconds",
            "External API call latency in seconds",
            ["service", "operation"],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0],
        )

        # Sprint 49 Phase B: Action metrics
        _action_exec_total = Counter(
            "action_exec_total",
            "Total action executions by provider, action, and status",
            ["provider", "action", "status"],
        )

        _action_latency_seconds = Histogram(
            "action_latency_seconds",
            "Action execution latency in seconds",
            ["provider", "action"],
            buckets=[0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0],
        )

        _action_error_total = Counter(
            "action_error_total",
            "Total action errors by provider, action, and reason",
            ["provider", "action", "reason"],
        )

        _METRICS_INITIALIZED = True
        _LOG.info("Prometheus metrics initialized (port configured via PROM_EXPORT_PORT, default 9090)")

    except ImportError:
        _LOG.warning(
            "prometheus-client not installed; telemetry will be no-op. "
            "Install with: pip install djp-workflow[observability]"
        )
        _PROM_AVAILABLE = False


def record_http_request(method: str, endpoint: str, status_code: int, duration_seconds: float) -> None:
    """Record HTTP request metrics.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: Endpoint path (e.g., /api/workflows)
        status_code: HTTP status code (200, 404, etc.)
        duration_seconds: Request duration in seconds
    """
    if not _PROM_AVAILABLE or not _METRICS_INITIALIZED:
        return

    try:
        _http_request_duration.labels(method=method, endpoint=endpoint, status_code=status_code).observe(
            duration_seconds
        )
        _http_requests_total.labels(method=method, endpoint=endpoint, status_code=status_code).inc()
    except Exception as exc:
        _LOG.warning("Failed to record HTTP request metric: %s", exc)


def record_queue_job(job_type: str, duration_seconds: float) -> None:
    """Record background job metrics.

    Args:
        job_type: Type of job (e.g., workflow_run, batch_publish)
        duration_seconds: Job processing time in seconds
    """
    if not _PROM_AVAILABLE or not _METRICS_INITIALIZED:
        return

    try:
        _queue_job_latency.labels(job_type=job_type).observe(duration_seconds)
    except Exception as exc:
        _LOG.warning("Failed to record queue job metric: %s", exc)


def set_queue_depth(queue_name: str, depth: int) -> None:
    """Set current queue depth gauge.

    Args:
        queue_name: Name of the queue (e.g., batch_runner)
        depth: Current number of jobs in queue
    """
    if not _PROM_AVAILABLE or not _METRICS_INITIALIZED:
        return

    try:
        _queue_depth.labels(queue_name=queue_name).set(depth)
    except Exception as exc:
        _LOG.warning("Failed to set queue depth metric: %s", exc)


def record_external_api_call(service: str, operation: str, duration_seconds: float) -> None:
    """Record external API call metrics.

    Args:
        service: Service name (outlook, teams, slack, etc.)
        operation: Operation name (send_message, fetch_emails, etc.)
        duration_seconds: API call duration in seconds
    """
    if not _PROM_AVAILABLE or not _METRICS_INITIALIZED:
        return

    try:
        _external_api_calls.labels(service=service, operation=operation).inc()
        _external_api_duration.labels(service=service, operation=operation).observe(duration_seconds)
    except Exception as exc:
        _LOG.warning("Failed to record external API metric: %s", exc)


class TimerContext:
    """Context manager for timing operations.

    Example:
        with timer_context("my_operation") as timer:
            # do work
            pass
        print(f"Operation took {timer.elapsed_seconds}s")
    """

    def __init__(self, label: str = "operation"):
        self.label = label
        self.start_time: float | None = None
        self.elapsed_seconds: float = 0.0

    def __enter__(self) -> TimerContext:
        self.start_time = time.perf_counter()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        if self.start_time is not None:
            self.elapsed_seconds = time.perf_counter() - self.start_time


def timer_context(label: str = "operation") -> TimerContext:
    """Create a timer context manager.

    Args:
        label: Label for the operation being timed

    Returns:
        TimerContext instance
    """
    return TimerContext(label)


# Sprint 49 Phase B: Action metrics recording


def record_action_execution(provider: str, action: str, status: str, duration_seconds: float) -> None:
    """Record action execution metrics.

    Args:
        provider: Provider name (independent, microsoft, google)
        action: Action ID (e.g., webhook.save)
        status: Execution status (success, failed)
        duration_seconds: Execution duration in seconds
    """
    if not _PROM_AVAILABLE or not _METRICS_INITIALIZED:
        return

    try:
        _action_exec_total.labels(provider=provider, action=action, status=status).inc()
        _action_latency_seconds.labels(provider=provider, action=action).observe(duration_seconds)
    except Exception as exc:
        _LOG.warning("Failed to record action execution metric: %s", exc)


def record_action_error(provider: str, action: str, reason: str) -> None:
    """Record action error metrics.

    Args:
        provider: Provider name (independent, microsoft, google)
        action: Action ID (e.g., webhook.save)
        reason: Error reason (e.g., timeout, invalid_params)
    """
    if not _PROM_AVAILABLE or not _METRICS_INITIALIZED:
        return

    try:
        _action_error_total.labels(provider=provider, action=action, reason=reason).inc()
    except Exception as exc:
        _LOG.warning("Failed to record action error metric: %s", exc)


def generate_metrics_text() -> str:
    """Generate Prometheus metrics in text exposition format.

    Returns:
        Metrics text in Prometheus format, or empty string if disabled
    """
    if not _PROM_AVAILABLE or not _METRICS_INITIALIZED:
        return ""

    try:
        from prometheus_client import REGISTRY, generate_latest

        return generate_latest(REGISTRY).decode("utf-8")
    except Exception as exc:
        _LOG.error("Failed to generate metrics: %s", exc)
        return f"# Error generating metrics: {exc}\n"
