# Recommended Patterns: Sprint 60 Dual-Write Migration

**For:** Tech Leads, Backend Engineers
**Scope:** AI Orchestrator v0.1 to v0.1.5+ evolution
**Context:** PR #42 establishes v0.1 baseline; this document guides v0.1.5 Phase 1-3 migration

---

## Pattern 1: Feature Flag with Gradual Rollout

**When to Use:** Schema migrations, behavior changes in multi-tenant systems

**Pattern:**
```python
# src/queue/simple_queue.py - Dual-write implementation

ENABLE_NEW_SCHEMA = os.getenv("AI_JOBS_NEW_SCHEMA", "off").lower() == "on"

def enqueue(self, job_id: str, ..., workspace_id: str, ...) -> bool:
    """Enqueue job with dual-write support for schema migration."""

    # Always write to old schema (for backwards compatibility)
    job_key_old = f"ai:jobs:{job_id}"
    self._redis.hset(job_key_old, mapping=job_data)
    self._redis.rpush(self._queue_key, job_id)

    # Conditionally write to new schema (feature flag controlled)
    if ENABLE_NEW_SCHEMA:
        job_key_new = f"ai:job:{workspace_id}:{job_id}"
        self._redis.hset(job_key_new, mapping=job_data)

    return True
```

**Benefits:**
- Zero-downtime migration (dual-write for overlap period)
- Easy rollback (disable flag, old data still available)
- Validation period (confirm new schema works before cutover)
- Production-safe (no surprise failures)

**Anti-Pattern to Avoid:**
```python
# WRONG: Conditional logic in business logic
if workspace_id:
    # new behavior
else:
    # old behavior
```
This scatters concerns and makes testing harder.

**Best Practice:**
- Feature flag lives in ONE place (top of module)
- Business logic doesn't check flag directly
- Abstraction layer (SimpleQueue) handles it
- Endpoint code unchanged

**S60 Rollout Timeline:**
1. **Phase 1 (Week 1):** Enable dual-write in staging only
   - Seed new schema with 100% of writes
   - Compare old vs new via data dumps
   - Monitor CPU/memory impact

2. **Phase 1 (Week 2):** Enable dual-write in prod (feature flag off)
   - Write to both schemas, read from old only
   - Validate new schema silently accrues data
   - Measure latency impact (should be ~0ms)

3. **Phase 2 (Week 3):** Flip read path
   - Set `AI_JOBS_NEW_SCHEMA=on` in prod
   - Read from new schema directly
   - Monitor error rates (expect 0% change)

4. **Phase 3 (Week 4):** Cleanup
   - Disable old schema writes
   - Delete ai:job:* (old keys) after validation
   - Remove feature flag code

---

## Pattern 2: Interface Abstraction for Storage

**When to Use:** Any component that might have multiple implementations (Redis, DB, in-memory)

**Pattern:**
```python
# src/queue/simple_queue.py - Abstract interface

class JobQueue(Protocol):
    """Abstract job queue interface (supports any backend)."""

    def enqueue(self, job_id: str, ...) -> bool:
        """Add job to queue."""
        ...

    def dequeue(self) -> dict | None:
        """Fetch next job from queue."""
        ...

    def get_job(self, job_id: str) -> dict | None:
        """Fetch job by ID."""
        ...

    def update_status(self, job_id: str, status: str, result: dict | None = None) -> None:
        """Update job status."""
        ...

# Concrete implementation
class SimpleQueue:
    """Redis-backed job queue."""

    def __init__(self, redis_url: str | None = None):
        """Initialize with Redis connection."""
        url = redis_url or os.getenv("REDIS_URL", "redis://localhost:6379")
        self._redis = redis.from_url(url, decode_responses=True)

    def enqueue(self, ...) -> bool:
        # Implementation...
        pass
```

**Benefits:**
- Endpoint code doesn't care about storage backend
- Easy to test (inject mock queue)
- Easy to swap implementations (e.g., add PostgreSQL queue)
- Future: Sharded queue, queue with persistence, etc.

**How Endpoint Uses It:**
```python
# src/webapi.py
@app.get("/ai/jobs")
async def list_ai_jobs(request: Request, ...):
    """List jobs (backend-agnostic)."""
    try:
        queue = SimpleQueue()  # Could be any JobQueue implementation
    except ValueError as e:
        raise HTTPException(status_code=503, detail=f"Queue unavailable: {str(e)}") from e

    # Use queue interface (doesn't care it's Redis)
    jobs = []
    cursor_int, keys = queue.redis.scan(cursor_int, match=pattern, count=limit * 2)
    # ... rest of logic
```

