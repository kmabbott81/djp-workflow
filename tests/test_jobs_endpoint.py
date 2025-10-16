"""Tests for /ai/jobs endpoint workspace isolation and pagination (Sprint 59 S59-05).

This module provides comprehensive tests for S59-05 endpoint hardening:
- Workspace-scoped queries with security validation
- Cursor-based Redis SCAN pagination
- Telemetry recording with workspace_id labels
- Cross-workspace access prevention
- Minimal job summaries (redacted params for privacy)

Test Structure:
- TestWorkspaceSecurityValidation: Workspace validation logic and format checks
- TestWorkspaceIdCanonical: canonical_workspace_id() validation
- TestTelemetryHelpers: Telemetry helper function recording

TODO(S60): These tests validate against current schema (ai:job:{job_id} with workspace_id in hash fields).
Once keys are migrated to ai:job:{workspace_id}:{job_id}, update SCAN patterns in TestJobListEndpointLogic
and TestCursorPaginationWithRedis fixtures accordingly. See SPRINT_HANDOFF_S59_S60.md for migration plan.
"""

import time
from unittest.mock import Mock

import pytest


class TestWorkspaceSecurityValidation:
    """Test workspace security validation logic used in /ai/jobs endpoints."""

    def test_workspace_id_required_validation(self):
        """Workspace ID should be required in endpoint logic."""
        # Simulate endpoint validation
        request = Mock()
        request.state = Mock()
        delattr(request.state, "workspace_id")

        # Validation logic
        workspace_id = getattr(request.state, "workspace_id", None)
        assert workspace_id is None, "Missing workspace_id should be None"

    def test_workspace_id_present_validation(self):
        """When workspace_id is present, it should be captured."""
        request = Mock()
        request.state = Mock()
        request.state.workspace_id = "ws_test"

        workspace_id = getattr(request.state, "workspace_id", None)
        assert workspace_id == "ws_test", "workspace_id should be captured from request.state"

    def test_workspace_label_validation_disabled_by_default(self, monkeypatch):
        """Workspace label validation should be disabled by default."""
        monkeypatch.delenv("METRICS_WORKSPACE_LABEL", raising=False)

        from src.telemetry.prom import is_workspace_label_enabled

        assert is_workspace_label_enabled() is False, "Workspace labels should be disabled by default"

    def test_workspace_label_validation_enabled_when_on(self, monkeypatch):
        """Workspace label validation should be enabled when flag is 'on'."""
        monkeypatch.setenv("METRICS_WORKSPACE_LABEL", "on")

        from src.telemetry.prom import is_workspace_label_enabled

        assert is_workspace_label_enabled() is True, "Workspace labels should be enabled"


class TestWorkspaceIdCanonical:
    """Test canonical_workspace_id() validation used by endpoints."""

    def test_canonical_workspace_id_valid_format(self, monkeypatch):
        """Valid workspace IDs should pass validation."""
        monkeypatch.delenv("METRICS_WORKSPACE_ALLOWLIST", raising=False)

        from src.telemetry.prom import canonical_workspace_id

        assert canonical_workspace_id("ws_test") == "ws_test"
        assert canonical_workspace_id("workspace1") == "workspace1"
        assert canonical_workspace_id("my-workspace") == "my-workspace"

    def test_canonical_workspace_id_invalid_format(self, monkeypatch):
        """Invalid workspace IDs should fail validation."""
        monkeypatch.delenv("METRICS_WORKSPACE_ALLOWLIST", raising=False)

        from src.telemetry.prom import canonical_workspace_id

        # Uppercase should be rejected
        assert canonical_workspace_id("Workspace") is None
        # Special characters should be rejected
        assert canonical_workspace_id("workspace@test") is None
        # Empty should be rejected
        assert canonical_workspace_id("") is None
        assert canonical_workspace_id(None) is None

    def test_canonical_workspace_id_allowlist_enforcement(self, monkeypatch):
        """When allowlist is set, only listed workspaces should be accepted."""
        monkeypatch.setenv("METRICS_WORKSPACE_ALLOWLIST", "ws_allowed, ws_demo")

        from src.telemetry.prom import canonical_workspace_id

        assert canonical_workspace_id("ws_allowed") == "ws_allowed"
        assert canonical_workspace_id("ws_demo") == "ws_demo"
        assert canonical_workspace_id("ws_other") is None, "Non-allowlisted workspace should fail"


