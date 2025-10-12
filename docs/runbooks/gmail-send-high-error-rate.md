# Runbook: Gmail Send High Error Rate

**Alert Name:** `GmailSendHighErrorRateWarning` / `GmailSendHighErrorRateCritical`
**Severity:** Warning (>1%) | Critical (>5%)
**Service:** relay
**Component:** gmail

---

## What It Means

Gmail send requests are failing at an elevated rate over a sustained period (10+ minutes with traffic >0.1 req/s). This indicates either:
- **API issues** with Google Gmail API (rate limits, quota, service degradation)
- **Auth failures** (expired/revoked OAuth tokens)
- **Invalid request payloads** (validation errors, malformed MIME)
- **Network/infrastructure issues** (timeouts, connection failures)

---

## Immediate Triage

### 1. Check Current Error Rate & Traffic
**Dashboard:** [Gmail Integration Overview](https://grafana/d/gmail-integration/overview)
**Panel:** "Gmail Send Error Rate (with Traffic Guard)"

```promql
# Error rate
job:gmail_send_errors_rate:5m

# Traffic context
job:gmail_send_exec_rate:5m
```

**Questions:**
- Is error rate >1% (warning) or >5% (critical)?
- What is current traffic? (If <1 req/s, may be transient)
- Is error rate spiking or sustained?

### 2. Identify Top Error Codes
**Dashboard:** [Structured Errors Analysis](https://grafana/d/errors/structured-errors)
**Panel:** "Top 5 Error Codes (Cardinality-Bounded)"

```promql
job:structured_error_rate_top5_codes:5m
```

**Common Error Codes:**
- `GOOGLE_API_QUOTA_EXCEEDED`: Rate limit hit, need to back off
- `GOOGLE_AUTH_INVALID`: OAuth token expired/revoked
- `GOOGLE_API_UNAVAILABLE`: Google service degradation
- `INVALID_RECIPIENT`: Client sending bad email addresses
- `MIME_BUILD_FAILED`: MIME construction errors

### 3. Check Result-Split Latency
**Dashboard:** [Gmail Integration Overview](https://grafana/d/gmail-integration/overview)
**Panel:** "Gmail Send Latency (P95) - Split by Result"

```promql
# Success path latency
job:gmail_send_latency_p95_by_result:5m{status="ok"}

# Error path latency
job:gmail_send_latency_p95_by_result:5m{status="error"}
```

**Question:** Are errors timing out (high latency) or failing fast (low latency)?

### 4. Review Recent Structured Errors
**Logs:** `logs/connectors.jsonl`

```bash
# Last 50 structured errors
tail -n 1000 logs/connectors.jsonl | grep '"event":"structured_error"' | tail -50
```

Look for patterns in `code`, `source`, `context` fields.

---

## Immediate Mitigations

### If GOOGLE_API_QUOTA_EXCEEDED
```bash
# Option 1: Pause Google provider temporarily
# Edit flags or environment variable
export PROVIDER_GOOGLE_ENABLED=false

# Option 2: Reduce rollout percentage
# Use rollout controller to dial back traffic
python scripts/rollout_controller.py --set-percent google 10
```

### If GOOGLE_AUTH_INVALID
```bash
# Check OAuth token health
python scripts/oauth/verify_tokens.py

# Refresh tokens if needed
python scripts/oauth/refresh_tokens.py

# Worst case: Re-authenticate
python scripts/oauth/oauth_flow.py
```

### If GOOGLE_API_UNAVAILABLE
- **Action:** Monitor Google Workspace Status Dashboard: https://www.google.com/appsstatus
- **Decision:** If Google outage confirmed, pause provider until resolved
- **Timeline:** Check status every 15 minutes

### If INVALID_RECIPIENT / Client Errors
- **Action:** High validation error rate suggests client-side issue
- **Check:** Dashboard "Validation Error Spike Detection" panel
- **Escalate:** Notify client integration team to review input validation
- **No immediate action needed** (client issue, not service issue)

---

## Rollout Controller Impact

The rollout controller monitors this error rate via:
```promql
sum(rate(action_error_total{provider="google",action="gmail.send"}[5m]))
/ clamp_min(sum(rate(action_exec_total{provider="google",action="gmail.send"}[5m])), 1)
```

**If error rate >1%:**
- Controller will **HOLD** current rollout percentage (no promotion)
- SLO violation logged in `logs/rollout.jsonl`

**If error rate >5% for 10+ minutes:**
- Controller may **ROLLBACK** if configured (check `ROLLOUT_ROLLBACK_ENABLED`)
- Manual intervention recommended: Set rollout to safe baseline

```bash
# Rollback to 10% (known stable)
python scripts/rollout_controller.py --set-percent google 10
```

---

## Escalation

### Warning Alert (1-5% error rate)
**Owner:** On-call SRE (Slack #ops-relay)
**Timeline:** Respond within 15 minutes
**Action:** Triage via dashboards, review logs, identify root cause

### Critical Alert (>5% error rate)
**Owner:** On-call SRE + Gmail Integration Lead
**Timeline:** Page immediately, respond within 5 minutes
**Action:** Immediate mitigation (pause provider or rollback), then root cause analysis

### If Unresolved After 30 Minutes
**Escalate to:** Platform Engineering Lead
**Consider:** Full provider disable, incident war room

---

## Post-Incident

### 1. Update Controller SLOs (if needed)
**File:** `config/rollout/slo_thresholds.yaml`

If 1% error rate is too strict for this integration:
```yaml
providers:
  google:
    error_rate_threshold: 0.02  # Raise to 2%
    latency_p95_threshold_ms: 500
```

### 2. Add Structured Error Code Handling
If new error code discovered:
**File:** `src/actions/adapters/google.py`

```python
# Add mapping for new error code
ERROR_CODE_MAP = {
    "insufficientPermissions": "GOOGLE_AUTH_INSUFFICIENT_PERMS",
    # ... add new code here
}
```

### 3. Update Alert Thresholds (if noisy)
**File:** `config/prometheus/prometheus-alerts-v2.yml`

If warning alert too sensitive:
```yaml
# Raise warning threshold from 1% to 2%
expr: (job:gmail_send_exec_rate:5m > 0.1) and (job:gmail_send_errors_rate:5m > 0.02)
```

### 4. Post-Mortem
**Template:** `docs/postmortems/YYYY-MM-DD-gmail-error-spike.md`

Include:
- Timeline of events (error rate spike start/end)
- Root cause (API quota, auth failure, etc.)
- Impact (requests failed, users affected)
- Mitigations applied (rollback, token refresh, etc.)
- Action items (code changes, config updates, monitoring improvements)

---

## Related Alerts

- **GmailSendErrorBudgetFastBurn**: Multi-window SLO burn alert (5m + 1h)
- **GmailSendErrorBudgetSlowBurn**: Long-term SLO burn alert (1h + 6h)
- **GmailValidationErrorSpike**: High structured error rate (may correlate)

---

## References

- **Dashboard:** https://grafana/d/gmail-integration/overview
- **Errors Dashboard:** https://grafana/d/errors/structured-errors
- **Rollout Controller:** `scripts/rollout_controller.py`
- **Logs:** `logs/connectors.jsonl`
- **Google Workspace Status:** https://www.google.com/appsstatus
