# Sprint 60 Phase 2 Epic: Read Routing + Webapi Security Fixes

**Parent**: Sprint 60 - Workspace-Scoped Key Migration
**Depends On**: v0.1.5-phase1 (Phase 1 dual-write deployed and stable)
**Estimated Effort**: 15-20 hours
**Priority**: HIGH (blocks multi-tenant production)

---

## Overview

Phase 2 completes the workspace-scoped key migration by:
1. Fixing pre-existing workspace isolation vulnerabilities in webapi endpoints
2. Implementing read-routing to prioritize new schema
3. Adding async backfill for historical jobs
4. Adding comprehensive isolation tests

**Gate Requirement**: All subtasks must pass agent reviews (Code-Reviewer, Security-Reviewer) before merge.

---

## Subtasks

### 1. Webapi Security Fixes (CRITICAL - 8 hours)

**Reference**: `SECURITY_TICKET_S60_WEBAPI.md`

**Issues to Fix**:
- **CRITICAL-2**: `/ai/jobs` endpoint workspace isolation bypass
- **CRITICAL-3**: `/ai/execute` endpoint workspace_id injection
- **HIGH-4**: `/ai/jobs` pagination returns all workspaces

**Implementation**:

#### Task 1.1: Add `get_authenticated_workspace()` Dependency (2 hours)
**File**: `src/webapi.py`

```python
from fastapi import Depends, Header, HTTPException, status

async def get_authenticated_workspace(
    authorization: str = Header(...)
) -> str:
    """Extract and validate workspace_id from auth token.

    Returns:
        workspace_id: Authenticated workspace identifier

    Raises:
        HTTPException: If token invalid or workspace missing
    """
    try:
        token = authorization.replace("Bearer ", "")
        workspace_id = extract_workspace_id_from_token(token)
        if not workspace_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Workspace not found in authentication token"
            )
        return workspace_id
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )
```

**Tests**: `tests/test_webapi_auth.py`
- `test_get_authenticated_workspace_valid_token()`
- `test_get_authenticated_workspace_missing_workspace()`
- `test_get_authenticated_workspace_invalid_token()`

---

#### Task 1.2: Fix `/ai/jobs` Endpoint (CRITICAL-2, HIGH-4) (3 hours)
**File**: `src/webapi.py:217-253`

**Before**:
```python
@app.get("/ai/jobs")
@require_scopes(["ai:jobs:read"])
async def list_ai_jobs(workspace_id: str | None = None, ...):
    jobs = queue.list_jobs(workspace_id=workspace_id, ...)
    return {"jobs": jobs}
```

**After**:
```python
@app.get("/ai/jobs")
@require_scopes(["ai:jobs:read"])
async def list_ai_jobs(
    auth_workspace_id: str = Depends(get_authenticated_workspace),
    workspace_id: str | None = None,  # Optional filter (must match auth)
    status: str | None = None,
    limit: int = 100,
):
    """List AI orchestrator jobs (workspace-scoped).

    Security: Only returns jobs for authenticated workspace.
    """
    # RBAC check: If workspace_id provided, must match authenticated workspace
    if workspace_id is not None and workspace_id != auth_workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access jobs from other workspaces"
        )

    # Always filter by authenticated workspace (ignore client-provided value)
    jobs = queue.list_jobs(workspace_id=auth_workspace_id, status=status, limit=limit)
    return {"jobs": jobs}
```

**Tests**: `tests/test_webapi_workspace_isolation.py`
- `test_list_jobs_enforces_workspace_isolation()`
- `test_list_jobs_rejects_cross_workspace_query()`
- `test_list_jobs_allows_same_workspace_query()`

---

#### Task 1.3: Fix `/ai/execute` Endpoint (CRITICAL-3) (3 hours)
**File**: `src/webapi.py:279-350`

**Before**:
```python
@app.post("/ai/execute")
@require_scopes(["ai:execute"])
async def execute_ai_action(body: ExecuteRequest, ...):
    job_id = await orchestrator.enqueue_job(
        workspace_id=body.workspace_id,  # Client-controlled
        ...
    )
```

**After**:
```python
@app.post("/ai/execute")
@require_scopes(["ai:execute"])
async def execute_ai_action(
    body: ExecuteRequest,
    auth_workspace_id: str = Depends(get_authenticated_workspace),
    ...
):
    """Execute AI action with orchestration (workspace-scoped).

    Security: Validates body.workspace_id matches authenticated workspace.
    """
    # RBAC check: Reject if body.workspace_id doesn't match auth
    if body.workspace_id != auth_workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot execute actions in other workspaces"
        )

    job_id = await orchestrator.enqueue_job(
        workspace_id=auth_workspace_id,  # Use authenticated workspace
        action_provider=body.action_provider,
        action_name=body.action_name,
        params=body.params,
        actor_id=auth_workspace_id,  # Or extract from token
    )

    return {"job_id": job_id, "status": "enqueued"}
```

**Tests**: `tests/test_webapi_workspace_isolation.py`
- `test_execute_rejects_cross_workspace_injection()`
- `test_execute_allows_same_workspace()`
- `test_execute_rejects_mismatched_body_workspace()`

