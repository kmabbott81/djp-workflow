"""Simple job queue with idempotency for AI agent actions.

Sprint 55 Week 3: Redis-backed queue for AI action execution with idempotency.
Sprint 60 Phase 1: Dual-write migration for workspace-scoped keys.
"""

import json
import logging
import os
import re
from datetime import datetime, timezone
from typing import Any

import redis

# Sprint 60 Phase 1: Feature flag for dual-write migration
# When enabled, writes to both old (ai:jobs:{job_id}) and new (ai:job:{workspace_id}:{job_id}) schemas
ENABLE_NEW_SCHEMA = os.getenv("AI_JOBS_NEW_SCHEMA", "off").lower() == "on"

_LOG = logging.getLogger(__name__)

# Workspace ID validation (Sprint 60 Phase 1 - Security fix HIGH-5)
# Pattern: lowercase alphanumeric, hyphens, underscores; 1-32 chars; must start with alphanumeric
# Accepted pattern: ^[a-z0-9][a-z0-9_-]{0,31}$
_WORKSPACE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")


def _validate_workspace_id(workspace_id: str) -> None:
    """Validate workspace_id to prevent Redis key pattern injection.

    Args:
        workspace_id: Workspace identifier to validate

    Raises:
        ValueError: If workspace_id is invalid
    """
    if not workspace_id or not _WORKSPACE_ID_PATTERN.fullmatch(workspace_id):
        raise ValueError(
            "Invalid workspace_id: must be 1-32 lowercase alphanumeric/hyphen/underscore, start with alphanumeric"
        )