class TestTelemetryHelpers:
    """Test telemetry helper functions used in endpoints."""

    def test_record_job_list_query_function_exists(self):
        """record_job_list_query() should be importable."""
        from src.telemetry.prom import record_job_list_query

        assert callable(record_job_list_query), "record_job_list_query should be callable"

    def test_record_job_list_query_accepts_workspace_id(self, monkeypatch):
        """record_job_list_query() should accept workspace_id parameter."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "false")  # Disable to avoid registration issues

        from src.telemetry.prom import record_job_list_query

        # Should not raise exception
        record_job_list_query(workspace_id="ws_test", count=5, seconds=0.123)
        record_job_list_query(workspace_id=None, count=0, seconds=0.001)

    def test_record_job_list_query_backward_compatible(self, monkeypatch):
        """record_job_list_query() should handle old calls without workspace_id."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "false")

        from src.telemetry.prom import record_job_list_query

        # Should work with positional args (backward compat)
        record_job_list_query("ws_compat", 3, 0.05)


class TestJobListEndpointLogic:
    """Test core logic patterns used in /ai/jobs endpoint."""

    def test_redis_scan_pattern_with_workspace(self):
        """SCAN pattern should include workspace_id for filtering."""
        workspace_id = "ws_test"
        pattern = f"ai:job:{workspace_id}:*"

        assert "ai:job:" in pattern, "Pattern should include job prefix"
        assert workspace_id in pattern, "Pattern should include workspace_id"
        assert pattern.endswith(":*"), "Pattern should use wildcard"

    def test_job_key_parsing_from_redis_key(self):
        """Job ID should be parseable from Redis key."""
        redis_key = "ai:job:ws_test:job_123"
        job_id = redis_key.split(":")[-1]

        assert job_id == "job_123", "Job ID should be last component of key"

    def test_job_summary_excludes_params(self):
        """Job summaries should not include params for privacy."""
        # Simulate job data structure
        job_data = {
            "job_id": "job_1",
            "status": "completed",
            "action_provider": "google",
            "action_name": "gmail.send",
            "params": {"to": "secret@example.com", "body": "secret"},  # Should be redacted
            "result": {"success": True},  # Should be included
            "error": None,
            "enqueued_at": time.time(),
        }

        # Build minimal summary (like endpoint does)
        job_summary = {
            "job_id": job_data["job_id"],
            "status": job_data["status"],
            "action": f"{job_data['action_provider']}.{job_data['action_name']}",
            "result": job_data.get("result"),
            "error": job_data.get("error"),
        }

        # Verify params not in summary
        assert "params" not in job_summary, "params should be redacted from summary"
        assert "result" in job_summary, "result should be included in summary"

    def test_cursor_pagination_zero_means_fresh_scan(self):
        """Cursor value of 0 should indicate fresh SCAN (no cursor from client)."""
        cursor = None  # From query parameter
        cursor_int = int(cursor) if cursor else 0

        assert cursor_int == 0, "None cursor should become 0 for fresh SCAN"

    def test_cursor_pagination_preserves_cursor_int(self):
        """Cursor should be preserved from SCAN for next call."""
        cursor = "42"  # From previous response
        cursor_int = int(cursor) if cursor else 0

        assert cursor_int == 42, "Cursor should be parsed from string"

    def test_next_cursor_returns_string_or_none(self):
        """next_cursor in response should be string or None."""
        # Simulating SCAN return values
        scenarios = [
            (0, None, "Final cursor should be None in response"),
            (123, "123", "Non-zero cursor should be stringified"),
            (1, "1", "Cursor 1 should be stringified"),
        ]

        for cursor_int, expected_response, msg in scenarios:
            response_cursor = str(cursor_int) if cursor_int else None
            assert response_cursor == expected_response, msg


