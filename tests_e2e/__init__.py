"""End-to-end smoke tests for OpenAI Agents Workflows.

This package contains integration tests that verify the application's
core functionality across multiple components without requiring live
external API calls.

All tests in this package:
- Use DRY_RUN mode for connectors (no real API calls)
- Work offline (no network dependencies)
- Can run in CI environments
- Are marked with @pytest.mark.e2e
"""
