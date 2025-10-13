# Runbook: Gmail Send High Latency

**Alert Name:** `GmailSendHighLatencyWarning` / `GmailSendHighLatencyCritical`
**Severity:** Warning (P95 >500ms) | Critical (P95 >2s)
**Service:** relay
**Component:** gmail

---

## What It Means

P95 latency for Gmail send operations has exceeded acceptable thresholds. This impacts user experience and may indicate:
- **Google API slowness** (upstream service degradation)
- **Network issues** (increased RTT, packet loss)
- **Large attachment processing** (MIME build taking too long)
- **Auth token refresh delays** (OAuth token validation slow)

---

## Immediate Triage

### 1. Check Latency Distribution
**Dashboard:** [Gmail Integration Overview](https://grafana/d/gmail-integration/overview)
**Panel:** "Gmail Send Latency (P95) - Split by Result"

```promql
# Success path latency
job:gmail_send_latency_p95_by_result:5m{status="ok"}

# Error path latency
job:gmail_send_latency_p95_by_result:5m{status="error"}

# Combined P95
job:gmail_send_latency_p95:5m
```

**Questions:**
- Is latency spike on **success path** or **error path**?
- Are P50 and P99 also elevated? (Check recording rules)

### 2. Check MIME Builder Performance
**Dashboard:** [Gmail Integration Overview](https://grafana/d/gmail-integration/overview)
**Panel:** "MIME Builder P95 Build Time"

```promql
job:gmail_mime_build_p95:5m
```

**If MIME P95 >500ms:**
- Large attachments likely culprit
- Check attachment sizes: `job:gmail_attachment_bytes_rate:1m`

### 3. Review Attachment Patterns
```promql
# Attachment processing rate by result
job:gmail_attachment_bytes_rate:1m

# Inline image references
job:gmail_inline_refs_rate:1m
```

**Question:** Recent spike in attachment count or size?

### 4. Check Error Rate Correlation
**Panel:** "Gmail Send Error Rate (with Traffic Guard)"

```promql
job:gmail_send_errors_rate:5m
```

**If error rate also elevated:**
- Timeouts may be causing both high latency AND errors
- Check for `GOOGLE_API_TIMEOUT` in structured errors

---

## Immediate Mitigations

### If MIME Builder Slow (P95 >500ms)
```bash
# Option 1: Add attachment size limits (code change required)
# File: src/actions/adapters/google_mime.py
MAX_ATTACHMENT_SIZE_MB = 10  # Lower from 25MB

# Option 2: Reduce rollout to lower load
python scripts/rollout_controller.py --set-percent google 25
```

### If Google API Slow (upstream)
```bash
# Check Google Workspace Status
curl -s https://www.google.com/appsstatus | grep Gmail

# If confirmed outage: Reduce load or pause
export PROVIDER_GOOGLE_ENABLED=false
```

### If Timeout-Related (high error + latency)
```bash
# Increase timeout temporarily
# File: src/actions/adapters/google.py
GMAIL_API_TIMEOUT_SECONDS = 15  # Raise from 10

# Or reduce concurrent requests (if connection pooling issue)
GMAIL_API_MAX_CONNECTIONS = 5  # Lower from 10
```

---

## Rollout Controller Impact

Controller monitors latency via:
```promql
job:gmail_send_latency_p95:5m
```

**If P95 >500ms for 10+ minutes:**
- Controller will **HOLD** current rollout (no promotion)
- SLO violation logged

**If P95 >2s (critical):**
- Manual rollback recommended
```bash
python scripts/rollout_controller.py --set-percent google 10
```

---

## Escalation

### Warning (P95 500ms-2s)
**Owner:** On-call SRE (Slack #ops-relay)
**Timeline:** Respond within 15 minutes
**Action:** Triage dashboards, check MIME/attachment patterns

### Critical (P95 >2s)
**Owner:** On-call SRE + Gmail Integration Lead
**Timeline:** Page immediately, respond within 5 minutes
**Action:** Immediate rollback or provider pause

---

## Post-Incident

### Optimize MIME Builder
**File:** `src/actions/adapters/google_mime.py`

Consider:
- Stream large attachments (avoid loading into memory)
- Cache inline image encoding
- Pre-validate attachment sizes before MIME build

### Adjust Latency SLO
**File:** `config/rollout/slo_thresholds.yaml`

If 500ms too strict:
```yaml
providers:
  google:
    latency_p95_threshold_ms: 1000  # Raise to 1s
```

---

## Related Alerts

- **MimeBuilderSlowPerformance**: MIME-specific latency alert
- **GmailSendHighErrorRate**: May correlate with timeouts

---

## References

- **Dashboard:** https://grafana/d/gmail-integration/overview
- **MIME Code:** `src/actions/adapters/google_mime.py:1`
- **Adapter Code:** `src/actions/adapters/google.py:1`
