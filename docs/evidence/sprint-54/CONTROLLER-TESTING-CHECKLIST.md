# Rollout Controller Testing Checklist

**Sprint 54**: Pre-production validation for automated rollout controller.

---

## Preconditions

Before starting testing, verify these are complete:

- [ ] All code from Sprint 54 merged to `main`
- [ ] GitHub Actions secrets configured (`REDIS_URL`)
- [ ] GitHub Actions variables configured (`PROMETHEUS_BASE_URL`, `ROLLOUT_DRY_RUN`)
- [ ] Redis flags initialized (`flags:google:enabled`, `flags:google:internal_only`, `flags:google:rollout_percent`, `flags:google:paused`)
- [ ] Prometheus alerts deployed (`observability/templates/prometheus-alerts.yml`)
- [ ] Unit tests passing (`pytest tests/rollout/`)

---

## Phase 1: Dry-Run Validation (24-48h)

**Goal:** Validate controller logic without affecting production rollout.

**Setup:**
```bash
# Set dry-run mode in GitHub Actions variables
ROLLOUT_DRY_RUN=true
```

**Tasks:**
- [ ] Enable dry-run mode in GitHub Actions
- [ ] Trigger workflow manually (Actions → Rollout Controller → Run workflow)
- [ ] Check workflow logs for recommendations
- [ ] Verify no Redis updates occur (check `flags:google:rollout_percent` remains unchanged)
- [ ] Run for 24-48 hours, checking logs every 6-8 hours
- [ ] Confirm policy recommendations make sense given metrics

**Success Criteria:**
- Controller runs without errors
- Recommendations appear reasonable
- No unexpected Redis updates
- Prometheus queries succeed

**Rollback Plan:**
- N/A (dry-run has no production impact)

---

## Phase 2: Live Controller + Forced Scenarios (2-4h)

**Goal:** Test controller with live Redis updates using forced metric scenarios.

**Setup:**
```bash
# Disable dry-run mode
ROLLOUT_DRY_RUN=false

# Reset rollout to 0%
redis-cli SET flags:google:rollout_percent "0"
redis-cli SET flags:google:paused "false"
redis-cli DEL flags:google:last_change_time
redis-cli DEL flags:google:last_percent
```

**Tasks:**

### Scenario A: Happy Path Promotion
- [ ] Start at 0%, metrics healthy
- [ ] Wait 10 minutes (next controller run)
- [ ] Verify promotion to 10% (check Redis + audit log)
- [ ] Wait 15 minutes (min dwell time)
- [ ] Verify promotion to 50%
- [ ] Wait 15 minutes
- [ ] Verify promotion to 100%

### Scenario B: SLO Violation Rollback
- [ ] Set rollout to 50% manually
- [ ] Inject high error rate (simulate bad deploy or use test traffic)
- [ ] Wait 10 minutes
- [ ] Verify rollback to 10% (check audit log for "SLO violated" reason)

### Scenario C: Cooldown After Rollback
- [ ] After Scenario B rollback, ensure metrics are healthy
- [ ] Wait 15 minutes (min dwell time passes)
- [ ] Verify controller holds at 10% (cooldown active)
- [ ] Wait 1 hour (cooldown expires)
- [ ] Verify promotion resumes to 50%

### Scenario D: Manual Pause
- [ ] Set `flags:google:paused=true`
- [ ] Wait 10 minutes
- [ ] Check workflow logs show "Controller is paused"
- [ ] Verify no Redis updates
- [ ] Set `flags:google:paused=false`
- [ ] Verify controller resumes

**Success Criteria:**
- All scenarios execute as expected
- Audit log captures all changes correctly
- Safety guards (dwell time, cooldown) work
- Manual pause functions properly

**Rollback Plan:**
```bash
# Pause controller immediately
redis-cli SET flags:google:paused "true"

# Force rollout to safe percentage
redis-cli SET flags:google:rollout_percent "0"
```

---

## Phase 3: SLO Alert Validation (1-2h)

**Goal:** Verify Prometheus alerts fire when SLOs are violated.

**Setup:**
- Ensure Prometheus alerts are deployed (`observability/templates/prometheus-alerts.yml`)
- Confirm alerting destination configured (Slack, PagerDuty, etc.)

