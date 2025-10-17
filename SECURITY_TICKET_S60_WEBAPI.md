# Security Ticket: Workspace Isolation in /ai/* Endpoints (Sprint 60 Follow-Up)

**Created**: 2025-10-17
**Sprint**: Sprint 60 Phase 1 Follow-Up
**Priority**: HIGH (CRITICAL for multi-tenant production)
**Affects**: src/webapi.py (Lines 217-350)
**Status**: Blocked on Sprint 60 Phase 1 completion

---

## Summary

During Sprint 60 Phase 1 gate review (dual-write migration), Security-Reviewer and Code-Reviewer agents identified **3 pre-existing security issues** in `src/webapi.py` that affect workspace isolation:

1. **CRITICAL-2**: Workspace isolation bypass in `/ai/jobs` endpoint
2. **CRITICAL-3**: Workspace_id injection via request body in `/ai/execute`
3. **HIGH-4**: Missing workspace isolation in `/ai/jobs` pagination

These issues are **OUT OF SCOPE** for Sprint 60 Phase 1 (dual-write migration) but must be fixed before the system handles multi-tenant production traffic.

---

## Issues Detail

### CRITICAL-2: Workspace Isolation Bypass in `/ai/jobs`

**File**: `src/webapi.py`
**Lines**: 217-253 (`GET /ai/jobs`)

**Issue**:
The `/ai/jobs` endpoint accepts `workspace_id` as a **query parameter** without verifying the authenticated user has permission to access that workspace:

```python
@app.get("/ai/jobs")
@require_scopes(["ai:jobs:read"])
async def list_ai_jobs(workspace_id: str | None = None, ...):
    """List AI orchestrator jobs with optional workspace filter."""
    # ISSUE: workspace_id from query param, no RBAC check
    jobs = queue.list_jobs(workspace_id=workspace_id, ...)
    return {"jobs": jobs}
```

**Attack Scenario**:
1. Attacker authenticates as `user@workspace-a.com`
2. Attacker calls `GET /ai/jobs?workspace_id=workspace-b`
3. System returns jobs from `workspace-b` (unauthorized access)

**Impact**: Multi-tenant data leak (CRITICAL)

**CVSS**: 8.1 (High) - AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N

---

### CRITICAL-3: Workspace_id Injection via Request Body

**File**: `src/webapi.py`
**Lines**: 279-350 (`POST /ai/execute`)

**Issue**:
The `/ai/execute` endpoint accepts `workspace_id` in the **request body** without verifying it matches the authenticated user's workspace:

```python
@app.post("/ai/execute")
@require_scopes(["ai:execute"])
async def execute_ai_action(body: ExecuteRequest, ...):
    """Execute AI action with orchestration."""
    # ISSUE: body.workspace_id from client, no RBAC check
    job_id = await orchestrator.enqueue_job(
        workspace_id=body.workspace_id,  # Attacker-controlled
        ...
    )
```

**Attack Scenario**:
1. Attacker authenticates as `user@workspace-a.com`
2. Attacker sends `POST /ai/execute` with `{"workspace_id": "workspace-b", ...}`
3. Job is enqueued under `workspace-b` (privilege escalation)
4. Attacker can now list jobs via CRITICAL-2

**Impact**: Privilege escalation + cross-tenant data pollution (CRITICAL)

**CVSS**: 8.8 (High) - AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:H/A:N

---

### HIGH-4: Missing Workspace Isolation in `/ai/jobs` Pagination

**File**: `src/webapi.py`
**Lines**: 217-253 (`GET /ai/jobs`)

**Issue**:
When `workspace_id=None` (not provided), the endpoint returns jobs from **all workspaces** (Sprint 55 Week 3 behavior):

```python
@app.get("/ai/jobs")
@require_scopes(["ai:jobs:read"])
async def list_ai_jobs(workspace_id: str | None = None, ...):
    """List AI orchestrator jobs with optional workspace filter."""
    # ISSUE: workspace_id=None returns all workspaces
    jobs = queue.list_jobs(workspace_id=workspace_id, ...)  # No filter!
    return {"jobs": jobs}
```

**Attack Scenario**:
1. Attacker authenticates as `user@workspace-a.com`
2. Attacker calls `GET /ai/jobs` (no workspace_id param)
3. System returns jobs from all workspaces

**Impact**: Multi-tenant data leak (HIGH)

**CVSS**: 7.5 (High) - AV:N/AC:L/PR:L/UI:N/S:U/C:H/I:N/A:N

---

## Root Cause Analysis

All three issues stem from a **missing workspace context extraction layer** in the webapi:

1. **No workspace resolution from auth token**: The `@require_scopes` decorator verifies scopes but does **not** extract the authenticated user's workspace_id.

2. **Client-controlled workspace_id**: Both endpoints trust the client to provide the correct workspace_id (query param or body).

