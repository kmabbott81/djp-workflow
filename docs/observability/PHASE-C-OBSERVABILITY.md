# Sprint 54 Phase C: Observability Plan
**Date**: 2025-10-08
**Status**: Planning
**Scope**: Metrics, alerts, and dashboards for Gmail rich email features

---

## 1. Overview

This document defines the observability strategy for Sprint 54 Phase C (HTML email, attachments, and Studio Google UX). It extends the existing telemetry framework from Sprint 48/53 with new metrics specific to rich email features.

**Goals**:
- Detect MIME building errors and performance regressions
- Monitor attachment/inline CID usage and payload sizes
- Track HTML sanitization outcomes
- Alert on SLO violations (latency, error rate, quota exhaustion)
- Enable deep-dive debugging with structured logs

---

## 2. New Metrics

### 2.1 MIME Builder Metrics

#### `gmail_mime_build_seconds` (Histogram)
**Description**: Time spent building multipart MIME messages
**Type**: Histogram (seconds)
**Labels**:
- `mime_structure` - Values: `text`, `html`, `mixed`, `alternative`, `related`
- `attachment_count` - Buckets: `0`, `1-3`, `4-6`, `7-10`, `>10`
- `inline_count` - Buckets: `0`, `1-5`, `6-10`, `11-20`, `>20`

**Buckets**: `[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5]`

**PromQL Queries**:
```promql
# P95 MIME build latency by structure
histogram_quantile(0.95, sum by (le, mime_structure) (
  rate(gmail_mime_build_seconds_bucket[5m])
))

# Slow MIME builds (>500ms)
sum(rate(gmail_mime_build_seconds_bucket{le="0.5"}[5m]))
  /
sum(rate(gmail_mime_build_seconds_count[5m]))
```

---

#### `gmail_attachment_bytes_total` (Counter)
**Description**: Total bytes processed across all attachments
**Type**: Counter (bytes)
**Labels**:
- `content_type` - MIME type (e.g., `application/pdf`, `image/png`)
- `disposition` - Values: `attachment`, `inline`
- `result` - Values: `accepted`, `rejected_type`, `rejected_size`

**PromQL Queries**:
```promql
# Attachment bytes per minute by type
sum by (content_type) (
  rate(gmail_attachment_bytes_total{result="accepted"}[1m])
) * 60

# Rejection rate by reason
sum by (result) (
  rate(gmail_attachment_bytes_total{result=~"rejected_.*"}[5m])
)
```

---

#### `gmail_inline_refs_total` (Counter)
**Description**: Count of inline CID references processed
**Type**: Counter
**Labels**:
- `result` - Values: `matched`, `orphan_cid`, `missing_content_id`

**PromQL Queries**:
```promql
# Inline CID match rate (should be ~100%)
sum(rate(gmail_inline_refs_total{result="matched"}[5m]))
  /
sum(rate(gmail_inline_refs_total[5m]))

# Orphan CID references (HTML references missing inline attachment)
rate(gmail_inline_refs_total{result="orphan_cid"}[5m])
```

---

### 2.2 HTML Sanitization Metrics

#### `gmail_html_sanitization_seconds` (Histogram)
**Description**: Time spent sanitizing HTML content
**Type**: Histogram (seconds)
**Labels**:
- `html_size_kb` - Buckets: `<10`, `10-100`, `100-500`, `500-1000`, `>1000`

**Buckets**: `[0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5]`

---

#### `gmail_html_sanitization_changes_total` (Counter)
**Description**: Count of tags/attributes removed during sanitization
**Type**: Counter
**Labels**:
- `change_type` - Values: `tag_removed`, `attribute_removed`, `css_blocked`

**PromQL Queries**:
```promql
# Sanitization change rate (high values = aggressive filtering)
sum by (change_type) (
  rate(gmail_html_sanitization_changes_total[5m])
)
```

---

### 2.3 Validation Metrics

#### `gmail_validation_errors_total` (Counter)
**Description**: Count of validation errors for rich email features
**Type**: Counter
**Labels**:
- `error_reason` - Values from bounded error taxonomy:
  - `html_too_large`
  - `html_invalid_encoding`
  - `attachment_too_large`
  - `attachment_count_exceeded`
  - `attachment_type_blocked`
  - `inline_too_large`
  - `inline_count_exceeded`
  - `total_payload_too_large`

**PromQL Queries**:
```promql
# Top validation errors
topk(5, sum by (error_reason) (
  rate(gmail_validation_errors_total[5m])
))
```

