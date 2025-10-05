"""Logging integration for trace correlation.

Sprint 47: Add trace_id to structured logs.

This module provides a logging filter that injects trace_id from the current
OTel span context into log records. This enables correlating logs with traces
in observability backends (Grafana, Datadog, etc.).
"""

from __future__ import annotations

import logging


class TraceIdFilter(logging.Filter):
    """Logging filter to inject trace_id into log records.

    Adds 'trace_id' field to all log records when OTel tracing is enabled
    and there's an active span. If no active span, trace_id will be empty string.

    Usage:
        import logging
        from src.telemetry.log_correlation import TraceIdFilter

        logger = logging.getLogger(__name__)
        logger.addFilter(TraceIdFilter())

        # Logs will automatically include trace_id field
        logger.info("Processing request", extra={"user_id": "123"})
        # Output: {"message": "Processing request", "trace_id": "abc123...", "user_id": "123"}
    """

    def filter(self, record: logging.LogRecord) -> bool:
        """Add trace_id to log record.

        Args:
            record: Log record to modify

        Returns:
            True (always pass through the record)
        """
        # Import here to avoid circular dependencies
        from src.telemetry.otel import get_current_trace_id

        # Add trace_id to record (empty string if no active span)
        record.trace_id = get_current_trace_id()

        return True


def install_trace_correlation() -> None:
    """Install trace correlation for all loggers.

    This function adds the TraceIdFilter to the root logger, so all
    loggers in the application will automatically include trace_id in
    their log records.

    Safe to call multiple times (idempotent).
    """
    root_logger = logging.getLogger()

    # Check if filter already installed
    for filt in root_logger.filters:
        if isinstance(filt, TraceIdFilter):
            return

    # Add filter to root logger
    root_logger.addFilter(TraceIdFilter())


def get_structured_log_context() -> dict[str, str]:
    """Get current trace context for structured logging.

    Returns:
        Dictionary with trace_id and span_id (if available)

    Example:
        import logging
        from src.telemetry.log_correlation import get_structured_log_context

        logger = logging.getLogger(__name__)
        logger.info("Processing request", extra=get_structured_log_context())
    """
    from src.telemetry.otel import get_current_span_id, get_current_trace_id

    context = {}

    trace_id = get_current_trace_id()
    if trace_id:
        context["trace_id"] = trace_id

    span_id = get_current_span_id()
    if span_id:
        context["span_id"] = span_id

    return context
