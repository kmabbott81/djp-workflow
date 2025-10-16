"""Test utilities for metrics registry and environment isolation (Sprint 59 S59-02).

This module provides helpers for clean test fixture initialization, registry bootstrap,
and environment variable management without polluting other tests.
"""

from typing import Optional


def init_test_registry():
    """Bootstrap Prometheus registry for test isolation.

    Clears existing metrics and re-initializes telemetry with a clean state.
    Must be called AFTER test starts (not at import time) to avoid singleton issues.

    Returns:
        None (modifies global prom state)
    """
    try:
        # Import locally to avoid module-level registration
        from prometheus_client import REGISTRY

        # Unregister all collectors from existing registry
        collectors = list(REGISTRY._collector_to_names.keys())
        for collector in collectors:
            try:
                REGISTRY.unregister(collector)
            except Exception:
                pass  # Already unregistered or not ours

        # Re-initialize telemetry with clean registry
        from src.telemetry import prom

        prom._PROM_AVAILABLE = False
        prom._METRICS_INITIALIZED = False
        prom.init_prometheus()

    except ImportError:
        pass  # Telemetry not available in test environment


def set_workspace_env(
    monkeypatch,
    label: str = "off",
    allowlist: Optional[str] = None,
) -> None:
    """Set workspace metrics environment variables for test isolation.

    Args:
        monkeypatch: pytest monkeypatch fixture
        label: METRICS_WORKSPACE_LABEL value ("on" or "off", default "off")
        allowlist: METRICS_WORKSPACE_ALLOWLIST value (comma-separated, optional)
    """
    monkeypatch.setenv("METRICS_WORKSPACE_LABEL", label)
    if allowlist:
        monkeypatch.setenv("METRICS_WORKSPACE_ALLOWLIST", allowlist)
    else:
        monkeypatch.delenv("METRICS_WORKSPACE_ALLOWLIST", raising=False)
