"""FastAPI middleware for automatic HTTP request telemetry.

Sprint 46: Automatic instrumentation for HTTP endpoints (Prometheus metrics).
Sprint 47: Added OpenTelemetry tracing integration.

This middleware automatically tracks HTTP request latency and counts,
feeding data to the Prometheus exporter and OTel tracer. It's safe-by-default:
if telemetry is disabled, the middleware adds negligible overhead (~0.1ms per request).
"""

from __future__ import annotations

import logging
import time
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

_LOG = logging.getLogger(__name__)


class TelemetryMiddleware(BaseHTTPMiddleware):
    """FastAPI middleware for automatic HTTP telemetry.

    Tracks request latency and counts for all HTTP endpoints.
    Safe to install even when telemetry is disabled (minimal overhead).
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and record metrics + traces.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response from downstream handler
        """
        # Import here to avoid circular dependencies and support lazy loading
        from src.telemetry.otel import start_span
        from src.telemetry.prom import record_http_request

        start_time = time.perf_counter()
        response = None
        status_code = 500  # Default to 500 if exception occurs

        # Normalize endpoint path to avoid cardinality explosion
        # /api/workflows/abc123 -> /api/workflows/{id}
        endpoint = self._normalize_endpoint(request.url.path)

        # Sprint 47: Wrap request in OTel span
        with start_span(
            "http.server",
            {
                "http.method": request.method,
                "http.route": endpoint,
                "http.target": request.url.path,
                "http.scheme": request.url.scheme,
            },
        ) as span:
            try:
                response = await call_next(request)
                status_code = response.status_code
                span.set_attribute("http.status_code", status_code)
                return response
            except Exception as exc:
                span.set_attribute("http.status_code", 500)
                _LOG.error("Exception in request handler: %s", exc, exc_info=True)
                raise
            finally:
                duration_seconds = time.perf_counter() - start_time
                span.set_attribute("http.duration_seconds", duration_seconds)

                # Record Prometheus metrics (no-op if telemetry disabled)
                record_http_request(
                    method=request.method,
                    endpoint=endpoint,
                    status_code=status_code,
                    duration_seconds=duration_seconds,
                )

    @staticmethod
    def _normalize_endpoint(path: str) -> str:
        """Normalize endpoint path to avoid high cardinality.

        Replace UUIDs and IDs with placeholders to keep metric labels bounded.

        Args:
            path: Raw URL path

        Returns:
            Normalized path with ID placeholders
        """
        import re

        # Replace UUID-like segments with {id}
        path = re.sub(r"/[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}", "/{id}", path, flags=re.I)

        # Replace numeric IDs with {id}
        path = re.sub(r"/\d+", "/{id}", path)

        # Replace tenant IDs (pattern: tenant-*)
        path = re.sub(r"/tenant-[a-zA-Z0-9_-]+", "/tenant-{id}", path)

        return path