---

### 2.4 Studio UX Metrics

#### `studio_google_oauth_flow_total` (Counter)
**Description**: Count of OAuth flows initiated from Studio
**Type**: Counter
**Labels**:
- `flow_type` - Values: `connect`, `reconnect`, `disconnect`
- `result` - Values: `success`, `user_cancelled`, `error`

**PromQL Queries**:
```promql
# OAuth success rate from Studio
sum(rate(studio_google_oauth_flow_total{result="success"}[5m]))
  /
sum(rate(studio_google_oauth_flow_total[5m]))
```

---

#### `studio_gmail_send_attempts_total` (Counter)
**Description**: Count of Gmail send attempts from Studio
**Type**: Counter
**Labels**:
- `has_html` - Values: `true`, `false`
- `has_attachments` - Values: `true`, `false`
- `result` - Values: `success`, `validation_error`, `quota_error`, `network_error`

**PromQL Queries**:
```promql
# Studio Gmail send success rate
sum(rate(studio_gmail_send_attempts_total{result="success"}[5m]))
  /
sum(rate(studio_gmail_send_attempts_total[5m]))

# Rich email feature adoption (HTML usage)
sum(rate(studio_gmail_send_attempts_total{has_html="true"}[1h]))
  /
sum(rate(studio_gmail_send_attempts_total[1h]))
```

---

## 3. Alert Rules

### 3.1 Latency Alerts

#### **Alert: GmailMIMEBuildSlow**
**Description**: P95 MIME build latency exceeds 500ms
**Severity**: Warning
**SLO Mapping**: Latency SLO (P95 < 500ms for actions)

```yaml
alert: GmailMIMEBuildSlow
expr: |
  histogram_quantile(0.95, sum by (le) (
    rate(gmail_mime_build_seconds_bucket[5m])
  )) > 0.5
for: 5m
labels:
  severity: warning
  team: backend
annotations:
  summary: "Gmail MIME build latency is high (P95 > 500ms)"
  description: "P95 MIME build time: {{ $value }}s. Check for large attachments or slow Base64 encoding."
  runbook_url: "https://docs.relay.dev/runbooks/gmail-mime-slow"
```

---

#### **Alert: GmailHTMLSanitizationSlow**
**Description**: P95 HTML sanitization latency exceeds 100ms
**Severity**: Warning

```yaml
alert: GmailHTMLSanitizationSlow
expr: |
  histogram_quantile(0.95, sum by (le) (
    rate(gmail_html_sanitization_seconds_bucket[5m])
  )) > 0.1
for: 5m
labels:
  severity: warning
  team: backend
annotations:
  summary: "HTML sanitization is slow (P95 > 100ms)"
  description: "P95 sanitization time: {{ $value }}s. Check HTML payload sizes or bleach library performance."
```

---

### 3.2 Error Rate Alerts

#### **Alert: GmailValidationErrorsHigh**
**Description**: Validation error rate exceeds 5% of total Gmail actions
**Severity**: Warning
**SLO Mapping**: Error rate SLO (success rate > 99%)

```yaml
alert: GmailValidationErrorsHigh
expr: |
  sum(rate(gmail_validation_errors_total[5m]))
    /
  sum(rate(relay_actions_executed_total{action_id="gmail.send"}[5m]))
  > 0.05
for: 10m
labels:
  severity: warning
  team: backend
annotations:
  summary: "Gmail validation error rate is high (>5%)"
  description: "Error rate: {{ $value | humanizePercentage }}. Check top error reasons."
  dashboard_url: "https://grafana.relay.dev/d/gmail-errors"
```

---

#### **Alert: GmailInlineCIDOrphansHigh**
**Description**: >10% of inline CID references are orphans (HTML refs missing attachment)
**Severity**: Warning

```yaml
alert: GmailInlineCIDOrphansHigh
expr: |
  sum(rate(gmail_inline_refs_total{result="orphan_cid"}[5m]))
    /
  sum(rate(gmail_inline_refs_total[5m]))
  > 0.1
for: 5m
labels:
  severity: warning
  team: backend
annotations:
  summary: "High rate of orphan inline CID references (>10%)"
  description: "Orphan rate: {{ $value | humanizePercentage }}. HTML may reference CIDs not present in inline attachments."
```

---

### 3.3 Quota Alerts

