# Automated Rollout Controller - Usage Guide

**Sprint 54**: SLO-based automated rollout for Gmail features.

---

## Overview

The automated rollout controller runs on a schedule (every 10 minutes via GitHub Actions) and makes rollout decisions based on Prometheus SLO metrics.

**What it does:**
1. Queries Prometheus for Gmail SLO metrics (error rate, latency, OAuth failures)
2. Gets current rollout percentage from Redis
3. Calls `gmail_policy()` to get recommendation
4. Updates Redis if recommendation differs (with safety guards)
5. Logs decision to audit trail

**User Experience:**
- Uses **consistent hashing** (SHA-256) for stable user bucketing
- Same `actor_id` → same rollout decision across requests
- Users don't flip between enabled/disabled states during rollout

**Safety guards:**
- **Min dwell time**: 15 minutes between any change
- **Cooldown after rollback**: 1 hour hold before next promotion
- **Manual pause**: Set `flags:google:paused=true` to stop controller
- **Dry-run mode**: Test without making changes
- **Prometheus unreachable**: Hold at current level, exit non-zero (no blind changes)
- **Redis write failure**: Exit non-zero, fail-fast (surfaces in GitHub Actions)

---

## Setup

### 1. Configure GitHub Actions Secrets

Add these secrets in your GitHub repo settings:

**Settings → Secrets and variables → Actions → New repository secret**

| Secret Name | Value | Description |
|------------|-------|-------------|
| `REDIS_URL` | `redis://...` | Redis connection URL |

### 2. Configure GitHub Actions Variables

**Settings → Secrets and variables → Actions → Variables tab**

| Variable Name | Value | Description |
|--------------|-------|-------------|
| `PROMETHEUS_BASE_URL` | `http://prometheus:9090` | Prometheus server URL |
| `ROLLOUT_DRY_RUN` | `false` | Set to `true` for testing |
| `PUSHGATEWAY_URL` | `http://pushgateway:9091` | (Optional) Pushgateway URL for controller telemetry |

### 3. Initialize Redis Flags

Set these keys in Redis before enabling the controller:

```bash
# Via Redis CLI
redis-cli SET flags:google:enabled "true"
redis-cli SET flags:google:internal_only "true"
redis-cli SET flags:google:rollout_percent "0"
redis-cli SET flags:google:paused "false"
```

Or via Python:

```python
import redis, os
r = redis.from_url(os.getenv("REDIS_URL"))
r.set("flags:google:enabled", "true")
r.set("flags:google:internal_only", "true")
r.set("flags:google:rollout_percent", "0")
r.set("flags:google:paused", "false")
```

### 4. Enable Workflow

The workflow is enabled automatically when you merge the PR. It will run every 10 minutes.

---

## How It Works

### Decision Flow

```
Every 10 minutes:
├─ Check if paused (flags:google:paused=true) → Exit if paused
├─ Query Prometheus for metrics
│  ├─ Error rate (last 5m)
│  ├─ P95 latency (last 5m)
│  └─ OAuth refresh failures (last 15m)
├─ Get current rollout % from Redis
├─ Call gmail_policy(metrics, current_%) → Get recommendation
├─ Check if change needed
│  ├─ If target == current → Exit (no change)
│  └─ If target != current → Continue
├─ Safety guards
│  ├─ Min dwell time: 15 min since last change?
│  └─ Cooldown: 1 hour after rollback?
├─ Update Redis (flags:google:rollout_percent)
└─ Log to docs/evidence/sprint-54/rollout_log.md
```

### Promotion Path

**Automatic progression when SLOs are healthy:**

```
0% → (Initial canary) → 10%
10% → (Healthy → ramp) → 50%
50% → (Healthy → full) → 100%
100% → (Hold) → 100%
```

**Automatic rollback when SLO violated:**

```
Any % → (SLO violated) → 10% (or 0%)
```

### Safety Guards

**1. Min Dwell Time (15 minutes)**
- Prevents rapid changes
- Controller waits 15 min after any change before making another

**2. Cooldown After Rollback (1 hour)**
- After a rollback (decrease), wait 1 hour before promoting again
- Prevents oscillation (up → down → up → down)