---

### 2. Read Routing Implementation (MEDIUM - 4 hours)

**Goal**: Prioritize new schema for all reads, maintain fallback to old schema.

#### Task 2.1: Update `get_job()` Read Logic (2 hours)
**File**: `src/queue/simple_queue.py:168-210`

**Current**: Tries new schema only if `workspace_id` provided
**Target**: Try new schema first ALWAYS (when flag=on), fall back to old

**Change**:
```python
def get_job(self, job_id: str, workspace_id: str | None = None) -> dict[str, Any] | None:
    job_data = None

    # Sprint 60 Phase 2: Try new schema first if enabled
    if ENABLE_NEW_SCHEMA and workspace_id:
        _validate_workspace_id(workspace_id)
        job_key_new = f"{self._jobs_key_new}:{workspace_id}:{job_id}"
        job_data = self._redis.hgetall(job_key_new)

    # Fallback to old schema (backward compatibility)
    if not job_data:
        job_key_old = f"{self._jobs_key}:{job_id}"
        job_data = self._redis.hgetall(job_key_old)

    if not job_data:
        return None

    # Deserialize and return
    ...
```

**Tests**: `tests/test_dual_write.py`
- `test_get_job_prefers_new_schema_when_available()`
- `test_get_job_falls_back_to_old_schema_when_new_missing()`

---

#### Task 2.2: Update `list_jobs()` to Scan New Schema (2 hours)
**File**: `src/queue/simple_queue.py:280-329`

**Current**: Only scans old schema (`ai:jobs:*`)
**Target**: Scan new schema when `workspace_id` provided (much faster)

**Change**:
```python
def list_jobs(
    self,
    workspace_id: str | None = None,
    status: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """List jobs with optional filters.

    Sprint 60 Phase 2: Scans new schema when workspace_id provided (faster).
    """
    if ENABLE_NEW_SCHEMA and workspace_id:
        # Phase 2: Scan new schema (workspace-scoped, much faster)
        _validate_workspace_id(workspace_id)
        job_keys = self._redis.keys(f"{self._jobs_key_new}:{workspace_id}:*")
    else:
        # Fallback: Scan old schema (all workspaces)
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
        ...

        jobs.append(job_data)
        if len(jobs) >= limit:
            break

    # Sort by enqueued_at descending
    jobs.sort(key=lambda j: j.get("enqueued_at", ""), reverse=True)
    return jobs[:limit]
```

**Tests**: `tests/test_dual_write.py`
- `test_list_jobs_scans_new_schema_when_workspace_provided()`
- `test_list_jobs_falls_back_to_old_schema_without_workspace()`
- `test_list_jobs_filters_by_workspace_correctly()`

---

### 3. Async Backfill Implementation (OPTIONAL - 5 hours)

**Goal**: Migrate existing jobs from old schema to new schema in background.

#### Task 3.1: Create Backfill Script (3 hours)
**File**: `scripts/backfill_redis_keys.py`

```python
"""Async backfill for Sprint 60 Phase 2: Migrate old schema jobs to new schema.

Usage:
    python scripts/backfill_redis_keys.py --dry-run
    python scripts/backfill_redis_keys.py --batch-size 100
"""

import argparse
import redis
import json
from tqdm import tqdm

def backfill_jobs(redis_url: str, batch_size: int = 100, dry_run: bool = True):
    """Backfill old schema jobs to new schema.

    Args:
        redis_url: Redis connection string
        batch_size: Number of jobs to process per batch
        dry_run: If True, log changes without applying
    """
    r = redis.from_url(redis_url, decode_responses=True)

    # Get all old schema keys
    old_keys = r.keys("ai:jobs:*")
    print(f"Found {len(old_keys)} jobs in old schema")

    backfilled = 0
    skipped = 0
    errors = 0

    for old_key in tqdm(old_keys, desc="Backfilling jobs"):
        try:
            # Get job data
            job_data = r.hgetall(old_key)
            if not job_data:
                skipped += 1
                continue

            # Extract workspace_id and job_id
            workspace_id = job_data.get("workspace_id")
            job_id = old_key.split(":")[-1]

            if not workspace_id:
                print(f"Skipping {old_key}: No workspace_id")
                skipped += 1
                continue

            # Construct new key
            new_key = f"ai:job:{workspace_id}:{job_id}"

            # Check if already exists
            if r.exists(new_key):
                skipped += 1
                continue

            # Write to new schema
            if not dry_run:
                r.hset(new_key, mapping=job_data)
                print(f"Backfilled: {old_key} -> {new_key}")
            else:
                print(f"[DRY-RUN] Would backfill: {old_key} -> {new_key}")

            backfilled += 1

        except Exception as e:
            print(f"Error backfilling {old_key}: {e}")
            errors += 1

    print(f"\nBackfill complete:")
    print(f"  Backfilled: {backfilled}")
    print(f"  Skipped: {skipped}")
    print(f"  Errors: {errors}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--redis-url", default="redis://localhost:6379", help="Redis URL")
    parser.add_argument("--batch-size", type=int, default=100, help="Batch size")
    parser.add_argument("--dry-run", action="store_true", help="Dry run (no writes)")
    args = parser.parse_args()

    backfill_jobs(args.redis_url, args.batch_size, args.dry_run)
```

