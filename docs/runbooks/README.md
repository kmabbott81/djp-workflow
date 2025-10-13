# Gmail Integration Runbooks

**Sprint 54 - Phase 4D: Production Readiness**

This directory contains operational runbooks for all Gmail integration alerts. Each runbook follows a standard format:
- **What It Means**: Alert condition explanation
- **Immediate Triage**: Dashboard panels + PromQL queries for diagnosis
- **Immediate Mitigations**: Commands to stabilize the system
- **Escalation**: Owner, timeline, and escalation path
- **Post-Incident**: Configuration updates and lessons learned

---

## Runbook Index

### Critical Alerts (Page)

| Alert | Threshold | Runbook | Impact |
|-------|-----------|---------|--------|
| GmailSendHighErrorRateCritical | >5% error rate | [gmail-send-high-error-rate.md](gmail-send-high-error-rate.md) | Service degradation, user impact |
| GmailSendHighLatencyCritical | P95 >2s | [gmail-send-high-latency.md](gmail-send-high-latency.md) | Poor UX, timeouts |
| GmailSendErrorBudgetFastBurn | 5m+1h >1% | [slo-burn-fast.md](slo-burn-fast.md) | SLO violation, auto-hold |
| GmailMetricsMissing | No metrics 15m | [metrics-missing.md](metrics-missing.md) | Blind spot, scrape failure |

### Warning Alerts (Slack Ops)

| Alert | Threshold | Runbook | Impact |
|-------|-----------|---------|--------|
| GmailSendHighErrorRateWarning | 1-5% error rate | [gmail-send-high-error-rate.md](gmail-send-high-error-rate.md) | Elevated errors, investigate |
| GmailSendHighLatencyWarning | P95 500ms-2s | [gmail-send-high-latency.md](gmail-send-high-latency.md) | Degraded performance |
| GmailSendErrorBudgetSlowBurn | 1h+6h >1% | [slo-burn-slow.md](slo-burn-slow.md) | Long-term SLO erosion |
| RolloutControllerStalled | No runs 60m | [rollout-controller-stalled.md](rollout-controller-stalled.md) | Automation stopped |
| RolloutControllerFailing | Errors in 15m | [rollout-controller-failing.md](rollout-controller-failing.md) | Controller errors |
| MimeBuilderSlowPerformance | P95 >500ms | [mime-builder-slow.md](mime-builder-slow.md) | MIME construction slow |

### Info Alerts (Slack Low-Noise)

| Alert | Threshold | Runbook | Impact |
|-------|-----------|---------|--------|
| GmailValidationErrorSpike | >10% validation errors | [validation-error-spike.md](validation-error-spike.md) | Client-side issue |
| HighSanitizationActivity | >50 changes/sec | [sanitization-spike.md](sanitization-spike.md) | Possible hostile input |

---

## Quick Reference

### Common Mitigations

```bash
# Pause Google provider
export PROVIDER_GOOGLE_ENABLED=false

# Rollback rollout percentage
python scripts/rollout_controller.py --set-percent google 10

# Refresh OAuth tokens
python scripts/oauth/refresh_tokens.py

# View recent errors
tail -n 100 logs/connectors.jsonl | grep structured_error
```

### Common Dashboards

- **Gmail Integration Overview**: https://grafana/d/gmail-integration/overview
- **Rollout Controller**: https://grafana/d/rollout-controller/monitoring
- **Structured Errors**: https://grafana/d/errors/structured-errors

### Common Queries

```promql
# Current error rate
job:gmail_send_errors_rate:5m

# Current P95 latency
job:gmail_send_latency_p95:5m

# Traffic rate
job:gmail_send_exec_rate:5m

# Top error codes
job:structured_error_rate_top5_codes:5m

# Rollout percentage
rollout_controller_percent{feature="google"}
```

---

## Escalation Paths

### Level 1: On-Call SRE (Slack #ops-relay)
- **Alerts**: Warning severity
- **Timeline**: Respond within 15 minutes
- **Action**: Triage via dashboards, apply standard mitigations

### Level 2: On-Call SRE + Integration Lead (PagerDuty)
- **Alerts**: Critical severity
- **Timeline**: Page immediately, respond within 5 minutes
- **Action**: Immediate mitigation (rollback/pause), root cause analysis

### Level 3: Platform Engineering Lead
- **Escalate after**: 30 minutes unresolved
- **Action**: Incident war room, consider full provider disable

---

## Testing Runbooks

Use the synthetic alert driver to validate runbooks:

```bash
# Trigger warning error rate alert
python scripts/observability/pushgateway_synth.py --scenario error-rate-warn --duration 15m

# Follow runbook steps
# 1. Check dashboard panels
# 2. Review structured errors
# 3. Apply mitigation (if real incident)
# 4. Verify alert resolves
```

See [TABLETOP-DRILL-01.md](../observability/TABLETOP-DRILL-01.md) for full tabletop exercise.

---

## Contributing

When adding new alerts:
1. Create runbook file (copy template)
2. Add entry to this README
3. Update alert annotation `runbook_url` in `config/prometheus/prometheus-alerts-v2.yml`
4. Test runbook with synthetic alert driver
5. Conduct tabletop drill with on-call rotation

---

**Last Updated:** 2025-10-11
**Owner:** Platform Engineering / Gmail Integration Team
