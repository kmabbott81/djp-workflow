"""Telemetry module for observability (noop by default)."""
from __future__ import annotations

from .noop import init_noop_if_enabled

__all__ = ["init_noop_if_enabled"]
