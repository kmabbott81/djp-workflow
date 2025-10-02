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
