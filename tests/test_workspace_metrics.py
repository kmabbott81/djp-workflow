"""Tests for workspace_id label support in Prometheus metrics (Sprint 59).

This module tests the workspace label plumbing, flag-gating, and allowlist enforcement
for multi-tenant metrics scoping without cardinality explosion.

Test Structure:
- TestWorkspaceLabelFlag: Environment flag behavior (disabled by default, enabled on demand)
- TestWorkspaceIdValidation: Format validation and allowlist enforcement
- TestRecordQueueJobWithWorkspace: Integration with record_queue_job()
- TestRecordActionExecutionWithWorkspace: Integration with record_action_execution()
"""

from src.telemetry import prom


class TestWorkspaceLabelFlag:
    """Test METRICS_WORKSPACE_LABEL flag behavior."""

    def test_flag_disabled_by_default(self, monkeypatch):
        """METRICS_WORKSPACE_LABEL should be off by default."""
        monkeypatch.delenv("METRICS_WORKSPACE_LABEL", raising=False)
        assert prom.is_workspace_label_enabled() is False

    def test_flag_enabled_when_on(self, monkeypatch):
        """METRICS_WORKSPACE_LABEL=on should enable workspace labels."""
        monkeypatch.setenv("METRICS_WORKSPACE_LABEL", "on")
        assert prom.is_workspace_label_enabled() is True

    def test_flag_disabled_when_off_explicit(self, monkeypatch):
        """METRICS_WORKSPACE_LABEL=off should disable workspace labels."""
        monkeypatch.setenv("METRICS_WORKSPACE_LABEL", "off")
        assert prom.is_workspace_label_enabled() is False

    def test_flag_case_insensitive(self, monkeypatch):
        """METRICS_WORKSPACE_LABEL=ON (uppercase) should enable workspace labels."""
        monkeypatch.setenv("METRICS_WORKSPACE_LABEL", "ON")
        assert prom.is_workspace_label_enabled() is True

    def test_flag_disabled_for_invalid_values(self, monkeypatch):
        """METRICS_WORKSPACE_LABEL with invalid values should be treated as off."""
        monkeypatch.setenv("METRICS_WORKSPACE_LABEL", "true")
        assert prom.is_workspace_label_enabled() is False

        monkeypatch.setenv("METRICS_WORKSPACE_LABEL", "1")
        assert prom.is_workspace_label_enabled() is False


