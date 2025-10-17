"""Simple job queue with idempotency for AI agent actions.

Sprint 55 Week 3: Redis-backed queue for AI action execution with idempotency.
"""

import json
import os
from datetime import datetime, timezone
from typing import Any

import redis


class SimpleQueue:
    """Job queue with idempotency support using Redis.

    Provides enqueue, dequeue, status updates, and idempotency checking.
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
        # Check idempotency if client_request_id provided
        if client_request_id:
            idempotency_key = f"{self._idempotency_prefix}{workspace_id}:{client_request_id}"
            # SETNX with expiration (24 hours)
            is_new = self._redis.set(idempotency_key, job_id, nx=True, ex=86400)
            if not is_new:
                return False  # Duplicate request

        # Create job data
        job_data = {
            "job_id": job_id,
            "status": "pending",
            "action_provider": action_provider,
            "action_name": action_name,
            "params": json.dumps(params),
            "workspace_id": workspace_id,
            "actor_id": actor_id,
            "result": None,
            "enqueued_at": datetime.now(timezone.utc).isoformat(),
        }

        # Store job data
        job_key = f"{self._jobs_key}:{job_id}"
        self._redis.hset(job_key, mapping=job_data)

        # Add to queue
        self._redis.rpush(self._queue_key, job_id)

        return True

    def get_job(self, job_id: str) -> dict[str, Any] | None:
        """
        Get job data by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job data dict or None if not found
        """
        job_key = f"{self._jobs_key}:{job_id}"
        job_data = self._redis.hgetall(job_key)

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
    ) -> None:
        """
        Update job status.

        Args:
            job_id: Job identifier
            status: New status ('pending', 'running', 'completed', 'failed')
            result: Optional result data (for completed/failed status)
        """
        job_key = f"{self._jobs_key}:{job_id}"
        updates = {"status": status}

        # Add timestamps based on status
        if status == "running":
            updates["started_at"] = datetime.now(timezone.utc).isoformat()
        elif status in ("completed", "failed"):
            updates["finished_at"] = datetime.now(timezone.utc).isoformat()
            if result:
                updates["result"] = json.dumps(result)

        self._redis.hset(job_key, mapping=updates)

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
