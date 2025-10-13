# Tabletop Drill 01: Gmail Error Rate Warning

**Date:** 2025-10-11
**Duration:** 20 minutes
**Participants:** On-call SRE, Gmail Integration Lead
**Scenario:** Simulated 2% error rate spike via synthetic alert driver

---

## Objectives

1. **Validate alert routing**: Warning alert goes to Slack #ops-relay, not PagerDuty
2. **Test dashboard triage**: On-call can identify root cause via Grafana panels
3. **Verify inhibition**: Critical alerts suppress warning alerts
4. **Practice runbook**: Follow [gmail-send-high-error-rate.md](../runbooks/gmail-send-high-error-rate.md) steps
5. **Confirm resolution**: Alert resolves when synthetic signal stops

---

## Prerequisites

- Prometheus + Alertmanager + Grafana stack running
- Pushgateway available at `http://localhost:9091`
- Slack #ops-relay channel configured
- Runbook accessible: `docs/runbooks/gmail-send-high-error-rate.md`

---

## Drill Script

### Phase 1: Inject Synthetic Error Rate (5 minutes)

**Facilitator Action:**
```bash
# Start synthetic error rate (2% for 15 minutes)
python scripts/observability/pushgateway_synth.py \
  --scenario error-rate-warn \
  --duration 15m
```

**Expected Output:**
```
[error-rate-warn] Injecting 2% error rate for 900s...
  [60s] Pushed exec=50, error=1 (2% rate)
  [120s] Pushed exec=50, error=1 (2% rate)
  ...
```

**Wait:** 10-12 minutes for alert to fire (`for: 10m` in alert rule)

---

### Phase 2: Alert Fires (2 minutes)

**Facilitator:** Monitor Prometheus /alerts page

**Expected State:**
- `GmailSendHighErrorRateWarning` transitions to **FIRING** state
- Alert shows labels: `severity=warning, service=relay, component=gmail`

**On-Call SRE:** Check Slack #ops-relay for notification

**Expected Slack Message:**
```
⚠️ relay/gmail: GmailSendHighErrorRateWarning
Alert: Gmail send error rate >1% (warn)
Details: Error rate is 2.0% over the last 5 minutes (threshold: 1%, traffic: 0.5req/s)
Runbook: docs/runbooks/gmail-send-high-error-rate.md
Dashboard: https://grafana/d/gmail-integration/overview
```

**Verification Questions:**
- ✅ Did alert route to Slack #ops-relay (not PagerDuty)?
- ✅ Does Slack message include error rate + traffic context?
- ✅ Is runbook link accessible?

---

### Phase 3: Triage via Dashboard (5 minutes)

**On-Call SRE:** Open runbook and follow triage steps

