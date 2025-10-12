# Rollout Controller Activation Checklist

**Purpose:** Enable the Rollout Controller workflow for Gmail observation window and production rollout.

**Status:** ⏸️ Currently disabled (`ROLLOUT_CONTROLLER_ENABLED=false`)

---

## Phase 4C: Observation Window (24-48h)

**Objective:** Validate observability stack under real conditions before internal rollout.

### Prerequisites

- [ ] **Prometheus stack running** (Prometheus, Alertmanager, Grafana, Pushgateway)
  - Prometheus: http://localhost:9090 (or Railway URL)
  - Alertmanager: http://localhost:9093
  - Grafana: http://localhost:3000
  - Pushgateway: http://localhost:9091

- [ ] **Recording rules loaded** (`config/prometheus/prometheus-recording.yml`)
- [ ] **Alert rules loaded** (`config/prometheus/prometheus-alerts-v2.yml`)
- [ ] **Alertmanager routing configured** (`config/alertmanager/alertmanager.yml`)
- [ ] **Grafana dashboards imported** (3 dashboards)

### Step 1: Enable Controller (Dry-Run Mode)

Set GitHub repository variables:

1. Go to: https://github.com/kmabbott81/djp-workflow/settings/variables/actions
2. Set/update variables:
   - `ROLLOUT_CONTROLLER_ENABLED=true` ✅
   - `ROLLOUT_DRY_RUN=true` (keeps controller in observation mode)
   - `ROLLOUT_ENV=dev`
   - `PROMETHEUS_BASE_URL=http://your-prometheus:9090` (or Railway internal URL)

3. Add secrets:
   - `REDIS_URL=redis://...` (if not already set)

### Step 2: Verify Controller Starts

- [ ] Wait for next cron run (every 10 minutes) or trigger manually:
  - Go to: https://github.com/kmabbott81/djp-workflow/actions/workflows/rollout-controller.yml
  - Click "Run workflow" → "Run workflow"

- [ ] Check run logs for success:
  ```
  ✅ All required secrets/vars configured
  [INFO] Rollout controller starting (dry-run mode)
  ```

- [ ] Verify no failure emails

### Step 3: Monitor Metrics (First 60 Minutes)

Check Prometheus for controller metrics:

```promql
# Controller run status
rollout_controller_runs_total{status="ok"}

# Controller decisions
rollout_controller_changes_total{result=~"promote|hold|rollback"}

# Current rollout percentage
rollout_controller_percent{provider="google"}
```

Expected:
- Controller runs every 5-15 minutes
- `status="ok"` increments each run
- Rollout percentage decisions logged

### Step 4: Monitor Dashboards (Throughout Window)

**Every 4-6 hours:**
- Gmail Integration Overview dashboard
- Rollout Controller Monitoring dashboard
- Structured Errors Analysis dashboard

**Screenshot key panels:**
- Gmail Send Error Rate (with traffic guard)
- Gmail Send Latency P95 (split by result)
- Rollout Percentage History
- Controller Run Status
- Top 5 Error Codes

### Step 5: Execute Tabletop Drill (Hour 12)

Run synthetic alert test:

```bash
python scripts/observability/pushgateway_synth.py --scenario error-rate-warn --duration 15m
```

- [ ] Verify alert fires in Prometheus `/alerts`
- [ ] Verify notification in Slack #ops-relay (if configured)
- [ ] Follow runbook: `docs/runbooks/gmail-send-high-error-rate.md`
- [ ] Document score in tabletop drill template

### Step 6: Complete Observation Report (After 24-48h)

Fill template: `docs/evidence/sprint-54/PHASE-4C-OBSERVATION-REPORT.md`

**Sections to complete:**
1. Executive Summary (Go/No-Go decision)
2. Controller Behavior (run status, decisions)
3. Gmail Send SLOs (error rate, latency)
4. Structured Errors (top codes)
5. MIME Builder Performance
6. Alerts Fired (timeline, false positives)
7. Metrics Collection Health
8. Tabletop Drill Results
9. Readiness Assessment (10-point scale)
10. Recommendations
11. Go/No-Go Decision

**Readiness Score Target:** ≥7/10

---

## Phase 5: Internal Rollout (After GO Decision)

**Prerequisites:**
- [ ] Observation report complete with **GO decision**
- [ ] Readiness score ≥7/10
- [ ] No sustained SLO violations during observation
- [ ] Tabletop drill passed (≥5/6 score)
- [ ] Internal-only recipients configured

### Step 1: Configure Internal-Only Mode

Update environment variables in Railway/deployment:

```bash
export GOOGLE_INTERNAL_ONLY=true
export GOOGLE_INTERNAL_ALLOWED_DOMAINS=yourcompany.com,example.com
export GOOGLE_INTERNAL_TEST_RECIPIENTS=test@yourcompany.com
```

