# Runbook: Rollout Controller Stalled

**Alert Name:** `RolloutControllerStalled`
**Severity:** Warning
**Service:** relay
**Component:** rollout

---

## What It Means

The rollout controller hasn't completed a successful run in 60+ minutes. This means:
- No automatic rollout percentage adjustments
- SLO monitoring frozen (no promotion/hold/rollback decisions)
- May indicate controller process crashed or workflow disabled

---

## Immediate Triage

### 1. Check Controller Health
**Dashboard:** [Rollout Controller Monitoring](https://grafana/d/rollout-controller/monitoring)
**Panel:** "Controller Health - Stalled Detection"

```promql
# Seconds since last successful run
time() - (rollout_controller_runs_total{status="ok"} > 0)
```

### 2. Check Recent Runs
```promql
job:rollout_controller_run_rate:5m
```

**Questions:**
- Are ANY runs completing (ok/error)?
- Or is controller completely stopped?

### 3. Check Controller Logs
```bash
# If running via GitHub Actions
gh run list --workflow=rollout-controller.yml --limit 5

# If running locally
tail -f logs/rollout.jsonl
```

---

## Immediate Mitigations

### If Controller Process Crashed
```bash
# Restart controller (local)
set ROLLOUT_DRY_RUN=true
python scripts/rollout_controller.py

# Or trigger GitHub Actions workflow manually
gh workflow run rollout-controller.yml
```

### If Workflow Disabled
Check `.github/workflows/rollout-controller.yml`:
- Schedule may be commented out
- Workflow may be disabled in GitHub Actions UI

---

## Escalation

**Owner:** Platform Engineering
**Timeline:** Respond within 30 minutes
**Action:** Restart controller, verify automation resumes

---

## Related Alerts

- **RolloutControllerFailing**: Controller running but erroring

---

## References

- **Dashboard:** https://grafana/d/rollout-controller/monitoring
- **Controller:** `scripts/rollout_controller.py:1`
- **Workflow:** `.github/workflows/rollout-controller.yml:1`