class TestWorkspaceIdValidation:
    """Test canonical_workspace_id() format validation and allowlist enforcement."""

    def test_valid_workspace_id_format(self, monkeypatch):
        """Valid format: lowercase alphanumeric, underscores, hyphens (≤32 chars)."""
        monkeypatch.delenv("METRICS_WORKSPACE_ALLOWLIST", raising=False)

        assert prom.canonical_workspace_id("workspace1") == "workspace1"
        assert prom.canonical_workspace_id("my-workspace") == "my-workspace"
        assert prom.canonical_workspace_id("my_workspace") == "my_workspace"
        assert prom.canonical_workspace_id("0workspace") == "0workspace"

    def test_valid_max_length_workspace_id(self, monkeypatch):
        """workspace_id with exactly 32 chars should be valid."""
        monkeypatch.delenv("METRICS_WORKSPACE_ALLOWLIST", raising=False)
        ws_id = "a" + "b" * 30 + "c"  # 32 chars total
        assert len(ws_id) == 32
        assert prom.canonical_workspace_id(ws_id) == ws_id

    def test_invalid_empty_workspace_id(self):
        """Empty string should return None."""
        assert prom.canonical_workspace_id("") is None

    def test_invalid_none_workspace_id(self):
        """None should return None."""
        assert prom.canonical_workspace_id(None) is None

    def test_invalid_uppercase_workspace_id(self, monkeypatch, caplog):
        """Uppercase letters should be rejected."""
        monkeypatch.delenv("METRICS_WORKSPACE_ALLOWLIST", raising=False)
        assert prom.canonical_workspace_id("Workspace") is None
        assert "Invalid workspace_id format" in caplog.text

    def test_invalid_special_chars_workspace_id(self, monkeypatch, caplog):
        """Special characters (except - and _) should be rejected."""
        monkeypatch.delenv("METRICS_WORKSPACE_ALLOWLIST", raising=False)
        assert prom.canonical_workspace_id("workspace@test") is None
        assert prom.canonical_workspace_id("workspace.test") is None
        assert prom.canonical_workspace_id("workspace test") is None

    def test_invalid_leading_hyphen(self, monkeypatch):
        """workspace_id starting with hyphen should be rejected."""
        monkeypatch.delenv("METRICS_WORKSPACE_ALLOWLIST", raising=False)
        assert prom.canonical_workspace_id("-workspace") is None

    def test_invalid_leading_underscore(self, monkeypatch):
        """workspace_id starting with underscore should be rejected."""
        monkeypatch.delenv("METRICS_WORKSPACE_ALLOWLIST", raising=False)
        assert prom.canonical_workspace_id("_workspace") is None

    def test_invalid_exceeds_max_length(self, monkeypatch):
        """workspace_id exceeding 32 chars should be rejected."""
        monkeypatch.delenv("METRICS_WORKSPACE_ALLOWLIST", raising=False)
        ws_id = "a" * 33
        assert prom.canonical_workspace_id(ws_id) is None

    def test_allowlist_enforcement_single_workspace(self, monkeypatch, caplog):
        """When allowlist is set, only listed workspaces should be accepted."""
        monkeypatch.setenv("METRICS_WORKSPACE_ALLOWLIST", "workspace1")
        assert prom.canonical_workspace_id("workspace1") == "workspace1"
        assert prom.canonical_workspace_id("workspace2") is None
        assert "not in allowlist" in caplog.text

    def test_allowlist_enforcement_multiple_workspaces(self, monkeypatch):
        """Allowlist with comma-separated values should work correctly."""
        monkeypatch.setenv("METRICS_WORKSPACE_ALLOWLIST", "workspace1, workspace2, workspace3")
        assert prom.canonical_workspace_id("workspace1") == "workspace1"
        assert prom.canonical_workspace_id("workspace2") == "workspace2"
        assert prom.canonical_workspace_id("workspace3") == "workspace3"
        assert prom.canonical_workspace_id("workspace4") is None

    def test_allowlist_strips_whitespace(self, monkeypatch):
        """Allowlist parsing should handle whitespace around comma-separated values."""
        monkeypatch.setenv("METRICS_WORKSPACE_ALLOWLIST", "  workspace1  ,  workspace2  ")
        assert prom.canonical_workspace_id("workspace1") == "workspace1"
        assert prom.canonical_workspace_id("workspace2") == "workspace2"

    def test_allowlist_empty_entries_ignored(self, monkeypatch):
        """Allowlist parsing should skip empty entries."""
        monkeypatch.setenv("METRICS_WORKSPACE_ALLOWLIST", "workspace1,,workspace2,")
        assert prom.canonical_workspace_id("workspace1") == "workspace1"
        assert prom.canonical_workspace_id("workspace2") == "workspace2"

    def test_allowlist_not_set_all_valid_accepted(self, monkeypatch):
        """When allowlist is not set, all valid format workspace_ids should be accepted."""
        monkeypatch.delenv("METRICS_WORKSPACE_ALLOWLIST", raising=False)
        assert prom.canonical_workspace_id("workspace1") == "workspace1"
        assert prom.canonical_workspace_id("workspace2") == "workspace2"
        assert prom.canonical_workspace_id("any-valid-id") == "any-valid-id"

    def test_invalid_newline_injection(self, monkeypatch):
        """Newline injection should be rejected (prevents label injection)."""
        monkeypatch.delenv("METRICS_WORKSPACE_ALLOWLIST", raising=False)
        assert prom.canonical_workspace_id("workspace\n") is None
        assert prom.canonical_workspace_id("workspace\nmalicious") is None

    def test_invalid_null_byte_injection(self, monkeypatch):
        """Null byte injection should be rejected."""
        monkeypatch.delenv("METRICS_WORKSPACE_ALLOWLIST", raising=False)
        assert prom.canonical_workspace_id("workspace\x00") is None

    def test_invalid_prometheus_special_chars(self, monkeypatch):
        """Prometheus special characters should be rejected."""
        monkeypatch.delenv("METRICS_WORKSPACE_ALLOWLIST", raising=False)
        # Prometheus label reserved characters
        assert prom.canonical_workspace_id("workspace{test}") is None
        assert prom.canonical_workspace_id('workspace"test') is None
        assert prom.canonical_workspace_id("workspace=test") is None

    def test_invalid_control_characters(self, monkeypatch):
        """Control characters should be rejected."""
        monkeypatch.delenv("METRICS_WORKSPACE_ALLOWLIST", raising=False)
        assert prom.canonical_workspace_id("workspace\t") is None
        assert prom.canonical_workspace_id("workspace\r") is None
        assert prom.canonical_workspace_id("\tworkspace") is None