Verify:
```bash
python -c "from src.actions.adapters.google import GoogleAdapter; print(GoogleAdapter().internal_only)"
# Should print: True
```

### Step 2: Disable Dry-Run Mode

Update GitHub repository variables:

- `ROLLOUT_CONTROLLER_ENABLED=true` (keep)
- `ROLLOUT_DRY_RUN=false` ✅ **Remove dry-run mode**
- `ROLLOUT_ENV=prod` ✅ **Switch to production**

**Effect:** Controller will now make real rollout decisions based on SLOs

### Step 3: Set Initial Rollout (0%)

Controller will start at 0% by default. Verify:

```bash
# Check rollout gate logs
tail -n 50 logs/rollout.jsonl | grep provider=google

# Expected:
# {"provider":"google","percent":0,"decision":"hold","reason":"initial_rollout"}
```

### Step 4: Promote to 10% (First Internal Users)

**Manual promotion** (controller will hold at 0% initially):

```bash
python scripts/rollout_controller.py --set-percent google 10
```

**Or wait for controller to promote** based on SLOs:
- Error rate <1% for 1 hour
- Latency P95 <500ms
- No sustained alerts

### Step 5: Monitor Progression (0% → 10% → 50% → 100%)

Controller will automatically promote based on SLO health:

| Rollout % | Target Users | Promotion Criteria | Hold Time |
|-----------|--------------|-------------------|-----------|
| 0% | None (disabled) | Initial state | Manual start |
| 10% | ~10 internal users | SLOs green for 1h | 4-8 hours |
| 25% | ~25 internal users | SLOs green for 2h | 8-12 hours |
| 50% | ~50 internal users | SLOs green for 4h | 12-24 hours |
| 75% | ~75 internal users | SLOs green for 6h | 24-48 hours |
| 100% | All internal users | SLOs green for 12h | Final state |

**Monitor dashboards continuously:**
- Check every 2-4 hours
- Watch for error rate spikes
- Watch for latency degradation
- Respond to alerts per runbooks

### Step 6: Rollback Procedure (If Issues)

**Automatic rollback** (controller will rollback on SLO violations):
- Error rate >5% for 10 minutes → rollback 50%
- Error rate >10% for 5 minutes → rollback to 0%
- Critical alerts firing → rollback 50%

**Manual rollback:**

```bash
# Rollback to previous percentage
python scripts/rollout_controller.py --rollback google

# Rollback to specific percentage
python scripts/rollout_controller.py --set-percent google 10

# Disable completely
python scripts/rollout_controller.py --set-percent google 0
```

---

## Safety Checks

Before enabling controller in production:

- [ ] **Prometheus reachable** from controller (if on Railway, use internal URL)
- [ ] **Redis reachable** from controller
- [ ] **Recording rules evaluating** (check Prometheus `/rules`)
- [ ] **Alert rules evaluating** (check Prometheus `/alerts`)
- [ ] **Runbooks accessible** (linked in alert annotations)
- [ ] **On-call rotation configured** (PagerDuty/Slack routing)
- [ ] **Tabletop drill passed** (≥5/6 score)
- [ ] **Internal-only mode active** (external domains blocked)

---

## Troubleshooting

**Controller not running:**
- Check `ROLLOUT_CONTROLLER_ENABLED=true`
- Check GitHub Actions runs (should show "Success" or "Skipped", not "Failed")
- Check logs in workflow runs for error messages

**Controller running but no metrics:**
- Check `PROMETHEUS_BASE_URL` is correct
- Check Prometheus is reachable from GitHub runner (may need Railway worker or self-hosted runner)
- Check `REDIS_URL` is configured

**Controller making wrong decisions:**
- Check Prometheus queries in controller code match recording rules
- Check SLO thresholds are appropriate for your traffic
- Check traffic guards are preventing false positives

**Alerts firing unexpectedly:**
- Check traffic guard thresholds (exec_rate > 0.1 req/s)
- Check alert thresholds match SLO targets
- Check for false positives during low traffic periods
- Follow runbook for alert (docs/runbooks/)

---

## Rollback to Disabled State

To disable controller after enabling:

1. Set `ROLLOUT_CONTROLLER_ENABLED=false` in GitHub variables
2. Result: Workflow skips, no runs, no metrics
3. Manual rollout percentage persists in Redis (safe to re-enable later)

---

**References:**
- Observation Window Checklist: `docs/evidence/sprint-54/OBSERVATION-WINDOW-START.md`
- Observation Report Template: `docs/evidence/sprint-54/PHASE-4C-OBSERVATION-REPORT.md`
- Runbook Index: `docs/runbooks/README.md`
- Controller Preflight Checks: `.github/workflows/rollout-controller.yml`
- Controller Script: `scripts/rollout_controller.py`

**Created:** 2025-10-11
**Owner:** Platform Engineering
**Status:** Ready for observation window activation
