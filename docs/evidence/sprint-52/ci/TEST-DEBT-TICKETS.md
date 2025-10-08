# Test Debt Tracking Tickets - Sprint 52

**Created:** 2025-10-08
**Sprint:** 52 (Platform Alignment)
**Purpose:** Track technical debt for quarantined tests

---

## Meta-Ticket: Sprint 52 Test Quarantine Resolution

**Epic:** Restore full-green CI for sprint/52-platform-alignment
**Target:** Sprint 53-54
**Total Tests:** 40 (5 categories)

---

## S53-TEST-001: Install or Mock Streamlit Dependency

**Priority:** P2 (Low)
**Affected Tests:** 4
**File:** `tests/test_connector_dashboard_panel.py`

### Problem
Tests require `streamlit` package which is not in core dependencies. All 4 tests fail with:
```
ModuleNotFoundError: No module named 'streamlit'
```

### Acceptance Criteria
- [ ] **Option A:** Add streamlit to dev dependencies (`requirements-dev.txt`)
  - Pros: Tests run as-is
  - Cons: Heavy dependency (~50MB) for dashboard rendering tests
- [ ] **Option B:** Create lightweight stubs/mocks for streamlit UI components
  - Pros: No new dependency, faster tests
  - Cons: May not catch real streamlit API changes
- [ ] **Option C:** Convert to integration tests (mark as `@pytest.mark.live`)
  - Pros: Skip by default, run only when explicitly needed
  - Cons: Reduces test coverage in default CI runs

**Recommended:** Option B (stubs) or C (integration marker)

### Effort Estimate
- Option A: 10 minutes
- Option B: 1-2 hours
- Option C: 30 minutes

**Assigned:** Unassigned
**Sprint:** 53 or 54 (low priority)

---

## S53-TEST-002: Restore Missing create_artifacts Function

**Priority:** P1 (High)
**Affected Tests:** 13
**File:** `tests/test_archive_rotation_workflow.py`

### Problem
Tests import `create_artifacts` from `src.workflows.stress.archive_rotation_demo` but function doesn't exist. All 13 tests fail with:
```
ImportError: cannot import name 'create_artifacts' from 'src.workflows.stress.archive_rotation_demo'
```

### Acceptance Criteria
- [ ] **Option A:** Restore `create_artifacts()` function to `src/workflows/stress/archive_rotation_demo.py`
  - Check git history for original implementation
  - Verify function signature matches test expectations
- [ ] **Option B:** Update tests to use new API (if function was intentionally removed/renamed)
  - Find replacement function in codebase
  - Update all 13 test imports
- [ ] **Option C:** Stub the function for test purposes
  - Create minimal implementation that satisfies test fixtures
  - Generate realistic test artifacts

**Recommended:** Option A (restore from git history)

### Investigation
```bash
# Find when create_artifacts was last present
git log --all --full-history --oneline -- "*archive_rotation_demo.py" | head -20

# Check recent commits that modified this file
git log --all --oneline --grep="archive" | head -10
```

### Effort Estimate
- Option A: 30-60 minutes (if found in git history)
- Option B: 2-3 hours (if full refactor needed)
- Option C: 1-2 hours (if stub approach)

**Assigned:** Unassigned
**Sprint:** 53 (high priority - 13 tests affected)

---

## S53-TEST-003: Migrate to Ephemeral Port Allocation

**Priority:** P2 (Medium)
**Affected Tests:** 6
**File:** `tests/test_health_endpoints.py`

### Problem
Health server tests use fixed port `18086` which causes conflicts when tests run in parallel (`pytest-xdist`):
```
OSError: [Errno 98] Address already in use
```

### Acceptance Criteria
- [ ] Update `health_server` fixture to bind to port 0 (OS-assigned ephemeral port)
- [ ] Retrieve actual port from server after binding
- [ ] Pass dynamic port to test HTTP connections
- [ ] Verify tests pass with `pytest -n auto` (parallel execution)

### Implementation Sketch
```python
@pytest.fixture
def health_server():
    """Start health server on ephemeral port (OS-assigned)."""
    port = 0  # OS picks available port
    server = start_health_server(port)
    actual_port = server.server_port  # Get assigned port
    os.environ["HEALTH_PORT"] = str(actual_port)

    yield actual_port

    server.shutdown()
```

### Effort Estimate
1-2 hours (refactor fixture + update all tests)

**Assigned:** Unassigned
**Sprint:** 53 (medium priority - enables parallel test execution)

---

## S53-TEST-004: Update Scheduler/Queue API Signatures

**Priority:** P1 (High)
**Affected Tests:** 4
**Files:** `tests/test_queue_strategy.py`, `tests/test_scheduler_core.py`

### Problem
Tests use deprecated API signatures that are no longer compatible with current implementation:

1. `test_enqueue_task_convenience`: `sample_task_function() got an unexpected keyword argument 'args'`
2. `test_tick_once_*`: `tick_once() missing 1 required positional argument: 'dedup_cache'`

