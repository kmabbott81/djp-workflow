# Sprint 60 Phase 1 Handoff — Sonnet 4.5

**Date**: 2025-10-17
**Status**: ✅ Ready for Model Switch
**Current Model**: Haiku 4.5 → **Switch to Sonnet 4.5**
**Branch**: `sprint-60/s60-dual-write-migration`
**Tag**: v0.1.4 (S59-05 hotfix complete)

---

## Sprint 59 Closure Summary

### ✅ S59-05 Hotfix Complete
- **Removed**: Duplicate `/ai/jobs` endpoint
- **Added**: Workspace-scoped telemetry labels
  - `ai_jobs_total` (workspace_id, status)
  - `ai_job_latency_seconds` (workspace_id)
  - `ai_queue_depth` (workspace_id)
  - `security_decisions_total` (workspace_id, result)
- **Fixed**: Critical telemetry recording errors (tuple unpacking, label mismatches)

### ✅ Test Results
- 14 critical tests **PASSED** (100%)
- Post-merge smoke test **PASSED**
- Pre-commit hooks **PASSED**

### ✅ Git State
- main@6642df0 (HEAD)
- v0.1.4 tagged and pushed to origin
- Clean working tree

---

## Sprint 60 Phase 1: Dual-Write Migration

### Goal
Migrate Redis key schema from:
```
ai:job:{job_id}                    # Current (hotfix with app-layer filtering)
                ↓
ai:job:{workspace_id}:{job_id}     # Target (workspace-scoped by design)
```

With **zero downtime**, **dual-write**, and **idempotent backfill**.

### Migration Phases

**Phase 1: Dual-Write**
- Deploy code that writes to BOTH `ai:job:{job_id}` (legacy) AND `ai:job:{workspace_id}:{job_id}` (new)
- Reads still use legacy key pattern (old filtering logic active)
- Canary: 10% of new jobs → new schema
- Duration: ~48 hours (monitor metrics, no rollbacks)

**Phase 2: Read Routing** (depends on Phase 1 stability)
- Read logic checks new key pattern first, falls back to legacy
- Async backfill starts (copy missing legacy jobs to new schema)
- Canary: 50% of reads → new key pattern

**Phase 3: Backfill & Verify** (depends on Phase 2 success)
- Complete backfill of all historical jobs
- Reconciliation check (ensure no data loss)
- 100% read traffic to new pattern

**Phase 4: Legacy Cleanup** (after 30 days of Phase 3)
- Remove legacy key writes
- Delete old Redis keys (after archive)

---

## Sonnet 4.5 Instructions

### 1. **Initialize Sprint 60 Phase 1**
```bash
# Confirm branch
git branch -v
# Should show: sprint-60/s60-dual-write-migration (current)

# Start Phase 1 implementation
# - Modify src/queue/simple_queue.py to support dual-write
# - Update tests with new key pattern
# - Deploy canary config (PHASE_1_CANARY_PCT=10)
```

### 2. **Use Agents at Sprint Gates**

| Gate | Agent | Task |
|------|-------|------|
| **After Phase 1 code** | Code-Reviewer | Review dual-write logic, atomicity checks |
| **After Phase 1 code** | Security-Reviewer | Verify workspace isolation during key overlap |
| **After Phase 1 tests pass** | Tech-Lead | Evaluate key pattern evolution, telemetry alignment |
| **Pre-merge** | Code-Reviewer + Security-Reviewer | Final checkpoint before deployment |

### 3. **Telemetry & Monitoring**
- Workspace labels are now present (from S59-05)
- New metric: `ai_jobs_dual_write_ratio` (track % of jobs on new schema)
- Canary dashboards: Filter by workspace_id to spot isolation issues

### 4. **Parallel Instance Option**
If Phase 1 implementation takes >1 hour and tests are running:
- Open **Haiku 4.5 instance** for:
  - Documentation updates
  - Agent review feedback processing
  - Hotfix patches (if needed)
- Keep Sonnet focused on Phase 1 implementation

---

## Pre-Merge Checklist (Phase 1 Completion)

- [ ] Dual-write logic implemented & tested
- [ ] Canary config added (PHASE_1_CANARY_PCT env var)
- [ ] Code-Reviewer PASS (atomicity, no regressions)
- [ ] Security-Reviewer PASS (workspace isolation verified)
- [ ] Tech-Lead PASS (architecture aligned)
- [ ] All tests green (100%)
- [ ] Commit message references S60-01

---

## Key Files for Phase 1

| File | Change |
|------|--------|
| `src/queue/simple_queue.py` | Add dual-write logic (enqueue, get methods) |
| `src/telemetry/prom.py` | Add `ai_jobs_dual_write_ratio` counter |
| `tests/test_jobs_endpoint.py` | Add tests for new key pattern |
| `.env.example` | Add `PHASE_1_CANARY_PCT=10` |

---

## Blockers or Concerns
- None identified. S59-05 hotfix provides clean foundation.
- Existing workspace labels in metrics are ready.
- Test suite is green.

---

## Handoff Complete ✅
Ready for **Sonnet 4.5** to start **Sprint 60 Phase 1 (Dual-Write)**.

🚀 Switch model and give green light.
