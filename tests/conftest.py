"""Global pytest configuration and fixtures."""

import pytest


@pytest.fixture(autouse=True)
def _enable_rbac_and_budgets(monkeypatch):
    """
    Auto-enable RBAC and budgets for all tests to ensure deterministic behavior.

    This fixture ensures that security and budget features are always enabled
    during test runs, preventing false negatives when feature flags default to
    false in development environments.

    Feature flags enabled:
    - FEATURE_RBAC_ENFORCE: true (enforce role-based access control)
    - FEATURE_BUDGETS: true (enforce per-tenant budget limits)

    Network features disabled:
    - CONNECTORS_NETWORK_ENABLED: false (avoid external API calls in tests)

    This fixture uses autouse=True so it applies to all tests automatically
    without requiring explicit declaration in each test function.
    """
    # Enable RBAC enforcement for all tests
    monkeypatch.setenv("FEATURE_RBAC_ENFORCE", "true")

    # Enable budget enforcement for all tests
    monkeypatch.setenv("FEATURE_BUDGETS", "true")

    # Disable network calls for connectors (tests use mocks)
    monkeypatch.setenv("CONNECTORS_NETWORK_ENABLED", "false")

    # Set default tenant for tests
    monkeypatch.setenv("DEFAULT_TENANT_ID", "test-tenant")

    # Use temporary database file for tests (in-memory doesn't work with multiple connections)
    import atexit
    import tempfile

    temp_db = tempfile.NamedTemporaryFile(mode="w", suffix=".db", delete=False)
    temp_db.close()
    monkeypatch.setenv("METADATA_DB_PATH", temp_db.name)

    # Clean up temp file after test
    def cleanup():
        import os

        try:
            os.unlink(temp_db.name)
        except Exception:
            pass

    atexit.register(cleanup)

    # Disable audit logging to disk during tests (can log to memory/mock)
    monkeypatch.setenv("AUDIT_LOG_DIR", "/tmp/test-audit-logs")

    # Reinitialize metadata database after setting env vars
    from src.metadata import init_metadata_db

    init_metadata_db()


# Sprint 25 fixtures for new tests


@pytest.fixture
def mock_openai_client():
    """
    Fixture for mocking OpenAI client.

    Provides a mock OpenAI client that can be used to test OpenAI adapter
    without making real API calls. The mock client has a configured
    chat.completions.create method that can be set up with side_effect
    or return_value in tests.

    Returns:
        Mock: Mocked OpenAI client instance

    Example:
        def test_example(mock_openai_client):
            mock_response = Mock()
            mock_response.choices = [Mock(message=Mock(content="test"))]
            mock_openai_client.chat.completions.create.return_value = mock_response
    """
    from unittest.mock import Mock, patch

    with patch("src.agents.openai_adapter.OpenAI") as mock_client_class:
        mock_client = Mock()
        mock_client_class.return_value = mock_client
        yield mock_client


@pytest.fixture
def temp_artifacts_dir(tmp_path):
    """
    Fixture for temporary artifact directory.

    Creates a temporary directory structure for workflow artifacts.
    Automatically cleaned up after test completion.

    Args:
        tmp_path: pytest's built-in tmp_path fixture

    Returns:
        Path: Path to temporary artifacts directory

    Example:
        def test_example(temp_artifacts_dir):
            output_file = temp_artifacts_dir / "workflow" / "result.md"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            output_file.write_text("content")
    """
    artifacts_dir = tmp_path / "artifacts"
    artifacts_dir.mkdir(parents=True, exist_ok=True)
    return artifacts_dir


@pytest.fixture
def mock_cost_logger(tmp_path):
    """
    Fixture for capturing cost events.

    Creates a temporary cost event logger that writes to a JSONL file.
    Useful for testing cost tracking without polluting actual logs.

    Args:
        tmp_path: pytest's built-in tmp_path fixture

    Returns:
        tuple: (CostTracker instance, Path to log file)

    Example:
        def test_example(mock_cost_logger):
            tracker, log_path = mock_cost_logger
            tracker.log_event("tenant", "workflow", "model", 100, 50, 0.001)
            assert log_path.exists()
    """
    from src.agents.openai_adapter import CostTracker

    cost_log_path = tmp_path / "cost_events.jsonl"
    tracker = CostTracker(cost_log_path)
    return tracker, cost_log_path


@pytest.fixture
def temp_cost_log(tmp_path):
    """
    Fixture for temporary cost log path.

    Provides a path for cost event logging in tests.
    File is automatically cleaned up after test.

    Args:
        tmp_path: pytest's built-in tmp_path fixture

    Returns:
        Path: Path to temporary cost log file

    Example:
        def test_example(temp_cost_log):
            adapter = OpenAIAdapter(cost_log_path=temp_cost_log)
            # Cost events will be logged to temp_cost_log
    """
    return tmp_path / "cost_events.jsonl"


@pytest.fixture
def mock_project_root(tmp_path):
    """
    Fixture for mocking project root with config files.

    Creates a temporary project structure with templates/examples
    directory containing mock workflow configuration files.

    Args:
        tmp_path: pytest's built-in tmp_path fixture

    Returns:
        Path: Path to temporary project root

    Example:
        def test_example(mock_project_root):
            config_path = mock_project_root / "templates" / "examples" / "weekly_report.yaml"
            assert config_path.exists()
    """
    import yaml

    # Create templates/examples directory
    templates_dir = tmp_path / "templates" / "examples"
    templates_dir.mkdir(parents=True, exist_ok=True)

    # Create mock config files
    weekly_config = {
        "workflow_name": "weekly_report",
        "description": "Generate weekly status report",
        "prompt_template": "Generate a weekly report for {start_date} to {end_date}:\n{context}",
        "parameters": {"model": "gpt-4o", "max_tokens": 2000, "temperature": 0.5},
    }

    meeting_config = {
        "workflow_name": "meeting_brief",
        "description": "Generate meeting brief",
        "prompt_template": "Summarize meeting: {meeting_title} on {meeting_date}\nAttendees: {attendees}\n\nTranscript:\n{transcript}",
        "parameters": {"model": "gpt-4o", "max_tokens": 1500, "temperature": 0.3},
    }

    inbox_config = {
        "workflow_name": "inbox_sweep",
        "description": "Process inbox and drive files",
        "prompt_template": "Process these files: {file_list}",
        "parameters": {"model": "gpt-4o-mini", "max_tokens": 1000, "temperature": 0.4},
    }

    with open(templates_dir / "weekly_report.yaml", "w", encoding="utf-8") as f:
        yaml.dump(weekly_config, f)

    with open(templates_dir / "meeting_brief.yaml", "w", encoding="utf-8") as f:
        yaml.dump(meeting_config, f)

    with open(templates_dir / "inbox_sweep.yaml", "w", encoding="utf-8") as f:
        yaml.dump(inbox_config, f)

    return tmp_path