#### **Alert: GmailQuotaNearExhaustion**
**Description**: Gmail API quota usage exceeds 80% of daily limit
**Severity**: Critical
**SLO Mapping**: Availability SLO (99.5% uptime)

```yaml
alert: GmailQuotaNearExhaustion
expr: |
  (
    sum(increase(relay_actions_executed_total{action_id="gmail.send"}[1d]))
      /
    100000  # Daily quota from Gmail API (adjust based on actual quota)
  ) > 0.8
labels:
  severity: critical
  team: backend
annotations:
  summary: "Gmail API quota near exhaustion (>80%)"
  description: "Current usage: {{ $value | humanizePercentage }} of daily quota. Consider rate limiting or upgrading quota."
  runbook_url: "https://docs.relay.dev/runbooks/gmail-quota"
```

---

### 3.4 Feature Adoption Alerts

#### **Alert: StudioGmailOAuthFailureHigh**
**Description**: Studio OAuth success rate drops below 90%
**Severity**: Warning

```yaml
alert: StudioGmailOAuthFailureHigh
expr: |
  sum(rate(studio_google_oauth_flow_total{result="success"}[5m]))
    /
  sum(rate(studio_google_oauth_flow_total[5m]))
  < 0.9
for: 10m
labels:
  severity: warning
  team: frontend
annotations:
  summary: "Studio Gmail OAuth success rate is low (<90%)"
  description: "Success rate: {{ $value | humanizePercentage }}. Check for user_cancelled vs error outcomes."
```

---

## 4. Grafana Dashboard Additions

### 4.1 Gmail Rich Email Overview Panel

**Dashboard**: `relay-actions-gmail.json`
**Panel Name**: "Gmail Rich Email Features"
**Type**: Time series graph

**Metrics**:
1. **HTML Email Usage** (line graph)
   - Query: `sum(rate(studio_gmail_send_attempts_total{has_html="true"}[5m]))`
   - Color: Blue
   - Unit: ops/sec

2. **Attachment Usage** (line graph)
   - Query: `sum(rate(studio_gmail_send_attempts_total{has_attachments="true"}[5m]))`
   - Color: Green
   - Unit: ops/sec

3. **Plain Text Only** (line graph)
   - Query: `sum(rate(studio_gmail_send_attempts_total{has_html="false",has_attachments="false"}[5m]))`
   - Color: Gray
   - Unit: ops/sec

**Thresholds**: None (informational only)

---

### 4.2 MIME Build Performance Panel

**Dashboard**: `relay-actions-gmail.json`
**Panel Name**: "MIME Build Latency (P50/P95/P99)"
**Type**: Time series graph

**Metrics**:
1. **P50 Latency**
   - Query: `histogram_quantile(0.50, sum by (le) (rate(gmail_mime_build_seconds_bucket[5m])))`
   - Color: Green
   - Unit: seconds

2. **P95 Latency**
   - Query: `histogram_quantile(0.95, sum by (le) (rate(gmail_mime_build_seconds_bucket[5m])))`
   - Color: Yellow
   - Unit: seconds

3. **P99 Latency**
   - Query: `histogram_quantile(0.99, sum by (le) (rate(gmail_mime_build_seconds_bucket[5m])))`
   - Color: Red
   - Unit: seconds

**Thresholds**:
- Warning: P95 > 500ms (yellow line)
- Critical: P99 > 1s (red line)

---

### 4.3 Attachment & Inline Stats Panel

**Dashboard**: `relay-actions-gmail.json`
**Panel Name**: "Attachment Bytes & Inline CIDs"
**Type**: Stat panel (single value with sparkline)

**Metrics**:
1. **Total Attachment MB/min**
   - Query: `sum(rate(gmail_attachment_bytes_total{result="accepted"}[1m])) * 60 / 1024 / 1024`
   - Unit: MB/min
   - Thresholds: None

2. **Rejected Attachments/min**
   - Query: `sum(rate(gmail_attachment_bytes_total{result=~"rejected_.*"}[1m])) * 60`
   - Unit: count/min
   - Thresholds:
     - Warning: >10/min (yellow)
     - Critical: >50/min (red)

3. **Inline CID Match Rate**
   - Query: `sum(rate(gmail_inline_refs_total{result="matched"}[5m])) / sum(rate(gmail_inline_refs_total[5m]))`
   - Unit: percentage
   - Thresholds:
     - Critical: <90% (red)
     - Warning: <95% (yellow)
     - Good: ≥95% (green)

---

