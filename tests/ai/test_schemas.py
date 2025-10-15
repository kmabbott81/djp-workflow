"""Unit tests for AI Orchestrator schemas.

Sprint 55 Week 3: Validate Pydantic schemas for plans and actions.
"""

import pytest
from pydantic import ValidationError

# TODO(Slice 5): Implement src.schemas.ai_plan module
# CI Stabilization: Skip if Slice 5 modules not yet implemented
try:
    from src.schemas.ai_plan import PlannedAction, PlanResult
except ImportError:
    pytest.skip(
        "Slice 5 (AI Orchestrator) not yet implemented - skipping AI plan schema tests. "
        "Will be implemented when natural language action planning is added.",
        allow_module_level=True,
    )


class TestPlannedAction:
    """Tests for PlannedAction schema."""

    def test_valid_action(self):
        """Valid action passes validation."""
        action = PlannedAction(
            provider="google",
            action="gmail.send",
            params={"to": "user@example.com", "subject": "Test", "body": "Hello"},
            client_request_id="req-001",
        )

        assert action.provider == "google"
        assert action.action == "gmail.send"
        assert action.params["to"] == "user@example.com"
        assert action.client_request_id == "req-001"

    def test_minimal_action(self):
        """Action with minimal fields (no client_request_id)."""
        action = PlannedAction(
            provider="independent",
            action="webhook.post",
            params={"url": "https://example.com/hook"},
        )

        assert action.provider == "independent"
        assert action.action == "webhook.post"
        assert action.client_request_id is None

    def test_missing_required_fields(self):
        """Missing required fields raises ValidationError."""
        with pytest.raises(ValidationError) as exc_info:
            PlannedAction(
                provider="google",
                # Missing 'action' field
                params={},
            )

        errors = exc_info.value.errors()
        assert any(e["loc"] == ("action",) for e in errors)

    def test_empty_params_allowed(self):
        """Empty params dict is valid."""
        action = PlannedAction(
            provider="independent",
            action="system.healthcheck",
            params={},
        )

        assert action.params == {}

    def test_complex_params(self):
        """Complex nested params are preserved."""
        action = PlannedAction(
            provider="google",
            action="gmail.send",
            params={
                "to": ["user1@example.com", "user2@example.com"],
                "cc": ["cc@example.com"],
                "attachments": [{"name": "doc.pdf", "size": 1024}],
                "metadata": {"priority": "high", "tags": ["urgent", "sales"]},
            },
        )

        assert len(action.params["to"]) == 2
        assert action.params["metadata"]["priority"] == "high"


class TestPlanResult:
    """Tests for PlanResult schema."""

    def test_valid_plan(self, sample_plan_minimal):
        """Valid plan passes validation."""
        plan = PlanResult(**sample_plan_minimal)

        assert plan.intent == "Send email to ops team"
        assert plan.confidence == 0.95
        assert len(plan.actions) == 1
        assert plan.actions[0].action == "gmail.send"

    def test_multi_action_plan(self, sample_plan_multi_action):
        """Plan with multiple actions."""
        plan = PlanResult(**sample_plan_multi_action)

        assert len(plan.actions) == 2
        assert plan.actions[0].action == "gmail.send"
        assert plan.actions[1].action == "task.create"
        assert plan.notes == "Multi-step workflow"

    def test_confidence_boundaries(self):
        """Confidence must be between 0.0 and 1.0."""
        # Valid boundaries
        PlanResult(
            intent="Test",
            confidence=0.0,
            actions=[PlannedAction(provider="test", action="test.action", params={})],
        )

        PlanResult(
            intent="Test",
            confidence=1.0,
            actions=[PlannedAction(provider="test", action="test.action", params={})],
        )

        # Invalid: >1.0
        with pytest.raises(ValidationError) as exc_info:
            PlanResult(
                intent="Test",
                confidence=1.5,
                actions=[PlannedAction(provider="test", action="test.action", params={})],
            )

        assert any("less than or equal to 1" in str(e["msg"]).lower() for e in exc_info.value.errors())

        # Invalid: <0.0
        with pytest.raises(ValidationError) as exc_info:
            PlanResult(
                intent="Test",
                confidence=-0.1,
                actions=[PlannedAction(provider="test", action="test.action", params={})],
            )

        assert any("greater than or equal to 0" in str(e["msg"]).lower() for e in exc_info.value.errors())

    def test_empty_actions_list(self):
        """Plan with empty actions list is valid (for now)."""
        plan = PlanResult(
            intent="No actions needed",
            confidence=0.5,
            actions=[],
        )

        assert plan.actions == []

    def test_serialization_round_trip(self, sample_plan_minimal):
        """Plan can be serialized and deserialized."""
        plan = PlanResult(**sample_plan_minimal)

        # Serialize to dict
        plan_dict = plan.model_dump()

        # Deserialize from dict
        plan_restored = PlanResult(**plan_dict)

        assert plan_restored.intent == plan.intent
        assert plan_restored.confidence == plan.confidence
        assert len(plan_restored.actions) == len(plan.actions)

    def test_json_serialization(self, sample_plan_multi_action):
        """Plan can be serialized to JSON."""
        plan = PlanResult(**sample_plan_multi_action)

        # Serialize to JSON string
        json_str = plan.model_dump_json()

        assert "Send email and create task" in json_str
        assert "gmail.send" in json_str
        assert "task.create" in json_str

        # Deserialize from JSON
        plan_restored = PlanResult.model_validate_json(json_str)

        assert plan_restored.confidence == plan.confidence

    def test_optional_notes_field(self):
        """Notes field is optional."""
        # With notes
        plan1 = PlanResult(
            intent="Test",
            confidence=0.8,
            actions=[],
            notes="Some notes",
        )
        assert plan1.notes == "Some notes"

        # Without notes
        plan2 = PlanResult(
            intent="Test",
            confidence=0.8,
            actions=[],
        )
        assert plan2.notes is None