**3. Manual Pause**
- Set `flags:google:paused=true` to stop controller
- Controller checks this flag on every run

**4. Dry-Run Mode**
- Set `ROLLOUT_DRY_RUN=true` to log decisions without updating Redis
- Useful for testing policy changes

---

## Monitoring

### Check Controller Status

**GitHub Actions:**
- Go to: **Actions** tab → **Rollout Controller** workflow
- See recent runs (every 10 minutes)
- Click on a run to see logs

**Audit Log:**
```bash
cat docs/evidence/sprint-54/rollout_log.md
```

**Example output:**
```
2025-10-08T15:00:00Z  google  0% -> 10%  reason=Initial canary  by=controller
2025-10-08T15:45:00Z  google  10% -> 50%  reason=Healthy → ramp to 50%  by=controller
2025-10-08T16:30:00Z  google  50% -> 10%  reason=SLO violated: error_rate=2.5% > 1%  by=controller
```

### Prometheus Queries

**Current rollout percentage:**
```promql
# Not directly available in Prometheus
# Check Redis: redis-cli GET flags:google:rollout_percent
```

**Gmail error rate (5m):**
```promql
(
  increase(action_error_total{provider="google",action="gmail.send"}[5m])
    /
  increase(action_exec_total{provider="google",action="gmail.send"}[5m])
)
```

**Gmail P95 latency (5m):**
```promql
histogram_quantile(
  0.95,
  sum(rate(action_latency_seconds_bucket{provider="google",action="gmail.send"}[5m])) by (le)
)
```

**OAuth refresh failures (15m):**
```promql
increase(oauth_events_total{provider="google",event="refresh_failed"}[15m])
```

### Controller Health Telemetry

**Setup:** Set `PUSHGATEWAY_URL` environment variable to enable controller telemetry.

**Metrics emitted by controller:**

```promql
# Controller decisions (counter)
rollout_controller_changes_total{feature="google",result="promote|rollback|hold"}

# Current rollout percentage (gauge)
rollout_controller_percent{feature="google"}

# Controller health (counter)
rollout_controller_runs_total{status="ok|prom_unreachable|redis_error"}
```

**Recommended alerts:**

```yaml
# Alert if controller hasn't run successfully in 30 minutes
- alert: RolloutControllerStalled
  expr: |
    absent(rollout_controller_runs_total{status="ok"}[30m])
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Rollout controller has not run successfully in 30+ minutes"

# Alert on controller failures
- alert: RolloutControllerFailing
  expr: |
    increase(rollout_controller_runs_total{status!="ok"}[15m]) > 0
  for: 0m
  labels:
    severity: critical
  annotations:
    summary: "Rollout controller failing (Prometheus or Redis unreachable)"
```

---

## Manual Operations

### Pause Controller

```bash
redis-cli SET flags:google:paused "true"
```

Controller will exit on next run without making changes.

### Resume Controller

```bash
redis-cli SET flags:google:paused "false"
```

Controller will resume on next run.

### Manual Override (Force Percentage)

```bash
# Set rollout to specific percentage
redis-cli SET flags:google:rollout_percent "25"

# Log the manual change
python3 << EOF
from src.rollout.audit import append_rollout_log
append_rollout_log("google", 10, 25, "Manual override for testing", by="manual")
EOF
```