### 4.4 Validation Errors Breakdown Panel

**Dashboard**: `relay-actions-gmail.json`
**Panel Name**: "Gmail Validation Errors (Top 5)"
**Type**: Bar gauge

**Metrics**:
- Query: `topk(5, sum by (error_reason) (rate(gmail_validation_errors_total[5m])))`
- Unit: ops/sec
- Orientation: Horizontal
- Color: Red gradient

**Thresholds**: None (informational)

---

### 4.5 HTML Sanitization Activity Panel

**Dashboard**: `relay-actions-gmail.json`
**Panel Name**: "HTML Sanitization Changes"
**Type**: Stacked area graph

**Metrics**:
1. **Tags Removed**
   - Query: `sum(rate(gmail_html_sanitization_changes_total{change_type="tag_removed"}[5m]))`
   - Color: Orange

2. **Attributes Removed**
   - Query: `sum(rate(gmail_html_sanitization_changes_total{change_type="attribute_removed"}[5m]))`
   - Color: Yellow

3. **CSS Blocked**
   - Query: `sum(rate(gmail_html_sanitization_changes_total{change_type="css_blocked"}[5m]))`
   - Color: Red

**Thresholds**: None (informational)

---

### 4.6 Studio OAuth Success Rate Panel

**Dashboard**: `relay-studio.json`
**Panel Name**: "Google OAuth Success Rate (5m)"
**Type**: Gauge

**Metrics**:
- Query: `sum(rate(studio_google_oauth_flow_total{result="success"}[5m])) / sum(rate(studio_google_oauth_flow_total[5m]))`
- Unit: percentage (0-100)
- Min: 0
- Max: 100

**Thresholds**:
- Critical: <80% (red)
- Warning: <90% (yellow)
- Good: ≥90% (green)

---

## 5. Structured Logging

### 5.1 MIME Build Logs

**Log Level**: INFO
**Event**: `gmail.mime.build`

**Fields**:
```json
{
  "event": "gmail.mime.build",
  "preview_id": "prev_abc123",
  "mime_structure": "multipart/related",
  "attachment_count": 2,
  "inline_count": 3,
  "total_bytes": 1048576,
  "build_duration_ms": 42,
  "base64_duration_ms": 28,
  "sanitization_duration_ms": 8
}
```

---

### 5.2 HTML Sanitization Logs

**Log Level**: WARNING
**Event**: `gmail.html.sanitized`

**Fields**:
```json
{
  "event": "gmail.html.sanitized",
  "preview_id": "prev_abc123",
  "html_size_bytes": 32768,
  "html_sha256": "a1b2c3d4...",
  "tags_removed": 5,
  "attributes_removed": 12,
  "css_blocked": 3,
  "removed_tags": ["script", "iframe", "object"],
  "duration_ms": 15
}
```

**Note**: Only log SHA256 digest of HTML content, NEVER raw HTML (privacy policy).

---

### 5.3 Attachment Validation Logs

**Log Level**: WARNING
**Event**: `gmail.attachment.rejected`

**Fields**:
```json
{
  "event": "gmail.attachment.rejected",
  "preview_id": "prev_abc123",
  "filename_sha256": "e5f6g7h8...",
  "content_type": "application/x-executable",
  "size_bytes": 5242880,
  "rejection_reason": "attachment_type_blocked"
}
```

**Note**: Log SHA256 of filename only, NEVER actual filename (may contain PII).

---

### 5.4 Inline CID Orphan Logs

**Log Level**: WARNING
**Event**: `gmail.inline.orphan_cid`

**Fields**:
```json
{
  "event": "gmail.inline.orphan_cid",
  "preview_id": "prev_abc123",
  "orphan_cids": ["cid:image1", "cid:logo"],
  "inline_count": 1,
  "html_cid_refs": 3
}
```

---

## 6. SLO Mapping

| **SLO** | **Target** | **Metrics** | **Alert** |
|---------|-----------|-------------|-----------|
| **Latency** | P95 < 500ms | `gmail_mime_build_seconds` | `GmailMIMEBuildSlow` |
| **Error Rate** | Success > 99% | `gmail_validation_errors_total` | `GmailValidationErrorsHigh` |
| **Availability** | 99.5% uptime | Gmail API quota exhaustion | `GmailQuotaNearExhaustion` |
| **Data Quality** | Inline CID match > 95% | `gmail_inline_refs_total` | `GmailInlineCIDOrphansHigh` |

---

## 7. Rollout Monitoring Plan