#### Step 1: Check Current Error Rate & Traffic
**Dashboard:** [Gmail Integration Overview](https://grafana/d/gmail-integration/overview)
**Panel:** "Gmail Send Error Rate (with Traffic Guard)"

**Expected:**
- Error rate line at ~2%
- Traffic line at ~0.5 req/s (50 exec every 10s / 10s = 5 req/s, but rate over 5m averages lower)

**Question:** Is this a real incident or synthetic?
**Answer:** Check for `job=relay_synth` label in Prometheus (synthetic)

#### Step 2: Identify Top Error Codes
**Dashboard:** [Structured Errors Analysis](https://grafana/d/errors/structured-errors)
**Panel:** "Top 5 Error Codes (Cardinality-Bounded)"

**Expected:**
- No error codes visible (synthetic driver only pushes counters, not structured errors)
- In real incident: Would see `GOOGLE_API_QUOTA_EXCEEDED`, `GOOGLE_AUTH_INVALID`, etc.

#### Step 3: Check Result-Split Latency
**Dashboard:** [Gmail Integration Overview](https://grafana/d/gmail-integration/overview)
**Panel:** "Gmail Send Latency (P95) - Split by Result"

**Expected:**
- No latency data from synthetic signal (only counters, not histograms)
- In real incident: Would see elevated error path latency if timeouts

---

### Phase 4: Apply Mitigation (3 minutes)

**On-Call SRE:** Since this is a drill, **do not** apply actual mitigations

**In Real Incident:**
```bash
# Option 1: Pause provider
export PROVIDER_GOOGLE_ENABLED=false

# Option 2: Rollback rollout
python scripts/rollout_controller.py --set-percent google 10
```

**For Drill:** Document mitigation decision in incident log:
```
Decision: Synthetic signal confirmed (job=relay_synth)
Action: Monitor for resolution, no mitigation needed
```

---

### Phase 5: Test Alert Inhibition (5 minutes)

**Facilitator Action:**
```bash
# Inject critical error rate (6%) while warning is firing
python scripts/observability/pushgateway_synth.py \
  --scenario error-rate-crit \
  --duration 15m
```

**Wait:** 10-12 minutes for critical alert to fire

**Expected State:**
- `GmailSendHighErrorRateCritical` transitions to **FIRING**
- `GmailSendHighErrorRateWarning` transitions to **INHIBITED** in Alertmanager
- Only critical alert sends notification to PagerDuty

**On-Call SRE:** Verify Alertmanager /alerts page shows:
```
GmailSendHighErrorRateCritical: FIRING
GmailSendHighErrorRateWarning: INHIBITED (suppressed by critical)
```

**Verification Questions:**
- ✅ Did critical alert route to PagerDuty (not Slack)?
- ✅ Was warning alert inhibited (no duplicate Slack message)?
- ✅ Does Alertmanager UI show inhibition rule matched?

---

### Phase 6: Resolution (3 minutes)

**Facilitator Action:**
```bash
# Stop synthetic signal (Ctrl+C or wait for duration to complete)
```

**Wait:** 5 minutes for alerts to resolve (`for: 10m` + grace period)

**Expected State:**
- Both alerts transition to **RESOLVED**
- Slack receives "Resolved" notification

**Expected Slack Message:**
```
✅ relay/gmail: GmailSendHighErrorRateWarning RESOLVED
Error rate returned to normal
```

**Verification Questions:**
- ✅ Did alerts resolve within expected timeframe?
- ✅ Did Slack receive resolved notification?
- ✅ Are Grafana panels showing normal state?

---

## Drill Debrief

### What Went Well
- [ ] Alert fired within expected timeframe (10-12 minutes)
- [ ] Routing to Slack #ops-relay worked correctly
- [ ] Dashboard panels provided actionable context
- [ ] Runbook was accessible and easy to follow
- [ ] Inhibition prevented double-paging
- [ ] Alert resolved cleanly after signal stopped

### Issues Encountered
- [ ] List any issues (alert didn't fire, dashboard panel broken, runbook unclear, etc.)

### Action Items
- [ ] Update runbook if any steps were unclear
- [ ] Fix dashboard panel if queries failed
- [ ] Adjust alert threshold if too sensitive/noisy
- [ ] Update Alertmanager config if routing incorrect

---

## Drill Scoring

| Criteria | Target | Actual | Pass/Fail |
|----------|--------|--------|-----------|
| Alert fires within 15m | ✅ | ___ | ___ |
| Routes to Slack (not PagerDuty) | ✅ | ___ | ___ |
| Dashboard shows error rate + traffic | ✅ | ___ | ___ |
| Runbook accessible | ✅ | ___ | ___ |
| Critical inhibits warning | ✅ | ___ | ___ |
| Alert resolves within 10m | ✅ | ___ | ___ |

**Overall Score:** ___/6

**Grade:**
- 6/6: A+ (Production-ready)
- 5/6: A (Minor tuning needed)
- 4/6: B (Significant issues, re-drill after fixes)
- <4/6: F (Major issues, redesign alert/runbook)

---

## Next Drills

### Drill 02: Latency Critical (with rollback)
**Scenario:** P95 latency >2s, follow runbook to rollback rollout percentage

### Drill 03: Controller Stalled (automation failure)
**Scenario:** Controller stops running, detect via dashboard, restart manually

### Drill 04: Metrics Missing (scrape failure)
**Scenario:** Stop Prometheus scrape, verify sentinel alert fires and inhibits all component alerts

---

## References

- **Runbook:** `docs/runbooks/gmail-send-high-error-rate.md`
- **Synthetic Driver:** `scripts/observability/pushgateway_synth.py`
- **Alertmanager Config:** `config/alertmanager/alertmanager.yml`
- **Alert Rules:** `config/prometheus/prometheus-alerts-v2.yml`