class TestRecordQueueJobWithWorkspace:
    """Test record_queue_job() with optional workspace_id parameter."""

    def test_record_queue_job_signature_accepts_workspace_id(self):
        """record_queue_job() should accept optional workspace_id parameter."""
        # This test verifies the function signature is correct
        # (actual implementation is tested via integration)
        import inspect

        sig = inspect.signature(prom.record_queue_job)
        assert "workspace_id" in sig.parameters
        assert sig.parameters["workspace_id"].default is None

    def test_record_queue_job_backward_compatible(self):
        """record_queue_job() should work without workspace_id (backward compatible)."""
        # Should not raise exception when called without workspace_id
        prom.record_queue_job("test_job", 1.5)

    def test_record_queue_job_with_workspace_id(self):
        """record_queue_job() should accept workspace_id when provided."""
        # Should not raise exception when called with workspace_id
        prom.record_queue_job("test_job", 1.5, workspace_id="workspace1")

    def test_record_queue_job_with_none_workspace_id(self):
        """record_queue_job() should handle None workspace_id gracefully."""
        # Should not raise exception when called with workspace_id=None
        prom.record_queue_job("test_job", 1.5, workspace_id=None)


class TestRecordActionExecutionWithWorkspace:
    """Test record_action_execution() with optional workspace_id parameter."""

    def test_record_action_execution_signature_accepts_workspace_id(self):
        """record_action_execution() should accept optional workspace_id parameter."""
        # This test verifies the function signature is correct
        import inspect

        sig = inspect.signature(prom.record_action_execution)
        assert "workspace_id" in sig.parameters
        assert sig.parameters["workspace_id"].default is None

    def test_record_action_execution_backward_compatible(self):
        """record_action_execution() should work without workspace_id (backward compatible)."""
        # Should not raise exception when called without workspace_id
        prom.record_action_execution("provider", "action", "success", 2.5)

    def test_record_action_execution_with_workspace_id(self):
        """record_action_execution() should accept workspace_id when provided."""
        # Should not raise exception when called with workspace_id
        prom.record_action_execution("provider", "action", "success", 2.5, workspace_id="workspace1")

    def test_record_action_execution_with_none_workspace_id(self):
        """record_action_execution() should handle None workspace_id gracefully."""
        # Should not raise exception when called with workspace_id=None
        prom.record_action_execution("provider", "action", "success", 2.5, workspace_id=None)

    def test_record_action_execution_status_variations(self):
        """record_action_execution() should accept various status values."""
        # Test common status values with workspace_id
        prom.record_action_execution("google", "gmail.send", "success", 1.0, workspace_id="ws1")
        prom.record_action_execution("google", "gmail.send", "failed", 0.5, workspace_id="ws1")
        prom.record_action_execution("microsoft", "outlook.send", "success", 1.5, workspace_id="ws2")