3. **No RBAC check**: There is no check like `if workspace_id != auth_context.workspace_id: raise PermissionError`.

This pattern was acceptable in Sprint 55 Week 3 (single-tenant prototype) but is **unsafe for multi-tenant production**.

---

## Proposed Fix Plan

### Step 1: Extract Workspace from Auth Token

Add a `get_workspace_from_token()` dependency in `src/webapi.py`:

```python
from fastapi import Depends, HTTPException, status
from src.auth import extract_workspace_id_from_token

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

### Step 2: Fix `/ai/jobs` Endpoint (CRITICAL-2, HIGH-4)

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
    ...
):
    # RBAC check: If workspace_id provided, must match authenticated workspace
    if workspace_id is not None and workspace_id != auth_workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot access jobs from other workspaces"
        )

    # Always filter by authenticated workspace (ignore client-provided value)
    jobs = queue.list_jobs(workspace_id=auth_workspace_id, ...)
    return {"jobs": jobs}
```

### Step 3: Fix `/ai/execute` Endpoint (CRITICAL-3)

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
    # RBAC check: Reject if body.workspace_id doesn't match auth
    if body.workspace_id != auth_workspace_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot execute actions in other workspaces"
        )

    job_id = await orchestrator.enqueue_job(
        workspace_id=auth_workspace_id,  # Use authenticated workspace
        ...
    )
```

### Step 4: Add Tests

Create `tests/test_webapi_workspace_isolation.py`:

```python
def test_list_jobs_enforces_workspace_isolation():
    """GET /ai/jobs filters by authenticated workspace only."""
    # User authenticated for workspace-a
    client = TestClient(app, headers={"Authorization": "Bearer workspace-a-token"})

    # Attempt to access workspace-b jobs
    response = client.get("/ai/jobs?workspace_id=workspace-b")

    assert response.status_code == 403
    assert "Cannot access jobs from other workspaces" in response.json()["detail"]

def test_execute_rejects_cross_workspace_injection():
    """POST /ai/execute rejects workspace_id injection."""
    # User authenticated for workspace-a
    client = TestClient(app, headers={"Authorization": "Bearer workspace-a-token"})

    # Attempt to execute in workspace-b
    response = client.post("/ai/execute", json={
        "workspace_id": "workspace-b",
        "action_provider": "google",
        "action_name": "gmail.send",
        "params": {"to": "test@example.com"}
    })

    assert response.status_code == 403
    assert "Cannot execute actions in other workspaces" in response.json()["detail"]
```

---

## Implementation Timeline

| Phase | Task | Effort | Blocker |
|-------|------|--------|---------|
| **Phase 0** | Sprint 60 Phase 1 completion (dual-write) | - | Current work |
| **Phase 1** | Implement `get_authenticated_workspace()` helper | 2 hours | Sprint 60 P1 merge |
| **Phase 2** | Fix `/ai/jobs` endpoint (CRITICAL-2, HIGH-4) | 2 hours | Phase 1 |
| **Phase 3** | Fix `/ai/execute` endpoint (CRITICAL-3) | 2 hours | Phase 1 |
| **Phase 4** | Add 10+ tests for workspace isolation | 3 hours | Phase 2+3 |
| **Phase 5** | Security re-review (Security-Reviewer agent) | 1 hour | Phase 4 |

**Total Effort**: ~10 hours (2-3 days)

---

## Dependencies

1. **Sprint 60 Phase 1 must merge first**: This ticket addresses pre-existing issues but should not block Sprint 60 Phase 1 (dual-write migration).

2. **Auth token format**: Need to confirm auth token includes `workspace_id` claim (verify with Sprint 55 Week 3 implementation).

3. **Test environment**: Need multi-workspace test data for isolation tests.

---

## Acceptance Criteria

- [ ] `get_authenticated_workspace()` dependency implemented
- [ ] `/ai/jobs` endpoint filters by authenticated workspace only
- [ ] `/ai/execute` endpoint validates workspace_id matches auth token
- [ ] 10+ tests covering workspace isolation scenarios
- [ ] Security-Reviewer agent review passes
- [ ] No regression in existing tests (30+ tests still passing)

---

## References

- **Sprint 60 Phase 1 Code Review**: `SPRINT_60_PHASE_1_CODE_REVIEW.md`
- **Sprint 60 Review Summary**: `SPRINT_60_REVIEW_SUMMARY.txt`
- **Security-Reviewer Output**: (see agent review transcript)
- **Sprint 55 Week 3 Auth**: `src/auth.py` (token validation logic)

---

## Notes

- This ticket is **separate from Sprint 60 Phase 1** to avoid scope creep.
- These issues existed before Sprint 60 and are not introduced by dual-write changes.
- Fixing these issues is **mandatory before multi-tenant production deployment**.