**Migration-Friendly:**
In S60 Phase 2, if you need to change key format, change SimpleQueue. Endpoint doesn't change.

---

## Pattern 3: Workspace Scoping at Boundaries

**When to Use:** Multi-tenant systems where data isolation is a security requirement

**Pattern:**
```python
# src/webapi.py - Request boundary (entry point)
@app.get("/ai/jobs")
@require_scopes(["actions:preview"])  # Auth guard (boundary 1)
async def list_ai_jobs(request: Request, cursor: str | None = None, limit: int = 50):
    """List jobs (workspace-scoped)."""

    # Boundary 2: Extract workspace from auth context
    workspace_id = getattr(request.state, "workspace_id", None)
    if not workspace_id:
        raise HTTPException(status_code=403, detail="workspace_id required")

    # Boundary 3: Validate format (prevents injection)
    from src.telemetry.prom import canonical_workspace_id
    if is_workspace_label_enabled():
        validated_ws_id = canonical_workspace_id(workspace_id)
        if not validated_ws_id:
            raise HTTPException(status_code=403, detail="workspace_id invalid or not allowlisted")

    # Boundary 4: Filter results (application layer)
    queue = SimpleQueue()
    jobs = []
    # ... SCAN and filter loop (lines 1527-1567)

    # Only return jobs from this workspace
    return {
        "workspace_id": workspace_id,
        "jobs": jobs,  # All jobs in list belong to workspace_id
        # ...
    }
```

**Anti-Patterns to Avoid:**

```python
# WRONG: Workspace check buried in the middle
def list_ai_jobs(request: Request, job_id: str = None):
    # ... 50 lines of logic ...
    if request.state.workspace_id != job_id.workspace_id:  # Hidden check
        raise HTTPException(403)
    # ... more logic ...
```

```python
# WRONG: Conditional behavior based on workspace
def list_ai_jobs(request: Request):
    if request.state.workspace_id == "admin":
        return all_jobs()  # Admin sees everything
    else:
        return filtered_jobs()  # Regular user restricted
```

