# Phase 4C Observation Window - START

**Date:** 2025-10-11
**Status:** READY TO BEGIN
**Duration:** 24-48 hours
**Mode:** Dry-run (`ROLLOUT_DRY_RUN=true`)

---

## Prerequisites Checklist

Before starting the observation window, ensure:

### Observability Stack
- [ ] Prometheus running (`http://localhost:9090`)
- [ ] Alertmanager running (`http://localhost:9093`)
- [ ] Grafana running (`http://localhost:3000`)
- [ ] Pushgateway running (`http://localhost:9091`)

### Environment Variables
```bash
# Required for controller
export PROMETHEUS_BASE_URL=http://localhost:9090
export ROLLOUT_DRY_RUN=true

# Required for application (if generating traffic)
export ACTIONS_ENABLED=true
export TELEMETRY_ENABLED=true
export PROVIDER_GOOGLE_ENABLED=true
export GOOGLE_CLIENT_ID=[your-client-id]
export GOOGLE_CLIENT_SECRET=[your-client-secret]
export DATABASE_URL=[your-db-url]
export REDIS_URL=[your-redis-url]
export OAUTH_ENCRYPTION_KEY=[your-key]
```

### Configuration Files
- [ ] Recording rules loaded: `config/prometheus/prometheus-recording.yml`
- [ ] Alert rules loaded: `config/prometheus/prometheus-alerts-v2.yml`
- [ ] Alertmanager config: `config/alertmanager/alertmanager.yml`
- [ ] Grafana dashboards imported (3 dashboards)

---

## Start Command

```bash
# Set environment
export PROMETHEUS_BASE_URL=http://localhost:9090
export ROLLOUT_DRY_RUN=true

# Start controller (runs continuously)
python scripts/rollout_controller.py
```

**Alternative: Use GitHub Actions (if configured)**
```bash
gh workflow run rollout-controller.yml \
  --field mode=dry-run \
  --field duration=48h
```

---

## Monitoring During Window

### Every 4-6 Hours
1. **Check controller health**:
   - Dashboard: http://localhost:3000/d/rollout-controller/monitoring
   - Query: `rollout_controller_runs_total{status="ok"}`
   - Expected: Successful runs every 5-15 minutes

2. **Check Gmail SLOs**:
   - Dashboard: http://localhost:3000/d/gmail-integration/overview
   - Error rate: Should be <1%
   - Latency P95: Should be <500ms

3. **Check for alerts**:
   - Prometheus: http://localhost:9090/alerts
   - Alertmanager: http://localhost:9093/#/alerts
   - Expected: No sustained alerts (transient spikes OK)

4. **Screenshot key panels** (for observation report):
   - Gmail Send Error Rate (with traffic guard)
   - Gmail Send Latency (P95 split by result)
   - Rollout Percentage History
   - Controller Run Status
   - Top 5 Error Codes

---

## Observation Window Log

**Start Time:** [YYYY-MM-DD HH:MM UTC]

### Hour 0-6
- Controller started: [TIME]
- Dashboards checked: [TIME]
- Alerts observed: [NONE / list]
- Notes: [Any observations]

### Hour 6-12
- Dashboards checked: [TIME]
- Alerts observed: [NONE / list]
- Notes: [Any observations]

### Hour 12-18
- Dashboards checked: [TIME]
- Alerts observed: [NONE / list]
- Notes: [Any observations]

### Hour 18-24
- Dashboards checked: [TIME]
- Alerts observed: [NONE / list]
- Notes: [Any observations]

### Hour 24-36 (if extending)
- Dashboards checked: [TIME]
- Alerts observed: [NONE / list]
- Notes: [Any observations]

### Hour 36-48 (if extending)
- Dashboards checked: [TIME]
- Alerts observed: [NONE / list]
- Notes: [Any observations]

**End Time:** [YYYY-MM-DD HH:MM UTC]

---

## Tabletop Drill Schedule

**Plan to execute during observation window:**
- [ ] Drill 01: Error Rate Warning (Hour 12-18)
- [ ] Drill 02: Latency Critical (Hour 24-30, if extending)

---

## Data Collection Checklist

At end of window, collect for observation report:

- [ ] Controller run status (ok/error/timeout counts)
- [ ] Controller decision history (promote/hold/rollback counts)
- [ ] Error rate P50/P95/P99/Max
- [ ] Latency P50/P95/P99/Max
- [ ] Top 10 structured error codes
- [ ] Validation error rate
- [ ] MIME build time P50/P95/P99
- [ ] Alerts fired (timeline + resolution)
- [ ] Dashboard screenshots (8-10 panels)

---

## Quick Stop Command

If issues detected:
```bash
# Stop controller
pkill -f rollout_controller.py

# Or kill specific background process
# (Check task manager or use Ctrl+C in terminal)
```

---

## Next Steps After Window

1. Fill observation report: `docs/evidence/sprint-54/PHASE-4C-OBSERVATION-REPORT.md`
2. Calculate readiness score (target: 7/10)
3. Make go/no-go decision
4. If GO: Proceed to Phase 5 (disable dry-run, set rollout 10%)
5. If NO-GO: Address blockers, extend window, re-assess

---

**Started By:** [Name]
**Notes:** [Any special conditions, expected load patterns, etc.]