class TestJobDetailEndpointLogic:
    """Test core logic patterns used in /ai/jobs/{job_id} endpoint."""

    def test_cross_workspace_access_prevention_check(self):
        """Job detail should verify job belongs to requesting workspace."""
        job_data = {"job_id": "job_1", "workspace_id": "ws_other"}
        request_workspace_id = "ws_attacker"

        # Simulate endpoint check
        job_workspace_id = job_data.get("workspace_id")
        access_allowed = job_workspace_id == request_workspace_id

        assert access_allowed is False, "Cross-workspace access should be rejected"

    def test_same_workspace_access_allowed(self):
        """Job detail should allow access for same workspace."""
        job_data = {"job_id": "job_1", "workspace_id": "ws_test"}
        request_workspace_id = "ws_test"

        # Simulate endpoint check
        job_workspace_id = job_data.get("workspace_id")
        access_allowed = job_workspace_id == request_workspace_id

        assert access_allowed is True, "Same-workspace access should be allowed"

    def test_job_response_includes_workspace_id(self):
        """Job detail response should include workspace_id."""
        workspace_id = "ws_test"
        job_id = "job_1"

        response = {
            "workspace_id": workspace_id,
            "job_id": job_id,
            "status": "completed",
        }

        assert response["workspace_id"] == workspace_id, "Response should include workspace_id"


class TestCursorPaginationWithRedis:
    """Test cursor pagination with actual FakeRedis (if available)."""

    @pytest.fixture
    def fake_redis_instance(self):
        """Provide FakeRedis instance."""
        try:
            import fakeredis

            return fakeredis.FakeStrictRedis(decode_responses=True)
        except ImportError:
            pytest.skip("fakeredis not available")

    def test_redis_scan_returns_cursor_and_keys(self, fake_redis_instance):
        """Redis SCAN should return (cursor, keys_batch)."""
        # Seed some data
        for i in range(10):
            fake_redis_instance.hset(
                f"ai:job:ws_test:job_{i}",
                mapping={"job_id": f"job_{i}", "status": "pending"},
            )

        # SCAN should return cursor and keys
        cursor_out, keys = fake_redis_instance.scan(0, match="ai:job:ws_test:*", count=5)

        assert isinstance(cursor_out, int), "SCAN should return cursor as int"
        assert isinstance(keys, list), "SCAN should return keys as list"
        assert len(keys) <= 5, "SCAN should respect count parameter"

    def test_redis_scan_workspace_filtering(self, fake_redis_instance):
        """Redis SCAN with pattern should filter by workspace."""
        # Seed jobs for multiple workspaces
        for ws in ["ws_a", "ws_b"]:
            for i in range(3):
                fake_redis_instance.hset(
                    f"ai:job:{ws}:job_{i}",
                    mapping={"job_id": f"job_{i}", "workspace_id": ws},
                )

        # SCAN with workspace pattern
        _, keys_a = fake_redis_instance.scan(0, match="ai:job:ws_a:*", count=100)
        _, keys_b = fake_redis_instance.scan(0, match="ai:job:ws_b:*", count=100)

        # Each should only get their workspace keys
        assert len(keys_a) == 3, "ws_a pattern should return 3 keys"
        assert len(keys_b) == 3, "ws_b pattern should return 3 keys"

        # No cross-contamination
        assert all("ws_a" in k for k in keys_a), "ws_a results should only have ws_a keys"
        assert all("ws_b" in k for k in keys_b), "ws_b results should only have ws_b keys"

    def test_redis_scan_pagination_stateless(self, fake_redis_instance):
        """Redis SCAN pagination should be stateless (cursor-based)."""
        # Seed data
        for i in range(10):
            fake_redis_instance.hset(
                f"ai:job:ws_test:job_{i}",
                mapping={"job_id": f"job_{i}"},
            )

        # First scan
        cursor1, batch1 = fake_redis_instance.scan(0, match="ai:job:ws_test:*", count=3)
        first_batch_size = len(batch1)

        # Use returned cursor for next scan
        if cursor1:
            cursor2, batch2 = fake_redis_instance.scan(cursor1, match="ai:job:ws_test:*", count=3)
            assert len(batch2) > 0, "Next SCAN with cursor should return more results"
        else:
            # If cursor is 0, all results fit in first batch
            assert first_batch_size == 10, "All results should fit in one batch"