**Best Practice:**
1. **Establish workspace at request entry** (top of endpoint)
2. **Fail fast if missing** (403 immediately, don't continue)
3. **Filter consistently** (same logic for all endpoints)
4. **Return workspace in response** (client confirms isolation)

**S60 Application:**
When migrating to `ai:job:{workspace_id}:{job_id}` schema:
```python
# Phase 2: Read path migration
if ENABLE_NEW_SCHEMA:
    # Direct SCAN on workspace pattern (no app-layer filter needed)
    pattern = f"ai:job:{workspace_id}:*"
    cursor_int, keys = queue.redis.scan(cursor_int, match=pattern, count=limit)
    # Remove the workspace filter loop (lines 1527-1567)
else:
    # Old hotfix (Phase 1): SCAN all, filter in app
    pattern = "ai:job:*"
    cursor_int, keys = queue.redis.scan(cursor_int, match=pattern, count=limit * 2)
    # Keep workspace filter loop
```

---

## Pattern 4: PII Redaction Strategy

**When to Use:** APIs that expose user input (params, queries, form fields)

**Pattern:**
```python
# Redacted in responses
- Params: User input (contains secrets, PII) → REDACT
- Result: Action output (already filtered by action logic) → INCLUDE
- Error: Generic message (don't leak internals) → GENERIC

# src/schemas/ai_plan.py
SENSITIVE_KEYS = {
    "password", "token", "authorization", "api_key", "apiKey",
    "secret", "bearer", "access_token", "refresh_token", "auth",
}

def safe_dict(self) -> dict[str, Any]:
    """Export with sensitive fields redacted."""
    def redact_sensitive(obj: Any) -> Any:
        if isinstance(obj, dict):
            return {
                k: "***REDACTED***" if k.lower() in SENSITIVE_KEYS else redact_sensitive(v)
                for k, v in obj.items()
            }
        if isinstance(obj, list):
            return [redact_sensitive(v) for v in obj]
        return obj

    data = self.model_dump()
    for step in data.get("steps", []):
        step["params"] = redact_sensitive(step.get("params", {}))
    return data

# Usage in endpoint
return {
    **plan.safe_dict(),  # Redacted
    "request_id": request_id,
}
```

**Anti-Patterns to Avoid:**

```python
# WRONG: Redact everything (loses useful information)
job_summary = {
    "job_id": "***REDACTED***",
    "status": "***REDACTED***",
    "result": "***REDACTED***",
}
# Client can't do anything with this!

# WRONG: Expose full params
job_summary = {
    "job_id": "job_123",
    "params": {"api_key": "sk_live_1234567890", "email": "user@company.com"},
    # Secrets leaked!
}

# WRONG: Ad-hoc redaction (inconsistent)
if "password" in params:
    params["password"] = "***"
elif "token" in params:
    params["token"] = "***"
# Many cases missed, easy to forget
```

**Best Practice:**
1. **Identify sensitive keys** (password, token, api_key, etc.)
2. **Redact consistently** (centralized function, not scattered)
3. **Include actionable fields** (job_id, status, result, timestamps)
4. **Log conservative warnings** (don't log redacted values)

**S60 Application:**
When adding new action types, update `SENSITIVE_KEYS` immediately.

---

## Pattern 5: Cursor-Based Pagination for Large Result Sets

**When to Use:** Results that don't fit in memory, especially with filtering/sharding

**Pattern:**
```python
# src/webapi.py - Stateless cursor pagination
@app.get("/ai/jobs")
async def list_ai_jobs(request: Request, cursor: str | None = None, limit: int = 50):
    """List jobs with cursor-based pagination (stateless)."""

    # Parse cursor (prevent injection)
    try:
        cursor_int = int(cursor) if cursor else 0
    except (ValueError, TypeError) as e:
        raise HTTPException(status_code=400, detail="Invalid cursor format (must be integer)") from e

    # SCAN loop (stateless)
    jobs = []
    while True:
        cursor_int, job_keys_batch = queue.redis.scan(
            cursor_int, match=pattern, count=limit * 2
        )

        # Process batch
        for job_key in job_keys_batch:
            if len(jobs) >= limit:
                break

            job_data = queue.redis.hgetall(job_key)
            if not job_data:
                continue

            # Filter by workspace
            if job_data.get("workspace_id") != workspace_id:
                continue

            jobs.append({...})  # Add to results

        # Exit conditions
        if len(jobs) >= limit or cursor_int == 0:
            break

    # Response
    return {
        "jobs": jobs,
        "count": len(jobs),
        "next_cursor": str(cursor_int) if cursor_int else None,
    }

# Client usage
# GET /ai/jobs?limit=50 → first page, next_cursor=1234
# GET /ai/jobs?cursor=1234&limit=50 → next page, next_cursor=5678
# GET /ai/jobs?cursor=5678&limit=50 → last page, next_cursor=None
```

**Benefits:**
- **Stateless server** (no session storage)
- **Consistent results** (SCAN is atomic per cursor)
- **Memory efficient** (don't load all results)
- **Scalable** (works with large result sets)
- **Backward compatible** (client controls pagination)

**Anti-Pattern to Avoid:**

```python
# WRONG: Offset-based pagination (bad at scale)
@app.get("/ai/jobs")
async def list_ai_jobs(offset: int = 0, limit: int = 50):
    # Fetch from offset
    jobs = queue.list_jobs(offset=offset, limit=limit)
    # Problem: SKIP N items is O(N) with SCAN
    # With 1M items and offset=900K, very slow!
```

**S60 Optimization:**
In Phase 2, remove the `limit * 2` buffer and filtering loop:
```python
# OLD (Phase 1): SCAN all keys, filter in app
cursor_int, keys = queue.redis.scan(cursor_int, match="ai:job:*", count=limit * 2)

# NEW (Phase 2): SCAN workspace pattern directly
cursor_int, keys = queue.redis.scan(cursor_int, match=f"ai:job:{workspace_id}:*", count=limit)
# No filtering loop needed, SCAN efficiency = 100%
```

---

## Pattern 6: Exception Chaining for Debugging

**When to Use:** Any error handling where context is important

**Pattern:**
```python
# src/webapi.py - Exception chaining with 'from e'
try:
    cursor_int = int(cursor) if cursor else 0
except (ValueError, TypeError) as e:
    # CORRECT: Chain exception to preserve context
    raise HTTPException(
        status_code=400,
        detail="Invalid cursor format (must be integer)"
    ) from e
    # ^ "from e" preserves stack trace for debugging

# Anti-pattern: Silent swallow
try:
    cursor_int = int(cursor) if cursor else 0
except (ValueError, TypeError):
    # WRONG: Lost original error, harder to debug
    raise HTTPException(status_code=400, detail="Invalid cursor")
```

**Why It Matters:**
```
# With "from e" (GOOD debugging):
Traceback (most recent call last):
  File "/app/webapi.py", line 1520, in list_ai_jobs
    cursor_int = int(cursor) if cursor else 0
ValueError: invalid literal for int() with base 10: 'not_a_number'

During handling of the above exception, another exception occurred:
HTTPException: status_code=400, detail="Invalid cursor format (must be integer)"

# Without "from e" (BAD - original error hidden):
HTTPException: status_code=400, detail="Invalid cursor"
# ^ No idea what actually failed!
```

**Best Practice:**
- Always use `from e` when re-raising
- Include original exception message in detail if safe
- Don't leak internals (use generic messages for client)
- Log full exception internally (for debugging)

---

## Pattern 7: Safe-by-Default Telemetry

**When to Use:** Optional features that could impact production (cardinality, performance)

**Pattern:**
```python
# src/telemetry/prom.py - Flag-gated feature
def is_workspace_label_enabled() -> bool:
    """Check if workspace_id label should be attached to metrics."""
    return str(os.getenv("METRICS_WORKSPACE_LABEL", "off")).lower() == "on"

def record_job_list_query(workspace_id: str | None, count: int, seconds: float) -> None:
    """Record query metrics with optional workspace scoping."""
    if not _PROM_AVAILABLE or not _METRICS_INITIALIZED:
        return

    try:
        # Default to "unscoped" when workspace_id not provided or feature disabled
        ws_label = workspace_id if workspace_id and is_workspace_label_enabled() else "unscoped"

        _ai_job_list_queries_total.labels(workspace_id=ws_label).inc()
        _ai_job_list_duration_seconds.labels(workspace_id=ws_label).observe(seconds)
        _ai_job_list_results_total.labels(workspace_id=ws_label).inc(count)
    except Exception as exc:
        _LOG.warning("Failed to record job list query metric: %s", exc)
```

**Benefits:**
- **Opt-in risk** (feature disabled by default)
- **Cardinality bounded** (allowlist or "unscoped" default)
- **Observability** (can enable in staging, disable in prod)
- **Safe-by-default** (no surprises if misconfigured)

**S60 Application:**
When adding new observability features:
1. Create feature flag (e.g., `ENABLE_FEATURE=off`)
2. Validate before use
3. Provide safe default (usually "unscoped" or no-op)
4. Document cardinality impact

---

## Pattern 8: Validation at Boundaries

**When to Use:** Any input from clients, environments, external APIs

**Pattern:**
```python
# src/telemetry/prom.py - Validation layer
_WORKSPACE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]{0,31}$")

def canonical_workspace_id(workspace_id: str | None) -> str | None:
    """Validate and canonicalize workspace_id (boundary validation)."""

    # Boundary 1: Type check
    if not workspace_id or not isinstance(workspace_id, str):
        return None

    # Boundary 2: Format validation (fullmatch prevents injection)
    if not _WORKSPACE_ID_PATTERN.fullmatch(workspace_id):
        _LOG.warning("Invalid workspace_id format: %s", workspace_id)
        return None

    # Boundary 3: Allowlist enforcement (if configured)
    allowlist_str = os.getenv("METRICS_WORKSPACE_ALLOWLIST", "")
    if allowlist_str:
        allowlist = {s.strip() for s in allowlist_str.split(",") if s.strip()}
        if workspace_id not in allowlist:
            _LOG.warning("workspace_id not in allowlist: %s", workspace_id)
            return None

    # All checks passed
    return workspace_id

# Usage in endpoint
@app.get("/ai/jobs")
async def list_ai_jobs(request: Request, ...):
    workspace_id = getattr(request.state, "workspace_id", None)
    if not workspace_id:
        raise HTTPException(status_code=403, detail="workspace_id required")

    # Validate at boundary
    if is_workspace_label_enabled():
        validated_ws_id = canonical_workspace_id(workspace_id)
        if not validated_ws_id:
            raise HTTPException(status_code=403, detail="workspace_id invalid")

    # Rest of logic uses validated workspace_id
    # ...
```

**Best Practice:**
1. **Validate at entry point** (not scattered throughout code)
2. **Use fullmatch() for regex** (prevents injection)
3. **Fail fast** (return None/raise immediately)
4. **Log validation failures** (for security audit)
5. **Document rules** (format, length, allowlist)

---

## Migration Checklist: S60 Phase 1-3

### Phase 1: Dual-Write Foundation (Week 1-2)
- [ ] Create feature flag: `AI_JOBS_NEW_SCHEMA=off`
- [ ] Implement dual-write in `SimpleQueue.enqueue()`
- [ ] Add tests for both schemas (old and new)
- [ ] Deploy to staging, validate data consistency
- [ ] Deploy to prod (feature flag OFF), enable silent dual-write

### Phase 2: Read Path Migration (Week 3)
- [ ] Implement conditional read logic in endpoint
- [ ] Add telemetry to track schema usage
- [ ] Test read path with new schema in staging
- [ ] Enable feature flag in prod: `AI_JOBS_NEW_SCHEMA=on`
- [ ] Monitor error rates (expect 0% degradation)

### Phase 3: Cleanup (Week 4)
- [ ] Disable old schema writes in `SimpleQueue`
- [ ] Delete `ai:job:*` keys (old schema)
- [ ] Remove feature flag from code
- [ ] Remove conditional logic from endpoint
- [ ] Update documentation

### Production Rollout
- [ ] Create runbook for flag enable/disable
- [ ] Set alerts for migration metrics
- [ ] Schedule rollback procedure (in case of issues)
- [ ] Plan communication to ops team

---

## Quick Reference: File Locations

**Patterns Implemented in PR #42:**

| Pattern | File | Lines |
|---|---|---|
| Feature Flag (temp) | `src/webapi.py` | 1512-1514 |
| Interface Abstraction | `src/queue/simple_queue.py` | 14-42 |
| Workspace Scoping | `src/webapi.py` | 1483-1495 |
| PII Redaction | `src/schemas/ai_plan.py` | 156-176 |
| Cursor Pagination | `src/webapi.py` | 1527-1567 |
| Exception Chaining | `src/webapi.py` | 1520-1522 |
| Safe-by-Default Telemetry | `src/telemetry/prom.py` | 710-729 |
| Validation at Boundaries | `src/telemetry/prom.py` | 100-128 |

**Tests for Patterns:**

| Pattern | Test File | Test Class |
|---|---|---|
| Workspace Validation | `tests/test_jobs_endpoint.py` | TestWorkspaceSecurityValidation |
| Cursor Pagination | `tests/test_jobs_endpoint.py` | TestCursorPaginationWithRedis |
| PII Redaction | `tests/test_jobs_endpoint.py` | TestJobListEndpointLogic |
| Workspace Formatting | `tests/test_workspace_metrics.py` | TestWorkspaceIdCanonical |

---

## Questions & Answers

**Q: Why use feature flags instead of just deploying new code?**
A: Feature flags allow zero-downtime cutover. If new schema has bugs, you disable the flag and revert instantly (no redeploy). With just code, you'd need rollback which takes 5-10 minutes.

**Q: Why not just migrate all data upfront?**
A: With 10M+ jobs, upfront migration takes hours and risks data loss. Dual-write allows gradual cutover while validating correctness.

**Q: What happens if dual-write fails?**
A: Old schema still has data. New schema is behind. When you disable `AI_JOBS_NEW_SCHEMA`, read path goes back to old (successful). No data loss.

**Q: Can we skip Phase 1 and go straight to new schema?**
A: Only if you have <1M jobs and can afford 10-minute downtime. Not recommended for production with SLA.

**Q: What's the performance impact of dual-write?**
A: Expected <5% latency increase (two Redis hset calls instead of one). Measured in staging before prod rollout.

**Q: How do we validate new schema works?**
A: In Phase 1, compare old vs new via data dumps. Parse both, verify field-by-field. Add alerts for discrepancies.

---

**Document Version:** 1.0
**Last Updated:** 2025-10-17
**Status:** Reference Material for Sprint 60+
