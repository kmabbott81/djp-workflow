"""OpenTelemetry tracing for DJP Workflow.

Sprint 47: Phase 2 (Tracing) implementation.

This module provides OpenTelemetry tracing behind the TELEMETRY_ENABLED flag.
All instrumentation is safe-by-default: if the flag is false or OTel deps
are not installed, all operations become no-ops.

Exporters:
- console: Print spans to stdout (for local dev/CI smoke tests)
- otlp: Send spans to OTLP endpoint (Jaeger, Tempo, etc.)
- none: No export (tracing disabled)
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any

_LOG = logging.getLogger(__name__)

# Lazy imports - only load OTel if telemetry is enabled
_OTEL_AVAILABLE = False
_TRACER_INITIALIZED = False
_TRACER: Any | None = None


def _is_enabled() -> bool:
    """Check if OTel tracing is enabled via environment variables."""
    enabled = str(os.getenv("TELEMETRY_ENABLED", "false")).lower() in {"1", "true", "yes"}
    backend = os.getenv("TELEMETRY_BACKEND", "noop").lower()
    return enabled and backend in {"otel", "hybrid"}


def init_tracer(service_name: str | None = None) -> None:
    """Initialize OpenTelemetry tracer if enabled.

    Environment variables:
    - TELEMETRY_ENABLED: Enable/disable telemetry (default: false)
    - TELEMETRY_BACKEND: Backend to use (otel|hybrid, default: noop)
    - OTEL_EXPORTER: Exporter type (console|otlp|none, default: console)
    - OTEL_ENDPOINT: OTLP endpoint URL (e.g., http://tempo:4317)
    - OTEL_SERVICE_NAME: Service name for traces (default: djp-workflow)
    - OTEL_TRACE_SAMPLE: Sample rate (0.0-1.0, default: 0.02)

    Safe to call multiple times (idempotent). If TELEMETRY_ENABLED=false
    or OTel deps are not installed, this becomes a no-op.

    Args:
        service_name: Override service name (default: OTEL_SERVICE_NAME env var)
    """
    global _OTEL_AVAILABLE, _TRACER_INITIALIZED, _TRACER

    if not _is_enabled():
        _LOG.debug("OTel tracing disabled (TELEMETRY_ENABLED=false or backend!=otel)")
        return

    if _TRACER_INITIALIZED:
        _LOG.debug("OTel tracer already initialized")
        return

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
        from opentelemetry.sdk.trace.sampling import ParentBasedTraceIdRatio

        _OTEL_AVAILABLE = True

        # Get configuration
        service = service_name or os.getenv("OTEL_SERVICE_NAME", "djp-workflow")
        exporter_type = os.getenv("OTEL_EXPORTER", "console").lower()
        sample_rate = float(os.getenv("OTEL_TRACE_SAMPLE", "0.02"))

        # Create resource
        resource = Resource.create(
            {
                "service.name": service,
                "service.version": "1.0.2",
                "deployment.environment": os.getenv("ENV", "dev"),
            }
        )

        # Create sampler (parent-based with trace ID ratio)
        sampler = ParentBasedTraceIdRatio(sample_rate)

        # Create tracer provider
        provider = TracerProvider(resource=resource, sampler=sampler)

        # Add exporter
        if exporter_type == "console":
            exporter = ConsoleSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(exporter))
            _LOG.info("OTel tracer initialized: exporter=console, sample_rate=%.2f", sample_rate)

        elif exporter_type == "otlp":
            endpoint = os.getenv("OTEL_ENDPOINT")
            if not endpoint:
                _LOG.warning("OTEL_EXPORTER=otlp but OTEL_ENDPOINT not set, using console")
                exporter = ConsoleSpanExporter()
                provider.add_span_processor(BatchSpanProcessor(exporter))
            else:
                try:
                    # Auto-detect gRPC vs HTTP based on endpoint
                    if endpoint.endswith(":4317") or "/v1/traces" not in endpoint:
                        # gRPC endpoint
                        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

                        exporter = OTLPSpanExporter(endpoint=endpoint)
                    else:
                        # HTTP endpoint
                        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

                        exporter = OTLPSpanExporter(endpoint=endpoint)

                    provider.add_span_processor(BatchSpanProcessor(exporter))
                    _LOG.info(
                        "OTel tracer initialized: exporter=otlp, endpoint=%s, sample_rate=%.2f",
                        endpoint,
                        sample_rate,
                    )
                except ImportError as exc:
                    _LOG.error("OTLP exporter not available: %s. Install: pip install opentelemetry-exporter-otlp", exc)
                    exporter = ConsoleSpanExporter()
                    provider.add_span_processor(BatchSpanProcessor(exporter))

        elif exporter_type == "none":
            _LOG.info("OTel tracer initialized: exporter=none (tracing disabled)")
        else:
            _LOG.warning("Unknown OTEL_EXPORTER '%s', using console", exporter_type)
            exporter = ConsoleSpanExporter()
            provider.add_span_processor(BatchSpanProcessor(exporter))

        # Set as global tracer provider
        trace.set_tracer_provider(provider)
        _TRACER = trace.get_tracer(__name__)

        _TRACER_INITIALIZED = True

    except ImportError as exc:
        _LOG.warning(
            "OpenTelemetry not installed; tracing will be no-op. "
            "Install with: pip install djp-workflow[observability]. Error: %s",
            exc,
        )
        _OTEL_AVAILABLE = False


def get_tracer() -> Any | None:
    """Get the global tracer instance.

    Returns:
        Tracer instance, or None if not initialized
    """
    return _TRACER


def get_current_trace_id() -> str:
    """Get current trace ID as hex string.

    Returns:
        Trace ID (32-char hex), or empty string if no active span
    """
    if not _OTEL_AVAILABLE or not _TRACER_INITIALIZED:
        return ""

    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            return format(span.get_span_context().trace_id, "032x")
    except Exception as exc:
        _LOG.debug("Failed to get trace ID: %s", exc)

    return ""


def get_current_span_id() -> str:
    """Get current span ID as hex string.

    Returns:
        Span ID (16-char hex), or empty string if no active span
    """
    if not _OTEL_AVAILABLE or not _TRACER_INITIALIZED:
        return ""

    try:
        from opentelemetry import trace

        span = trace.get_current_span()
        if span and span.get_span_context().is_valid:
            return format(span.get_span_context().span_id, "016x")
    except Exception as exc:
        _LOG.debug("Failed to get span ID: %s", exc)

    return ""


@contextmanager
def start_span(name: str, attributes: dict[str, Any] | None = None):
    """Context manager to create and manage a span.

    Args:
        name: Span name (e.g., "http.server", "job.run", "external.api.call")
        attributes: Span attributes (e.g., {"http.method": "GET", "http.status_code": 200})

    Yields:
        Span instance (or no-op object if tracing disabled)

    Example:
        with start_span("external.api.call", {"service": "outlook", "operation": "fetch_emails"}) as span:
            # Make API call
            span.set_attribute("response.count", 10)
    """
    if not _OTEL_AVAILABLE or not _TRACER_INITIALIZED or _TRACER is None:
        # No-op span
        class NoOpSpan:
            def set_attribute(self, key: str, value: Any) -> None:
                pass

            def set_status(self, status: Any) -> None:
                pass

            def record_exception(self, exc: Exception) -> None:
                pass

        yield NoOpSpan()
        return

    try:
        from opentelemetry.trace import Status, StatusCode

        with _TRACER.start_as_current_span(name) as span:
            # Set attributes
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)

            try:
                yield span
            except Exception as exc:
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                span.record_exception(exc)
                raise

    except Exception as exc:
        _LOG.warning("Failed to create span '%s': %s", name, exc)

        # Yield no-op span to avoid breaking caller
        class NoOpSpan:
            def set_attribute(self, key: str, value: Any) -> None:
                pass

            def set_status(self, status: Any) -> None:
                pass

            def record_exception(self, exc: Exception) -> None:
                pass

        yield NoOpSpan()


def record_http_span(method: str, route: str, status_code: int, duration_seconds: float) -> None:
    """Record an HTTP request span.

    This is a convenience function for recording HTTP spans without needing
    to manually create a span context. Useful for middleware integration.

    Args:
        method: HTTP method (GET, POST, etc.)
        route: Route path (e.g., /api/workflows)
        status_code: HTTP status code
        duration_seconds: Request duration in seconds
    """
    if not _OTEL_AVAILABLE or not _TRACER_INITIALIZED:
        return

    try:
        with start_span(
            "http.server",
            {
                "http.method": method,
                "http.route": route,
                "http.status_code": status_code,
                "http.duration_seconds": duration_seconds,
            },
        ):
            pass  # Span is automatically closed
    except Exception as exc:
        _LOG.warning("Failed to record HTTP span: %s", exc)


def record_job_span(queue_name: str, job_type: str, duration_seconds: float, success: bool = True) -> None:
    """Record a background job span.

    Args:
        queue_name: Queue name (e.g., batch_runner)
        job_type: Job type (e.g., workflow_run)
        duration_seconds: Job duration in seconds
        success: Whether job completed successfully
    """
    if not _OTEL_AVAILABLE or not _TRACER_INITIALIZED:
        return

    try:
        from opentelemetry.trace import Status, StatusCode

        with start_span(
            "job.run",
            {
                "queue.name": queue_name,
                "job.type": job_type,
                "job.duration_seconds": duration_seconds,
                "job.success": success,
            },
        ) as span:
            if not success:
                span.set_status(Status(StatusCode.ERROR, "Job failed"))
    except Exception as exc:
        _LOG.warning("Failed to record job span: %s", exc)


def record_external_api_span(service: str, operation: str, duration_seconds: float, success: bool = True) -> None:
    """Record an external API call span.

    Args:
        service: Service name (outlook, teams, slack, etc.)
        operation: Operation name (fetch_emails, send_message, etc.)
        duration_seconds: API call duration in seconds
        success: Whether call completed successfully
    """
    if not _OTEL_AVAILABLE or not _TRACER_INITIALIZED:
        return

    try:
        from opentelemetry.trace import Status, StatusCode

        with start_span(
            "external.api.call",
            {
                "external.service": service,
                "external.operation": operation,
                "external.duration_seconds": duration_seconds,
                "external.success": success,
            },
        ) as span:
            if not success:
                span.set_status(Status(StatusCode.ERROR, "External API call failed"))
    except Exception as exc:
        _LOG.warning("Failed to record external API span: %s", exc)
