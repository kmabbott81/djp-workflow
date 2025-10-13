"""Simple Redis-based queue for AI Orchestrator v0.1 jobs.

Sprint 55 Week 3: Lightweight job queue for action execution.
"""

import json
import os
from datetime import datetime
from typing import Optional

from .keys import ai_idempotency_key, ai_job_key, ai_queue_key


class SimpleQueue:
    """Simple Redis-based job queue with idempotency."""

    def __init__(self):
        """Initialize queue with Redis connection."""
        redis_url = os.getenv("REDIS_URL")
        if not redis_url:
            raise ValueError("REDIS_URL not configured")

        import redis

        self.redis = redis.from_url(redis_url, decode_responses=True)

    def enqueue(
        self,
        job_id: str,
        action_provider: str,
        action_name: str,
        params: dict,
        workspace_id: str,
        actor_id: str,
        client_request_id: Optional[str] = None,
    ) -> bool:
        """Enqueue a job with idempotency check.

        Args:
            job_id: Unique job identifier
            action_provider: Provider name (e.g., "google")
            action_name: Action ID (e.g., "gmail.send")
            params: Action parameters
            workspace_id: Workspace identifier
            actor_id: Actor identifier
            client_request_id: Optional idempotency key

        Returns:
            True if enqueued, False if duplicate (idempotency hit)
        """
        # Check idempotency (15 minute TTL)
        if client_request_id:
            idempotency_key = ai_idempotency_key(client_request_id)
            # SETNX returns 1 if key was set, 0 if already exists
            if not self.redis.set(idempotency_key, job_id, nx=True, ex=900):
                # Duplicate request - idempotency hit
                return False

        # Create job data
        job_data = {
            "job_id": job_id,
            "status": "pending",
            "action_provider": action_provider,
            "action_name": action_name,
            "params": params,
            "workspace_id": workspace_id,
            "actor_id": actor_id,
            "client_request_id": client_request_id,
            "enqueued_at": datetime.utcnow().isoformat(),
            "started_at": None,
            "finished_at": None,
            "result": None,
            "error": None,
        }

        # Store job data (24h TTL)
        job_key = ai_job_key(job_id)
        self.redis.hset(
            job_key, mapping={k: json.dumps(v) if not isinstance(v, str) else v for k, v in job_data.items()}
        )
        self.redis.expire(job_key, 86400)

        # Push to queue
        queue_key = ai_queue_key()
        self.redis.rpush(queue_key, job_id)

        return True

    def dequeue(self) -> Optional[dict]:
        """Dequeue next job (blocking with 1s timeout).

        Returns:
            Job data dict or None if queue empty
        """
        queue_key = ai_queue_key()

        # BLPOP blocks until item available (1 second timeout)
        result = self.redis.blpop(queue_key, timeout=1)
        if not result:
            return None

        _, job_id = result

        # Get job data
        return self.get_job(job_id)

    def get_job(self, job_id: str) -> Optional[dict]:
        """Get job data by ID.

        Args:
            job_id: Job identifier

        Returns:
            Job data dict or None if not found
        """
        job_key = ai_job_key(job_id)
        data = self.redis.hgetall(job_key)

        if not data:
            return None

        # Deserialize JSON fields
        for key in ["params", "result"]:
            if key in data and data[key]:
                try:
                    data[key] = json.loads(data[key])
                except json.JSONDecodeError:
                    pass

        return data

    def update_status(
        self,
        job_id: str,
        status: str,
        result: Optional[dict] = None,
        error: Optional[str] = None,
    ):
        """Update job status and result.

        Args:
            job_id: Job identifier
            status: New status (pending, running, completed, error)
            result: Result data (if completed)
            error: Error message (if error)
        """
        job_key = ai_job_key(job_id)

        updates = {
            "status": status,
        }

        if status == "running":
            updates["started_at"] = datetime.utcnow().isoformat()
        elif status in ("completed", "error"):
            updates["finished_at"] = datetime.utcnow().isoformat()

        if result:
            updates["result"] = json.dumps(result)

        if error:
            updates["error"] = error

        self.redis.hset(job_key, mapping=updates)

    def get_queue_depth(self) -> int:
        """Get current queue depth.

        Returns:
            Number of pending jobs
        """
        queue_key = ai_queue_key()
        return self.redis.llen(queue_key)