**Tests**: `tests/test_backfill.py`
- `test_backfill_migrates_job_correctly()`
- `test_backfill_skips_existing_jobs()`
- `test_backfill_handles_missing_workspace_id()`

---

#### Task 3.2: Add Backfill Monitoring (2 hours)
**File**: `src/telemetry/prom.py`

Add new metric:
```python
_backfill_jobs_total = Counter(
    "backfill_jobs_total",
    "Jobs migrated from old to new schema",
    ["workspace_id", "result"],  # succeeded | failed | skipped
)
```

Update backfill script to record telemetry.

---

### 4. Comprehensive Isolation Tests (MEDIUM - 3 hours)

**File**: `tests/test_webapi_workspace_isolation.py` (new)

**Test Coverage** (10+ tests):
1. `test_list_jobs_enforces_workspace_isolation()`
2. `test_list_jobs_rejects_cross_workspace_query()`
3. `test_list_jobs_allows_same_workspace_query()`
4. `test_execute_rejects_cross_workspace_injection()`
5. `test_execute_allows_same_workspace()`
6. `test_execute_rejects_mismatched_body_workspace()`
7. `test_get_authenticated_workspace_valid_token()`
8. `test_get_authenticated_workspace_missing_workspace()`
9. `test_get_authenticated_workspace_invalid_token()`
10. `test_workspace_isolation_across_all_endpoints()`

**Edge Cases**:
- Empty workspace_id
- Missing Authorization header
- Malformed token
- Workspace_id in query vs body mismatch

---

## Acceptance Criteria

### Phase 2 Merge Gate:
- [ ] All webapi security fixes implemented (CRITICAL-2, CRITICAL-3, HIGH-4)
- [ ] `get_authenticated_workspace()` dependency tested
- [ ] `/ai/jobs` endpoint enforces workspace isolation
- [ ] `/ai/execute` endpoint validates workspace_id
- [ ] Read-routing prioritizes new schema
- [ ] `list_jobs()` scans new schema when workspace_id provided
- [ ] 10+ isolation tests passing
- [ ] All existing tests still passing (36+ tests)
- [ ] Security-Reviewer agent review PASS
- [ ] Code-Reviewer agent review PASS

### Optional (Backfill):
- [ ] Backfill script tested with dry-run
- [ ] Backfill monitoring added to Grafana dashboard
- [ ] Backfill executed in staging environment

---

## Deployment Plan

### Phase 2.1: Webapi Security Fixes
1. Merge webapi fixes to main
2. Deploy to staging
3. Run isolation tests
4. Canary rollout (same 3-day pattern as Phase 1)

### Phase 2.2: Read Routing
1. Merge read-routing changes to main
2. Deploy to staging (flag still=on from Phase 1)
3. Verify new schema reads working
4. Full production rollout

### Phase 2.3: Backfill (Optional)
1. Run backfill script in dry-run mode
2. Execute backfill in staging
3. Validate consistency (old/new keys identical)
4. Execute backfill in production (off-peak hours)

---

## Rollback Plan

**If webapi fixes cause issues**:
1. Revert webapi changes (old schema still intact)
2. Roll back to v0.1.5-phase1
3. Fix issues, re-test, re-deploy

**If read-routing causes issues**:
1. Read fallback already in place (graceful degradation)
2. Monitor fallback rate via telemetry
3. Fix issues in hotfix PR

---

## References

- **Security Ticket**: `SECURITY_TICKET_S60_WEBAPI.md`
- **Phase 1 Checkpoint**: `SPRINT_60_PHASE_1_CHECKPOINT.md`
- **Deployment Checklist**: `SPRINT_60_CANARY_DEPLOYMENT_CHECKLIST.md`
- **Telemetry Dashboard**: `grafana-dashboard-sprint60-phase1.json`

---

## Estimated Timeline

| Task | Effort | Dependencies |
|------|--------|--------------|
| 1.1: Auth dependency | 2 hours | None |
| 1.2: Fix /ai/jobs | 3 hours | 1.1 |
| 1.3: Fix /ai/execute | 3 hours | 1.1 |
| 2.1: Update get_job() | 2 hours | Phase 1 stable |
| 2.2: Update list_jobs() | 2 hours | Phase 1 stable |
| 3.1: Backfill script | 3 hours | 2.1, 2.2 (optional) |
| 3.2: Backfill monitoring | 2 hours | 3.1 (optional) |
| 4: Isolation tests | 3 hours | 1.1, 1.2, 1.3 |

**Total**: 15-20 hours (excluding optional backfill: 10-15 hours)

---

## Success Metrics

After Phase 2 deployment:
- [ ] Zero workspace isolation bypass incidents
- [ ] 100% of reads use new schema (when workspace_id provided)
- [ ] `list_jobs()` performance improved (workspace-scoped keys faster)
- [ ] All isolation tests passing
- [ ] No regressions in existing functionality
- [ ] Ready for Phase 3 (primary schema switch)
