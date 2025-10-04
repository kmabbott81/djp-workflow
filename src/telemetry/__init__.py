"""Telemetry module for observability (noop by default).

Sprint 46: Factory pattern for backend selection.

Backends:
- noop: No-op (default when TELEMETRY_ENABLED=false)
- prom: Prometheus metrics (TELEMETRY_BACKEND=prom)
- otel: OpenTelemetry traces (TELEMETRY_BACKEND=otel, Sprint 47+)
"""
from __future__ import annotations

import logging
import os

_LOG = logging.getLogger(__name__)


def init_telemetry() -> None:
    """Initialize telemetry backend based on environment configuration.

    Environment variables:
    - TELEMETRY_ENABLED: Enable/disable telemetry (default: false)
    - TELEMETRY_BACKEND: Backend to use (noop|prom|otel, default: noop)

    Safe to call multiple times (idempotent).
    """
    enabled = str(os.getenv("TELEMETRY_ENABLED", "false")).lower() in {"1", "true", "yes"}

    if not enabled:
        _LOG.debug("Telemetry disabled (TELEMETRY_ENABLED=false)")
        return

    backend = os.getenv("TELEMETRY_BACKEND", "noop").lower()

    if backend == "prom":
        from .prom import init_prometheus

        init_prometheus()
        _LOG.info("Telemetry initialized: backend=prometheus")

    elif backend == "otel":
        # Sprint 47: OpenTelemetry initialization
        _LOG.warning("OTel backend not yet implemented (Sprint 47), using noop")
        from .noop import init_noop_if_enabled

        init_noop_if_enabled()

    elif backend == "noop":
        from .noop import init_noop_if_enabled

        init_noop_if_enabled()

    else:
        _LOG.warning("Unknown telemetry backend '%s', using noop", backend)
        from .noop import init_noop_if_enabled

        init_noop_if_enabled()


# Backwards compatibility: keep old function name
def init_noop_if_enabled() -> None:
    """Deprecated: Use init_telemetry() instead.

    This function is kept for backwards compatibility with Sprint 42 code.
    """
    from .noop import init_noop_if_enabled as _noop_init

    _noop_init()


__all__ = ["init_telemetry", "init_noop_if_enabled"]
