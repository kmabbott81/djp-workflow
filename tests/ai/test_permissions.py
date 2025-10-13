"""Unit tests for AI Orchestrator security permissions.

Sprint 55 Week 3: Test action allowlist enforcement.
"""

import os
from unittest.mock import patch

from src.security.permissions import can_execute


class TestPermissions:
    """Tests for action permission checks."""

    def test_allowed_action(self):
        """Allowed action passes permission check."""
        with patch.dict(os.environ, {"ALLOW_ACTIONS_DEFAULT": "gmail.send,outlook.send"}):
            assert can_execute("gmail.send") is True
            assert can_execute("outlook.send") is True

    def test_disallowed_action(self):
        """Disallowed action fails permission check."""
        with patch.dict(os.environ, {"ALLOW_ACTIONS_DEFAULT": "gmail.send"}):
            assert can_execute("system.shutdown") is False
            assert can_execute("rm -rf") is False

    def test_empty_allowlist(self):
        """Empty allowlist blocks all actions."""
        with patch.dict(os.environ, {"ALLOW_ACTIONS_DEFAULT": ""}):
            assert can_execute("gmail.send") is False

    def test_whitespace_handling(self):
        """Allowlist handles whitespace correctly."""
        with patch.dict(os.environ, {"ALLOW_ACTIONS_DEFAULT": " gmail.send , outlook.send "}):
            assert can_execute("gmail.send") is True
            assert can_execute("outlook.send") is True

    def test_case_sensitive(self):
        """Action matching is case-sensitive."""
        with patch.dict(os.environ, {"ALLOW_ACTIONS_DEFAULT": "gmail.send"}):
            assert can_execute("gmail.send") is True
            assert can_execute("GMAIL.SEND") is False
            assert can_execute("Gmail.Send") is False

    def test_default_allowlist(self):
        """Default allowlist includes common actions."""
        # Use the fixture's default
        assert can_execute("gmail.send") is True  # From fixture
        assert can_execute("outlook.send") is True  # From fixture