Controller will respect this on next run (won't change unless policy recommends different value).

### Trigger Controller Manually

Instead of waiting for cron:

**GitHub Actions:**
- Go to: **Actions** tab → **Rollout Controller**
- Click: **Run workflow** → **Run workflow**

**Locally (for testing):**
```bash
export PROMETHEUS_BASE_URL="http://localhost:9090"
export REDIS_URL="redis://localhost:6379"
export ROLLOUT_DRY_RUN="true"  # Optional: test without changes

python scripts/rollout_controller.py
```

---

## Tuning SLO Thresholds

During initial rollout, you may need to adjust policy thresholds.

**Edit:** `src/rollout/policy.py`

**Example: Error rate threshold too sensitive**

If 1.5% error rate is normal (e.g., user typos):

```python
# Before
if error_rate > 0.01:  # 1%
    return Recommendation(...)

# After
if error_rate > 0.03:  # 3% (more tolerant)
    return Recommendation(...)
```

**After changing thresholds:**
1. Commit and push changes
2. Controller will use new thresholds on next run
3. Document change in `rollout_log.md`

---

## Troubleshooting

### Controller Not Running

**Check GitHub Actions:**
- Go to: **Actions** tab → **Rollout Controller**
- Look for workflow runs (should be every 10 minutes)

**Possible issues:**
- `PROMETHEUS_BASE_URL` not set (workflow skips)
- `REDIS_URL` secret missing (controller fails)
- Controller paused (`flags:google:paused=true`)

### Controller Exiting with Error

**Symptom:** GitHub Actions workflow shows red (failed status)

**Check logs for error messages:**

**`PROMETHEUS_UNREACHABLE`:**
- Controller cannot query Prometheus
- **Fix**: Verify `PROMETHEUS_BASE_URL` is correct and Prometheus is running
- **Safety**: Controller holds at current percentage (no changes)

**`REDIS_WRITE_FAILED`:**
- Controller cannot write to Redis
- **Fix**: Verify `REDIS_URL` is correct and Redis is accessible
- **Safety**: No rollout changes applied (fail-fast)

**Expected behavior:** Controller exits with code 1 (loud failure) to surface issues immediately

### Controller Making Wrong Decisions

**Check metrics:**
```bash
# Run controller locally with debug output
python scripts/rollout_controller.py
```

Look for:
- `[INFO] Metrics: {...}` - Are metrics correct?
- `[INFO] Policy recommendation: X% (reason: ...)` - Does recommendation make sense?

**Check policy thresholds:**
- Open `src/rollout/policy.py`
- Verify thresholds match your expectations

### False Positives (Unnecessary Rollbacks)

**Symptom:** Controller rolls back when SLOs seem fine

**Diagnosis:**
1. Check Prometheus for metric spikes
2. Review audit log for pattern
3. Check if threshold is too sensitive

**Fix:** Adjust threshold in `src/rollout/policy.py`

### Controller Stuck (Not Promoting)

**Check safety guards:**

**Dwell time:**
```bash
# Check last change time
redis-cli GET flags:google:last_change_time
```

If < 15 minutes ago, controller is waiting.

**Cooldown after rollback:**
```bash
# Check if last change was a rollback
redis-cli GET flags:google:last_percent  # e.g., "50"
redis-cli GET flags:google:rollout_percent  # e.g., "10"
```

If last_percent > rollout_percent, controller waits 1 hour before promoting.

---

## Testing

### Dry-Run Mode

Test controller without making changes:

```bash
export ROLLOUT_DRY_RUN="true"
python scripts/rollout_controller.py
```

Output:
```
[DRY RUN] Would update rollout: 10% -> 50%
```

### Unit Tests

Run controller unit tests:

```bash
pytest tests/rollout/test_controller_unit.py -v
```

**Tests cover:**
- Prometheus query handling
- Metrics fetching
- Safety guards (dwell time, cooldown)
- Pause functionality
- Policy integration

---

## Maintenance

### Regular Reviews

**Weekly:**
- Check audit log for unexpected rollbacks
- Review Prometheus metrics trends
- Verify controller is running (GitHub Actions)

**Monthly:**
- Review SLO threshold tuning needs
- Check for false positives
- Document lessons learned

### Disable Controller

If you want to disable automated rollout entirely:

**Option 1: Pause (temporary)**
```bash
redis-cli SET flags:google:paused "true"
```

**Option 2: Disable workflow (permanent)**
- Edit `.github/workflows/rollout-controller.yml`
- Add to top of file:
  ```yaml
  on:
    workflow_dispatch:  # Manual only, no cron
  ```

---

## References

- **Controller Script**: `scripts/rollout_controller.py`
- **Policy Logic**: `src/rollout/policy.py`
- **GitHub Actions Workflow**: `.github/workflows/rollout-controller.yml`
- **Unit Tests**: `tests/rollout/test_controller_unit.py`
- **Audit Log**: `docs/evidence/sprint-54/rollout_log.md`
- **Observability Plan**: `docs/observability/PHASE-C-OBSERVABILITY.md`

---

**Document Version**: 1.0
**Last Updated**: 2025-10-08
**Author**: Claude (AI Assistant)