### Phase 1: Shadow Mode (Week 1)
**Enabled**: `PROVIDER_GOOGLE_RICH_EMAIL_ENABLED=false`
**Monitoring**:
- Baseline metrics from existing Gmail send (plain text only)
- Verify Prometheus scrape targets healthy
- Confirm dashboards render correctly

---

### Phase 2: Internal Canary (Week 2)
**Enabled**: `PROVIDER_GOOGLE_RICH_EMAIL_ENABLED=true` (internal users only)
**Monitoring**:
- Track `studio_gmail_send_attempts_total` split by `has_html`/`has_attachments`
- Monitor MIME build P95 latency (target: <200ms)
- Check validation error reasons (expect low rate initially)
- **Go/No-Go Gate**: Error rate <1%, P95 latency <500ms

---

### Phase 3: Limited Beta (Week 3)
**Enabled**: 10% of production traffic
**Monitoring**:
- Monitor attachment bytes/min (check for quota impact)
- Track HTML sanitization changes (high removal rate = UX issue)
- Alert on orphan CID rate (should be <5%)
- **Go/No-Go Gate**: No P0/P1 incidents, SLOs green for 48h

---

### Phase 4: Full Rollout (Week 4)
**Enabled**: 100% of production traffic
**Monitoring**:
- All alerts active
- Daily SLO review
- Weekly deep-dive on top validation errors

---

## 8. Debugging Playbook

### Issue: High MIME Build Latency

**Symptoms**: `GmailMIMEBuildSlow` alert firing

**Investigation**:
1. Check attachment count distribution:
   ```promql
   sum by (attachment_count) (rate(gmail_mime_build_seconds_count[5m]))
   ```
2. Check for large attachments:
   ```promql
   sum(rate(gmail_attachment_bytes_total[5m])) / sum(rate(gmail_mime_build_seconds_count[5m]))
   ```
3. Review logs for `gmail.mime.build` with `build_duration_ms > 500`

**Mitigation**:
- If large attachments: Add client-side validation for file sizes
- If Base64 encoding slow: Profile Python `base64` library, consider C extension
- If MIME assembly slow: Optimize `email.mime` library usage

---

### Issue: High Validation Error Rate

**Symptoms**: `GmailValidationErrorsHigh` alert firing

**Investigation**:
1. Check top error reasons:
   ```promql
   topk(5, sum by (error_reason) (rate(gmail_validation_errors_total[5m])))
   ```
2. Review logs for repeated patterns (e.g., same user retrying)

**Mitigation**:
- If `attachment_too_large`: Lower Studio UI max file size or show clearer error
- If `html_invalid_encoding`: Add client-side encoding validation
- If `attachment_type_blocked`: Update Studio UI to pre-filter file types

---

### Issue: Orphan Inline CID References

**Symptoms**: `GmailInlineCIDOrphansHigh` alert firing

**Investigation**:
1. Review logs for `gmail.inline.orphan_cid` events
2. Check HTML for malformed `cid:` references:
   ```promql
   sum(rate(gmail_inline_refs_total{result="orphan_cid"}[5m]))
   ```

**Mitigation**:
- Add validation: require every HTML `cid:` to match an `inline[]` entry
- Studio UI: auto-generate CIDs when user inserts images

---

## 9. Open Questions

1. **Gmail API Quota**: What is our actual daily quota? Need to adjust `GmailQuotaNearExhaustion` alert threshold.
2. **Attachment Storage**: If we adopt presigned URLs for large attachments, add metrics for URL generation latency.
3. **HTML Sanitization Library**: Should we instrument `bleach` library internals, or rely on top-level timing only?
4. **Studio Analytics**: Do we need separate metrics for Studio vs API-driven Gmail sends?
5. **Cardinality**: Monitor Prometheus cardinality impact of `content_type` label (could explode if users send exotic MIME types).

---

## 10. References

- Sprint 54 Plan: `docs/planning/SPRINT-54-PLAN.md`
- Gmail Rich Email Spec: `docs/specs/GMAIL-RICH-EMAIL-SPEC.md`
- Test Matrix: `tests/plans/SPRINT-54-TEST-MATRIX.md`
- Sprint 48 Observability: `docs/observability/SPRINT-48-OBSERVABILITY.md`
- Prometheus Best Practices: https://prometheus.io/docs/practices/naming/
- Grafana Golden Signals: `observability/templates/grafana-golden-signals-ui.json`
