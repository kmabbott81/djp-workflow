"""Unit tests for Sprint 60 Phase 1 dual-write functionality.

Tests dual-write key migration from ai:jobs:{job_id} to ai:job:{workspace_id}:{job_id}.

References:
- Sprint 60 Phase 1: Dual-write migration for workspace-scoped keys
- src/queue/simple_queue.py: SimpleQueue with AI_JOBS_NEW_SCHEMA flag
- RECOMMENDED_PATTERNS_S60_MIGRATION.md: Dual-write pattern documentation
"""

from unittest.mock import patch

import fakeredis
import pytest

from src.queue.simple_queue import SimpleQueue


@pytest.fixture
def redis_client():
    """Provide FakeRedis client for testing."""
    return fakeredis.FakeStrictRedis(decode_responses=True)


@pytest.fixture
def queue_with_redis(redis_client):
    """Provide SimpleQueue with FakeRedis for testing."""
    with patch("src.queue.simple_queue.redis.from_url", return_value=redis_client):
        queue = SimpleQueue()
        queue._redis = redis_client  # Override with fake redis
        yield queue


class TestDualWriteDisabled:
    """Tests for dual-write when AI_JOBS_NEW_SCHEMA is disabled (default)."""

    def test_enqueue_writes_only_old_schema_when_flag_off(self, queue_with_redis):
        """Enqueue writes only to old schema when AI_JOBS_NEW_SCHEMA=off."""
        # Ensure flag is OFF
        with patch("src.queue.simple_queue.ENABLE_NEW_SCHEMA", False):
            success = queue_with_redis.enqueue(
                job_id="job-001",
                action_provider="google",
                action_name="gmail.send",
                params={"to": "test@example.com"},
                workspace_id="workspace-123",
                actor_id="user-456",
            )

            assert success is True

            # Verify old key exists
            old_key = "ai:jobs:job-001"
            assert queue_with_redis._redis.exists(old_key)

            # Verify new key does NOT exist
            new_key = "ai:job:workspace-123:job-001"
            assert not queue_with_redis._redis.exists(new_key)

    def test_get_job_reads_from_old_schema_when_flag_off(self, queue_with_redis):
        """get_job reads from old schema when AI_JOBS_NEW_SCHEMA=off."""
        with patch("src.queue.simple_queue.ENABLE_NEW_SCHEMA", False):
            # Enqueue job (writes to old schema only)
            queue_with_redis.enqueue(
                job_id="job-002",
                action_provider="google",
                action_name="gmail.send",
                params={"to": "test@example.com"},
                workspace_id="workspace-123",
                actor_id="user-456",
            )

            # Retrieve job (should read from old schema)
            job_data = queue_with_redis.get_job("job-002")
            assert job_data is not None
            assert job_data["job_id"] == "job-002"
            assert job_data["workspace_id"] == "workspace-123"


class TestDualWriteEnabled:
    """Tests for dual-write when AI_JOBS_NEW_SCHEMA is enabled."""

    def test_enqueue_writes_both_schemas_when_flag_on(self, queue_with_redis):
        """Enqueue writes to BOTH old and new schemas when AI_JOBS_NEW_SCHEMA=on."""
        with patch("src.queue.simple_queue.ENABLE_NEW_SCHEMA", True):
            with patch("src.telemetry.prom.record_dual_write_attempt") as mock_telemetry:
                success = queue_with_redis.enqueue(
                    job_id="job-003",
                    action_provider="google",
                    action_name="gmail.send",
                    params={"to": "test@example.com"},
                    workspace_id="workspace-123",
                    actor_id="user-456",
                )

                assert success is True

                # Verify old key exists
                old_key = "ai:jobs:job-003"
                assert queue_with_redis._redis.exists(old_key)

                # Verify new key exists
                new_key = "ai:job:workspace-123:job-003"
                assert queue_with_redis._redis.exists(new_key)

                # Verify both keys have same data
                old_data = queue_with_redis._redis.hgetall(old_key)
                new_data = queue_with_redis._redis.hgetall(new_key)
                assert old_data["job_id"] == new_data["job_id"]
                assert old_data["workspace_id"] == new_data["workspace_id"]

                # Verify telemetry was recorded
                mock_telemetry.assert_called_once_with("workspace-123", "succeeded")

    def test_get_job_reads_new_schema_first_when_flag_on(self, queue_with_redis):
        """get_job tries new schema first, falls back to old when AI_JOBS_NEW_SCHEMA=on."""
        with patch("src.queue.simple_queue.ENABLE_NEW_SCHEMA", True):
            # Manually create job in new schema only (simulates backfill scenario)
            new_key = "ai:job:workspace-123:job-004"
            queue_with_redis._redis.hset(
                new_key,
                mapping={
                    "job_id": "job-004",
                    "status": "pending",
                    "action_provider": "google",
                    "action_name": "gmail.send",
                    "params": '{"to": "test@example.com"}',
                    "workspace_id": "workspace-123",
                    "actor_id": "user-456",
                    "result": "null",
                    "enqueued_at": "2025-01-01T00:00:00Z",
                },
            )

            # Retrieve job with workspace_id (should read from new schema)
            job_data = queue_with_redis.get_job("job-004", workspace_id="workspace-123")
            assert job_data is not None
            assert job_data["job_id"] == "job-004"
            assert job_data["workspace_id"] == "workspace-123"

    def test_update_status_writes_both_schemas_when_flag_on(self, queue_with_redis):
        """update_status writes to both schemas when AI_JOBS_NEW_SCHEMA=on."""
        with patch("src.queue.simple_queue.ENABLE_NEW_SCHEMA", True):
            with patch("src.telemetry.prom.record_dual_write_attempt"):
                # Enqueue job (writes to both schemas)
                queue_with_redis.enqueue(
                    job_id="job-005",
                    action_provider="google",
                    action_name="gmail.send",
                    params={"to": "test@example.com"},
                    workspace_id="workspace-123",
                    actor_id="user-456",
                )

                # Update status
                queue_with_redis.update_status(job_id="job-005", status="completed", workspace_id="workspace-123")

                # Verify old key has updated status
                old_key = "ai:jobs:job-005"
                old_data = queue_with_redis._redis.hgetall(old_key)
                assert old_data["status"] == "completed"

                # Verify new key has updated status
                new_key = "ai:job:workspace-123:job-005"
                new_data = queue_with_redis._redis.hgetall(new_key)
                assert new_data["status"] == "completed"