**Tasks:**

### Alert: GmailErrorRateHigh
- [ ] Generate Gmail traffic with >1% error rate
- [ ] Verify alert fires within 10 minutes
- [ ] Check alert message clarity
- [ ] Verify controller rolls back based on metrics

### Alert: GmailLatencySlow
- [ ] Generate Gmail traffic with P95 latency >500ms
- [ ] Verify alert fires within 10 minutes
- [ ] Check alert message clarity

### Alert: OAuthRefreshFailures
- [ ] Simulate OAuth refresh failures (revoke tokens, etc.)
- [ ] Verify alert fires immediately (for=0m)
- [ ] Check alert message clarity

**Success Criteria:**
- All alerts fire correctly
- Alert messages are actionable
- Controller responds to metric violations

**Rollback Plan:**
- N/A (alerts are read-only)

---

## Phase 4: Audit Trail Review (30m)

**Goal:** Verify audit log is complete and useful for debugging.

**Setup:**
```bash
# Review audit log after Phase 2 scenarios
cat docs/evidence/sprint-54/rollout_log.md
```

**Tasks:**
- [ ] Verify all rollout changes are logged
- [ ] Check timestamps are correct (UTC)
- [ ] Verify reasons are descriptive
- [ ] Confirm `by=controller` or `by=manual` is accurate
- [ ] Test manual override logging:
  ```bash
  redis-cli SET flags:google:rollout_percent "25"
  python3 << EOF
  from src.rollout.audit import append_rollout_log
  append_rollout_log("google", 10, 25, "Manual override for testing", by="manual")
  EOF
  ```

**Success Criteria:**
- Audit log contains all changes
- Log format is clear and parseable
- Manual changes can be logged

**Rollback Plan:**
- N/A (audit log is append-only)

---

## Phase 5: Internal Traffic Test (1-2 days)

**Goal:** Validate controller with real internal user traffic before public rollout.

**Setup:**
```bash
# Reset rollout to 0%
redis-cli SET flags:google:rollout_percent "0"
redis-cli DEL flags:google:last_change_time
redis-cli DEL flags:google:last_percent

# Ensure paused=false
redis-cli SET flags:google:paused "false"
```

**Tasks:**
- [ ] Start at 0% with internal-only traffic
- [ ] Let controller promote automatically (0% → 10% → 50% → 100%)
- [ ] Monitor Prometheus dashboards daily
- [ ] Review audit log for unexpected rollbacks
- [ ] Check GitHub Actions workflow runs (should be every 10 minutes)
- [ ] Verify no false positives (unnecessary rollbacks)

**Success Criteria:**
- Controller promotes to 100% without manual intervention
- No unexpected rollbacks
- SLO alerts do not fire (unless real issues)
- Internal users report no issues

**Rollback Plan:**
```bash
# Pause controller
redis-cli SET flags:google:paused "true"

# Force rollout to 0%
redis-cli SET flags:google:rollout_percent "0"

# Log manual rollback
python3 << EOF
from src.rollout.audit import append_rollout_log
append_rollout_log("google", 100, 0, "Manual rollback during testing", by="manual")
EOF
```

---

## Phase 6: Public Rollout

**Goal:** Enable Gmail for public users with automated rollout.

**Setup:**
```bash
# Disable internal-only flag
redis-cli SET flags:google:internal_only "false"

# Reset rollout to 0%
redis-cli SET flags:google:rollout_percent "0"
redis-cli DEL flags:google:last_change_time
redis-cli DEL flags:google:last_percent
```

**Tasks:**
- [ ] Announce rollout start to team
- [ ] Monitor dashboard continuously for first 24 hours
- [ ] Review audit log every 4 hours
- [ ] Check SLO alerts (expect none)
- [ ] Let controller promote automatically (0% → 10% → 50% → 100%)
- [ ] Monitor user feedback channels (support, Slack, etc.)

**Success Criteria:**
- Controller reaches 100% within 1-2 days
- No SLO violations
- No user-reported issues
- Audit log shows smooth progression

