# Sprint 60 Phase 1 - Canary Deployment Checklist

**Release**: v0.1.5-phase1
**Branch**: main (PR #44 merged)
**Date**: 2025-10-17
**Feature Flag**: `AI_JOBS_NEW_SCHEMA=on`

---

## Pre-Deployment Verification

- [x] PR #44 merged to main (squashed)
- [x] Tag v0.1.5-phase1 created and pushed
- [x] All 36 tests passing (11 dual-write + 25 existing)
- [x] All gate reviews approved (Code-Reviewer, Security-Reviewer, Tech-Lead)
- [ ] Staging environment ready
- [ ] Telemetry dashboard created (see Prometheus queries below)
- [ ] Rollback procedure documented

---

## Staging Deployment (Day 1)

### 1. Deploy to Staging

```bash
# Set environment variable
export AI_JOBS_NEW_SCHEMA=on

# Deploy v0.1.5-phase1
# (Railway, Docker, or your deployment method)
railway up --service djp-workflow --environment staging
```

### 2. Smoke Tests

**Manual Test 1**: Verify dual-write creates both keys
```bash
# Create test job via API
curl -X POST https://staging.yourapp.com/ai/execute \
  -H "Authorization: Bearer $STAGING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "test-workspace",
    "action_provider": "google",
    "action_name": "gmail.send",
    "params": {"to": "test@example.com", "subject": "Test", "body": "Test"}
  }'

# Verify both Redis keys exist
redis-cli -h staging-redis -p 6379
> KEYS ai:jobs:*       # Should find old key
> KEYS ai:job:test-workspace:*   # Should find new key
> HGETALL ai:jobs:{job_id}
> HGETALL ai:job:test-workspace:{job_id}
# Both should have identical data
```

**Manual Test 2**: Verify telemetry recording
```bash
# Check Prometheus metrics endpoint
curl https://staging.yourapp.com/metrics | grep ai_jobs_dual_write_total
# Should see: ai_jobs_dual_write_total{workspace_id="test-workspace",result="succeeded"} 1
```

**Manual Test 3**: Verify workspace_id validation
```bash
# Attempt invalid workspace_id (should fail)
curl -X POST https://staging.yourapp.com/ai/execute \
  -H "Authorization: Bearer $STAGING_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "workspace_id": "INVALID:WORKSPACE",
    "action_provider": "google",
    "action_name": "gmail.send",
    "params": {"to": "test@example.com"}
  }'
# Should return 400 or 500 with generic error message
```

### 3. Run Full Test Suite in Staging

```bash
# SSH to staging or run via CI
pytest tests/test_dual_write.py tests/test_jobs_endpoint.py -v

# Expected: 36/36 passing
```

### 4. Check Logs

```bash
# No errors containing "Failed to enqueue job"
# No stack traces in ERROR logs
# DEBUG logs should have details (job_id, workspace_id)
```

---

## Canary Deployment (Days 2-4)

### Phase 1: 10% Rollout (Day 2, 00:00 UTC)

```bash
# Deploy to 10% of production workers
# Set AI_JOBS_NEW_SCHEMA=on for canary workers only
railway scale --service djp-workflow --replicas 10 --environment production-canary
```

**Monitor for 24 hours**:
- [ ] `ai_jobs_dual_write_total{result="succeeded"}` increasing linearly
- [ ] `ai_jobs_dual_write_total{result="failed"}` == 0
- [ ] `ai_job_latency_seconds` p99 < 110% of baseline
- [ ] No ERROR logs with "Failed to enqueue job"
- [ ] Spot-check 10 random jobs: verify old/new keys identical

**Success Criteria**:
- Zero dual-write failures
- Latency increase < 10%
- No unhandled exceptions

### Phase 2: 50% Rollout (Day 3, 00:00 UTC)

```bash
# Deploy to 50% of production workers
railway scale --service djp-workflow --replicas 50 --environment production
```

**Monitor for 24 hours**:
- [ ] All Phase 1 metrics still healthy
- [ ] `ai_jobs_dual_write_total{result="succeeded"}` 5x higher (50% of traffic)
- [ ] Compare old/new key data: validate consistency across workspaces

### Phase 3: 100% Rollout (Day 4, 00:00 UTC)

```bash
# Deploy to all production workers
railway scale --service djp-workflow --replicas 100 --environment production
```

**Monitor for 48 hours**:
- [ ] All metrics healthy
- [ ] 100% of new jobs have dual-write telemetry
- [ ] Prepare for Phase 2 (read-routing + backfill)

---

## Prometheus Queries (Add to Telemetry Dashboard)

### 1. Dual-Write Success Rate

```promql
# Should be 100% (no failures)
rate(ai_jobs_dual_write_total{result="succeeded"}[5m])
/
(rate(ai_jobs_dual_write_total{result="succeeded"}[5m]) + rate(ai_jobs_dual_write_total{result="failed"}[5m]))
```

### 2. Dual-Write Coverage

```promql
# Percentage of jobs using new schema
rate(ai_jobs_dual_write_total{result="succeeded"}[5m])
/
rate(ai_jobs_total[5m])
```

### 3. Job Latency p99

```promql
# Should stay < 110% of baseline
histogram_quantile(0.99, rate(ai_job_latency_seconds_bucket[5m]))
```

### 4. Dual-Write Failures (Alert)

```promql
# Alert if any failures detected
rate(ai_jobs_dual_write_total{result="failed"}[5m]) > 0
```

### 5. Workspace-Scoped Metrics

```promql
# Per-workspace dual-write success
sum by (workspace_id) (rate(ai_jobs_dual_write_total{result="succeeded"}[5m]))
```

---

## Rollback Procedure

**Trigger Rollback If**:
- `ai_jobs_dual_write_total{result="failed"}` > 0
- `ai_job_latency_seconds` p99 > 120% of baseline
- ERROR logs contain unhandled exceptions
- Data inconsistency detected (old/new keys differ)

**Rollback Steps**:
1. Set `AI_JOBS_NEW_SCHEMA=off` in production config
2. Restart all workers (module-level flag requires restart)
3. Verify old schema writes resume normally
4. Investigate failure logs, fix issue
5. Retry Phase 1 deployment after fix

**Data Safety**: Old schema always written to, so no data loss on rollback.

---

## Post-Canary Actions

**After 48 hours stability at 100%**:
- [ ] Export telemetry dashboard for Phase 2 reference
- [ ] Document baseline latency for Phase 3 comparison
- [ ] Create Phase 2 epic: Read-routing + async backfill
- [ ] Create webapi security fix PR (SECURITY_TICKET_S60_WEBAPI.md)

---

## Key Contacts

- **Oncall Engineer**: [Your oncall rotation]
- **Deployment Runbook**: [Link to runbook]
- **Prometheus Dashboard**: [Link to dashboard]
- **Incident Response**: [Link to incident response doc]

---

## Success Metrics (After 48 Hours at 100%)

- [x] Zero dual-write failures (`ai_jobs_dual_write_total{result="failed"}` == 0)
- [x] Latency impact < 10% (`ai_job_latency_seconds` p99 < 110% baseline)
- [x] 1000+ jobs with dual-write telemetry
- [x] Data consistency validated (old/new keys identical)
- [x] No ERROR logs with stack traces

**When all metrics pass**: Sprint 60 Phase 1 complete. Proceed to Phase 2.
