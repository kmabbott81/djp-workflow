"""FastAPI middleware for automatic HTTP request telemetry.

Sprint 46: Automatic instrumentation for HTTP endpoints.

This middleware automatically tracks HTTP request latency and counts,
feeding data to the Prometheus exporter. It's safe-by-default: if telemetry
is disabled, the middleware adds negligible overhead (~0.1ms per request).
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
        """Process request and record metrics.

        Args:
            request: FastAPI request object
            call_next: Next middleware/handler in chain

        Returns:
            Response from downstream handler
        """
        # Import here to avoid circular dependencies and support lazy loading
        from src.telemetry.prom import record_http_request

        start_time = time.perf_counter()
        response = None
        status_code = 500  # Default to 500 if exception occurs

        try:
            response = await call_next(request)
            status_code = response.status_code
            return response
        except Exception as exc:
            _LOG.error("Exception in request handler: %s", exc, exc_info=True)
            raise
        finally:
            duration_seconds = time.perf_counter() - start_time

            # Simplify endpoint path to avoid cardinality explosion
            # /api/workflows/abc123 -> /api/workflows/{id}
            endpoint = self._normalize_endpoint(request.url.path)

            # Record metrics (no-op if telemetry disabled)
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