**Rollback Plan:**
```bash
# Immediate pause
redis-cli SET flags:google:paused "true"

# Force rollback to safe percentage (10% or 0%)
redis-cli SET flags:google:rollout_percent "10"

# Log incident
python3 << EOF
from src.rollout.audit import append_rollout_log
append_rollout_log("google", 100, 10, "Incident: [describe issue]", by="manual")
EOF

# Investigate metrics
# Visit Prometheus: http://localhost:9090/graph
# Run queries from CONTROLLER-USAGE.md
```

---

## Sign-Offs

### Phase 1: Dry-Run Validation
- **Tester:** ____________________
- **Date:** ____________________
- **Result:** ☐ Pass ☐ Fail
- **Notes:** ____________________

### Phase 2: Live Controller + Forced Scenarios
- **Tester:** ____________________
- **Date:** ____________________
- **Result:** ☐ Pass ☐ Fail
- **Notes:** ____________________

### Phase 3: SLO Alert Validation
- **Tester:** ____________________
- **Date:** ____________________
- **Result:** ☐ Pass ☐ Fail
- **Notes:** ____________________

### Phase 4: Audit Trail Review
- **Tester:** ____________________
- **Date:** ____________________
- **Result:** ☐ Pass ☐ Fail
- **Notes:** ____________________

### Phase 5: Internal Traffic Test
- **Tester:** ____________________
- **Date:** ____________________
- **Result:** ☐ Pass ☐ Fail
- **Notes:** ____________________

### Phase 6: Public Rollout
- **Approver:** ____________________
- **Date:** ____________________
- **Result:** ☐ Complete
- **Notes:** ____________________

---

## Appendix: Quick Commands

### Check Current Rollout Status
```bash
redis-cli GET flags:google:rollout_percent
redis-cli GET flags:google:paused
redis-cli GET flags:google:last_change_time
```

### Force Specific Percentage
```bash
redis-cli SET flags:google:rollout_percent "50"
python3 << EOF
from src.rollout.audit import append_rollout_log
append_rollout_log("google", 10, 50, "Manual adjustment for [reason]", by="manual")
EOF
```

### Pause/Resume Controller
```bash
# Pause
redis-cli SET flags:google:paused "true"

# Resume
redis-cli SET flags:google:paused "false"
```

### Check GitHub Actions Logs
```bash
# Via web: https://github.com/<org>/<repo>/actions/workflows/rollout-controller.yml
# Or via CLI:
gh run list --workflow=rollout-controller.yml --limit 5
gh run view <run-id> --log
```

### Query Prometheus Metrics
```bash
# Error rate (5m)
curl -s "http://localhost:9090/api/v1/query" --data-urlencode 'query=(increase(action_error_total{provider="google",action="gmail.send"}[5m])/increase(action_exec_total{provider="google",action="gmail.send"}[5m]))'

# P95 latency (5m)
curl -s "http://localhost:9090/api/v1/query" --data-urlencode 'query=histogram_quantile(0.95,sum(rate(action_latency_seconds_bucket{provider="google",action="gmail.send"}[5m])) by (le))'

# OAuth refresh failures (15m)
curl -s "http://localhost:9090/api/v1/query" --data-urlencode 'query=increase(oauth_events_total{provider="google",event="refresh_failed"}[15m])'
```

### Run Controller Locally
```bash
export PROMETHEUS_BASE_URL="http://localhost:9090"
export REDIS_URL="redis://localhost:6379"
export ROLLOUT_DRY_RUN="true"  # Optional: test without changes

python scripts/rollout_controller.py
```

### Reset Everything
```bash
redis-cli SET flags:google:rollout_percent "0"
redis-cli SET flags:google:paused "false"
redis-cli DEL flags:google:last_change_time
redis-cli DEL flags:google:last_percent
echo "Reset complete. Controller will start fresh on next run."
```

---

## References

- **Controller Script**: `scripts/rollout_controller.py`
- **Policy Logic**: `src/rollout/policy.py`
- **Usage Guide**: `docs/evidence/sprint-54/CONTROLLER-USAGE.md`
- **GitHub Workflow**: `.github/workflows/rollout-controller.yml`
- **Unit Tests**: `tests/rollout/test_controller_unit.py`, `tests/rollout/test_rollout_gate_unit.py`

---

**Document Version**: 1.0
**Last Updated**: 2025-10-08
**Author**: Claude (AI Assistant)