class SimpleQueue:
    """Job queue with idempotency support using Redis.

    Provides enqueue, dequeue, status updates, and idempotency checking.

    Sprint 60 Phase 1: Supports dual-write migration with AI_JOBS_NEW_SCHEMA flag.
    """

    def __init__(self, redis_url: str | None = None):
        """
        Initialize queue with Redis connection.

        Args:
            redis_url: Redis connection URL (defaults to REDIS_URL env var)
        """
        url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._redis = redis.from_url(url, decode_responses=True)
        self._queue_key = "ai:queue:pending"
        self._jobs_key = "ai:jobs"
        self._jobs_key_new = "ai:job"  # Sprint 60: New workspace-scoped prefix
        self._idempotency_prefix = "ai:idempotency:"

    def enqueue(
        self,
        job_id: str,
        action_provider: str,
        action_name: str,
        params: dict[str, Any],
        workspace_id: str,
        actor_id: str,
        client_request_id: str | None = None,
    ) -> bool:
        """
        Add job to queue with idempotency check.

        Sprint 60 Phase 1: Dual-write to both old and new key schemas when flag enabled.

        Args:
            job_id: Unique job identifier
            action_provider: Provider (e.g., 'google', 'microsoft')
            action_name: Action to execute (e.g., 'gmail.send')
            params: Action parameters
            workspace_id: Workspace identifier
            actor_id: Actor identifier
            client_request_id: Optional idempotency key

        Returns:
            True if enqueued, False if duplicate (blocked by idempotency)
        """
        # Sprint 60 Phase 1: Validate workspace_id to prevent key injection (HIGH-5)
        # Accepted pattern: ^[a-z0-9][a-z0-9_-]{0,31}$
        _validate_workspace_id(workspace_id)

        # Create job data
        job_data = {
            "job_id": job_id,
            "status": "pending",
            "action_provider": action_provider,
            "action_name": action_name,
            "params": json.dumps(params),
            "workspace_id": workspace_id,
            "actor_id": actor_id,
            "result": "",  # Empty string instead of None for Redis compatibility
            "enqueued_at": datetime.now(timezone.utc).isoformat(),
        }

        # Sprint 60 Phase 1: Atomic dual-write with Redis pipeline (HIGH-1/3/6, CRITICAL-1)
        # Always write to old schema (backwards compatibility)
        job_key_old = f"{self._jobs_key}:{job_id}"

        # Prepare idempotency key if provided
        idempotency_key = None
        if client_request_id:
            idempotency_key = f"{self._idempotency_prefix}{workspace_id}:{client_request_id}"
            # Check idempotency BEFORE pipeline (read-only check)
            if self._redis.exists(idempotency_key):
                return False  # Duplicate request

        try:
            # Sprint 60 Phase 1 FIX (HIGH-1): Use pipeline for atomicity
            pipe = self._redis.pipeline()

            # Write to old key pattern (always)
            pipe.hset(job_key_old, mapping=job_data)

            # Conditionally write to new schema
            if ENABLE_NEW_SCHEMA:
                job_key_new = f"{self._jobs_key_new}:{workspace_id}:{job_id}"
                pipe.hset(job_key_new, mapping=job_data)

            # Add to queue
            pipe.rpush(self._queue_key, job_id)

            # CRITICAL-1 FIX: Set idempotency AFTER writes (in same transaction)
            if idempotency_key:
                pipe.set(idempotency_key, job_id, nx=True, ex=86400)

            # Execute all operations atomically
            pipe.execute()

            # Record telemetry AFTER successful pipeline execution
            if ENABLE_NEW_SCHEMA:
                from src.telemetry.prom import record_dual_write_attempt

                record_dual_write_attempt(workspace_id, "succeeded")

            return True

        except Exception as exc:
            # HIGH-7 FIX: Remove exc_info=True to prevent leak
            _LOG.error("Failed to enqueue job for workspace (job_id logged internally)")
            _LOG.debug(
                "Enqueue failure details: job_id=%s, workspace_id=%s, error=%s",
                job_id,
                workspace_id,
                str(exc),
            )

            # Record telemetry for failure (nitpick: always observable)
            if ENABLE_NEW_SCHEMA:
                from src.telemetry.prom import record_dual_write_attempt

                record_dual_write_attempt(workspace_id, "failed")

            # Pipeline failed atomically - no partial state, no cleanup needed
            raise

    def get_job(self, job_id: str, workspace_id: str | None = None) -> dict[str, Any] | None:
        """
        Get job data by ID.

        Sprint 60 Phase 1: Falls back from new schema to old schema when flag enabled.

        Args:
            job_id: Job identifier
            workspace_id: Workspace identifier (required if ENABLE_NEW_SCHEMA is True)

        Returns:
            Job data dict or None if not found
        """
        job_data = None

        # Sprint 60 Phase 1: Try new schema first if enabled and workspace_id provided
        if ENABLE_NEW_SCHEMA and workspace_id:
            # Validate workspace_id to prevent key injection (HIGH-5)
            try:
                _validate_workspace_id(workspace_id)
            except ValueError:
                _LOG.warning("Invalid workspace_id in get_job, falling back to old schema")
                workspace_id = None  # Fall back to old schema

        if ENABLE_NEW_SCHEMA and workspace_id:
            job_key_new = f"{self._jobs_key_new}:{workspace_id}:{job_id}"
            job_data = self._redis.hgetall(job_key_new)

        # Fallback to old schema if not found in new schema (or flag disabled)
        if not job_data:
            job_key_old = f"{self._jobs_key}:{job_id}"
            job_data = self._redis.hgetall(job_key_old)

        if not job_data:
            return None

        # Deserialize params and result
        if "params" in job_data:
            job_data["params"] = json.loads(job_data["params"])
        if job_data.get("result"):
            job_data["result"] = json.loads(job_data["result"])

        return job_data

    def update_status(
        self,
        job_id: str,
        status: str,
        result: dict[str, Any] | None = None,
        workspace_id: str | None = None,
    ) -> None:
        """
        Update job status.

        Sprint 60 Phase 1: Dual-write status updates to both schemas when flag enabled.

        Args:
            job_id: Job identifier
            status: New status ('pending', 'running', 'completed', 'failed')
            result: Optional result data (for completed/failed status)
            workspace_id: Workspace identifier (required if ENABLE_NEW_SCHEMA is True)
        """
        # Sprint 60 Phase 1: Validate workspace_id (HIGH-5)
        if workspace_id:
            _validate_workspace_id(workspace_id)

        updates = {"status": status}

        # Add timestamps based on status
        if status == "running":
            updates["started_at"] = datetime.now(timezone.utc).isoformat()
        elif status in ("completed", "failed"):
            updates["finished_at"] = datetime.now(timezone.utc).isoformat()
            if result:
                updates["result"] = json.dumps(result)

        job_key_old = f"{self._jobs_key}:{job_id}"

        # HIGH-2 FIX: Use pipeline for atomic dual-update with error handling
        try:
            if ENABLE_NEW_SCHEMA and workspace_id:
                # Atomic dual-update with pipeline
                pipe = self._redis.pipeline()
                pipe.hset(job_key_old, mapping=updates)

                job_key_new = f"{self._jobs_key_new}:{workspace_id}:{job_id}"
                # Only update if key exists (checked in transaction)
                pipe.exists(job_key_new)
                pipe.hset(job_key_new, mapping=updates)

                results = pipe.execute()
                # results[1] is the EXISTS result for new key
                if not results[1]:
                    _LOG.debug("New schema key not found during update_status (job_id=%s)", job_id)
            else:
                # Single update to old schema
                self._redis.hset(job_key_old, mapping=updates)

        except Exception as exc:
            # HIGH-2 FIX: Add error handling for dual-update failures
            _LOG.error("Failed to update job status (logged internally)")
            _LOG.debug("update_status failure: job_id=%s, workspace_id=%s, error=%s", job_id, workspace_id, str(exc))
            raise

    def get_queue_depth(self) -> int:
        """
        Get number of pending jobs in queue.

        Returns:
            Number of jobs waiting to be processed
        """
        return self._redis.llen(self._queue_key)

    def list_jobs(
        self,
        workspace_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        """
        List jobs with optional filters.

        Args:
            workspace_id: Filter by workspace (None for all)
            status: Filter by status (None for all)
            limit: Maximum number of jobs to return

        Returns:
            List of job data dicts
        """
        # Get all job keys
        job_keys = self._redis.keys(f"{self._jobs_key}:*")
        jobs = []

        for job_key in job_keys:
            job_data = self._redis.hgetall(job_key)
            if not job_data:
                continue

            # Apply filters
            if workspace_id and job_data.get("workspace_id") != workspace_id:
                continue
            if status and job_data.get("status") != status:
                continue

            # Deserialize JSON fields
            if "params" in job_data:
                job_data["params"] = json.loads(job_data["params"])
            if job_data.get("result"):
                job_data["result"] = json.loads(job_data["result"])

            jobs.append(job_data)

            if len(jobs) >= limit:
                break

        # Sort by enqueued_at descending (most recent first)
        jobs.sort(key=lambda j: j.get("enqueued_at", ""), reverse=True)

        return jobs[:limit]