### Acceptance Criteria
- [ ] **Option A:** Update test calls to match new API signatures
  - Review current function signatures in `src/queue/`, `src/scheduler/`
  - Update test function calls with correct parameters
  - Verify tests pass with new signatures
- [ ] **Option B:** Add backward-compatibility shims to production code
  - Detect old-style calls and adapt internally
  - Emit deprecation warnings
  - Update tests to use new API (migration path)

**Recommended:** Option A (update tests to new API)

### Investigation
```python
# Check current signatures
from src.queue.strategy import enqueue_task
from src.scheduler.core import tick_once

import inspect
print(inspect.signature(enqueue_task))
print(inspect.signature(tick_once))
```

### Effort Estimate
- Option A: 30-60 minutes (update 4 tests)
- Option B: 2-3 hours (add compat layer + update tests)

**Assigned:** Unassigned
**Sprint:** 53 (high priority - scheduler/queue are core subsystems)

---

## S53-TEST-005: Fix Business Logic Assertion Failures

**Priority:** P0/P1 (Critical - 11 CLI tests, P2 - 2 misc tests)
**Affected Tests:** 13
**Files:** `tests/test_connectors_cli.py` (11), `tests/test_lifecycle.py` (1), `tests/test_negative_paths.py` (1), `tests/test_nightshift_e2e.py` (1)

### Problem
Multiple tests have assertion failures indicating business logic bugs or incorrect test expectations.

#### Sub-ticket 5A: Connectors CLI Exit Codes (11 tests)
**File:** `tests/test_connectors_cli.py`

**Symptom:** Tests expect exit code 0 or 1, but CLI returns exit code 2 (argument parsing error)

Example:
```
AssertionError: assert 2 == 0
# CLI returned: connectors.py: error: unrecognized arguments: --user user1 --tenant default
```

**Root Cause:** CLI argument parser changed or tests use incorrect flags

**Acceptance Criteria:**
- [ ] Review `src/connectors/cli.py` argument parser definition
- [ ] Verify tests use correct flag names (`--user` vs `--username`, etc.)
- [ ] Fix either CLI parser or test invocations to align
- [ ] Verify RBAC checks work as expected (test 6 expects "RBAC denied" in output)

**Effort:** 1-2 hours (review CLI changes + update 11 tests)

#### Sub-ticket 5B: Lifecycle Job Assertion (1 test)
**File:** `tests/test_lifecycle.py`
**Test:** `test_run_lifecycle_job_full_cycle`
**Error:** `assert 2 == 1`

**Investigation Needed:**
- What does the `2` represent? (exit code? job count? status enum?)
- Review lifecycle job execution logic
- Confirm expected behavior

**Effort:** 30 minutes

#### Sub-ticket 5C: Citation Disqualification Logic (1 test)
**File:** `tests/test_negative_paths.py`
**Test:** `test_citation_disqualification_logic`
**Error:** `assert 0 == 1`

**Investigation Needed:**
- Review citation counting/filtering logic in judge/debate modules
- Confirm disqualification rules (how many citations trigger disqualification?)
- Update test expectations or fix citation logic

**Effort:** 30-60 minutes

#### Sub-ticket 5D: Policy Parameter Parsing (1 test)
**File:** `tests/test_nightshift_e2e.py`
**Test:** `test_policy_parameter_parsing`
**Error:** `AssertionError: assert 'openai_only' == 'openai_preferred'`

**Investigation Needed:**
- Review policy parameter parsing in nightshift workflow
- Check if policy names changed ('openai_preferred' → 'openai_only')
- Update test expectations or fix parsing logic

**Effort:** 15-30 minutes

### Total Effort Estimate
3-5 hours (all sub-tickets combined)

**Assigned:** Unassigned
**Sprint:** 53 (P0/P1 - CLI tests critical, others can defer to 54)

---

## Burn-Down Plan

### Sprint 53 Targets (High Priority)
1. ✅ S53-TEST-002 (13 tests) - Restore create_artifacts function
2. ✅ S53-TEST-004 (4 tests) - Update scheduler/queue API signatures
3. ✅ S53-TEST-005A (11 tests) - Fix connectors CLI exit codes

**Total:** 28 tests resolved → 70% coverage restored

### Sprint 54 Targets (Medium/Low Priority)
4. ✅ S53-TEST-003 (6 tests) - Ephemeral ports for health endpoints
5. ✅ S53-TEST-005B/C/D (2 tests) - Misc business logic fixes
6. ✅ S53-TEST-001 (4 tests) - Streamlit stubs or integration marker

**Total:** 12 tests resolved → 100% coverage restored

---

## Success Criteria

- [ ] All 40 quarantined tests passing (RELAY_RUN_ALL=1 pytest -q)
- [ ] CI validate job green with full test suite (no marker exclusions)
- [ ] No xfail or skip markers remaining (except intentional integration tests)
- [ ] Test execution time remains < 2 minutes for PR suite

**Target Date:** End of Sprint 54 (2 sprints from now)

---

**Document Owner:** Platform Team
**Last Updated:** 2025-10-08
**Next Review:** Sprint 53 Retrospective
