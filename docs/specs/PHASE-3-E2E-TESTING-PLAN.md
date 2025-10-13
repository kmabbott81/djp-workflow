# Phase 3: E2E Testing Plan - Gmail Rich Email

**Date:** 2025-10-09
**Sprint:** 54 - Phase C (Gmail Rich Email)
**Status:** PLANNING

## Overview

End-to-end testing with real Gmail API to verify the complete path:
**MIME Builder → GoogleAdapter → Gmail API → Telemetry → Rollout Controller**

## Prerequisites

### Completed
- ✅ Phase 1: MIME builder, validation, sanitization (96 tests passing)
- ✅ Phase 2: GoogleAdapter integration (90 tests passing)
- ✅ Rollout infrastructure (Sprint 53.5)
- ✅ OAuth token management (Sprint 53)

### Required Setup
- [ ] Merge PR #34 (rollout infrastructure)
- [ ] Merge PR #35 (Gmail rich email)
- [ ] Configure GitHub secrets
- [ ] Set up test Gmail account with OAuth tokens
- [ ] Enable telemetry infrastructure

## Test Environment Configuration

### Environment Variables

```bash
# Provider Config
PROVIDER_GOOGLE_ENABLED=true
GOOGLE_CLIENT_ID=<from-gcp-console>
GOOGLE_CLIENT_SECRET=<from-gcp-console>

# Internal-Only Controls (start restrictive)
GOOGLE_INTERNAL_ONLY=true
GOOGLE_INTERNAL_ALLOWED_DOMAINS=example.com,yourdomain.com
GOOGLE_INTERNAL_TEST_RECIPIENTS=your-test-email@gmail.com

# Rollout Config
ROLLOUT_DRY_RUN=true  # Start in dry-run mode
REDIS_URL=redis://localhost:6379  # Or Railway Redis URL

# Telemetry
TELEMETRY_ENABLED=true
PROMETHEUS_PUSHGATEWAY_URL=http://localhost:9091  # Or Railway URL

# Database
DATABASE_URL=<postgresql-url>  # For OAuth tokens

# Actions
ACTIONS_ENABLED=true
ACTIONS_SIGNING_SECRET=<generate-with-openssl-rand-base64-32>

# Webhook (optional for testing)
WEBHOOK_URL=https://webhook.site/<your-unique-id>
```

### GitHub Secrets/Vars Needed

**Secrets:**
- `GOOGLE_CLIENT_SECRET` - OAuth client secret from GCP
- `ACTIONS_SIGNING_SECRET` - For action payload signing
- `DATABASE_URL` - PostgreSQL connection string

**Variables:**
- `GOOGLE_CLIENT_ID` - OAuth client ID from GCP
- `REDIS_URL` - Redis connection string
- `PROMETHEUS_BASE_URL` - Prometheus/Pushgateway endpoint
- `GOOGLE_INTERNAL_ALLOWED_DOMAINS` - Comma-separated internal domains

### Test Gmail Account Setup

1. Create dedicated test account: `relay-test@yourdomain.com` (or use Gmail)
2. Grant OAuth consent via existing flow:
   ```bash
   # Visit /auth/google/consent endpoint
   # Authorize with test account
   # Verify tokens stored in database
   ```
3. Verify scopes include: `https://www.googleapis.com/auth/gmail.send`

### Redis Setup

For local testing:
```bash
# Docker
docker run -d -p 6379:6379 redis:alpine

# Or Railway
railway run redis-cli ping
```

Initialize rollout state:
```bash
redis-cli SET flags:google:rollout_percent 0
redis-cli SET flags:google:rollout_enabled true
```

### Prometheus/Pushgateway Setup

For local testing:
```bash
# Pushgateway
docker run -d -p 9091:9091 prom/pushgateway

# Prometheus
docker run -d -p 9090:9090 -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml prom/prometheus

# Verify
curl http://localhost:9091/metrics
curl http://localhost:9090/-/healthy
```

## E2E Test Scenarios

### Scenario 1: Text-Only Email (Baseline)

**Purpose:** Verify basic Gmail send still works after integration

**Test:**
```python
params = {
    "to": "relay-test@yourdomain.com",
    "subject": "E2E Test: Text Only",
    "text": "This is a plain text email sent via E2E test."
}
```

**Expected:**
- ✅ Preview succeeds
- ✅ Execute succeeds
- ✅ Email received in Gmail inbox
- ✅ Metrics recorded: `action_execution_total{provider="google", action="gmail.send", status="ok"}`
- ✅ Correlation ID logged (not in response)
- ✅ Rollout controller observes latency/error rate (dry-run mode)

### Scenario 2: HTML + Text Fallback

**Purpose:** Verify HTML sanitization and multipart/alternative

**Test:**
```python
params = {
    "to": "relay-test@yourdomain.com",
    "subject": "E2E Test: HTML Email",
    "text": "Fallback plain text",
    "html": """
    <html>
    <body>
        <h1 style="color: blue;">Rich Email Test</h1>
        <p>This is <strong>HTML</strong> content.</p>
        <script>alert('xss')</script>  <!-- Should be sanitized -->
    </body>
    </html>
    """
}
```

**Expected:**
- ✅ Preview returns `sanitized_html` (no `<script>` tag)
- ✅ Preview returns `sanitization_summary` with `tag_removed: 1`
- ✅ Email received with HTML rendering (blue header)
- ✅ XSS blocked (script tag removed)
- ✅ Metrics: `gmail_html_sanitization_changes_total{change_type="tag_removed"}`

### Scenario 3: HTML + Inline Image

**Purpose:** Verify CID references and multipart/related

**Test:**
```python
import base64

# Create small test image (1x1 red pixel PNG)
red_pixel = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8DwHwAFBQIAX8jx0gAAAABJRU5ErkJggg=="
)

params = {
    "to": "relay-test@yourdomain.com",
    "subject": "E2E Test: Inline Image",
    "text": "Fallback: [Logo image]",
    "html": '<html><body><img src="cid:logo" alt="Logo" /></body></html>',
    "inline": [
        {
            "cid": "logo",
            "filename": "logo.png",
            "content_type": "image/png",
            "data": base64.b64encode(red_pixel).decode()
        }
    ]
}
```

**Expected:**
- ✅ Preview succeeds (CID validation passes)
- ✅ Email received with inline image displayed
- ✅ Image not shown as attachment (Content-Disposition: inline)
- ✅ Metrics: `gmail_inline_refs_total{result="matched"}`

### Scenario 4: Attachments

**Purpose:** Verify multipart/mixed with file attachments

**Test:**
```python
import base64

# Create small PDF attachment
pdf_content = b"%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n>>\nendobj\n%%EOF"

params = {
    "to": "relay-test@yourdomain.com",
    "subject": "E2E Test: Attachment",
    "text": "Please see attached PDF.",
    "attachments": [
        {
            "filename": "report.pdf",
            "content_type": "application/pdf",
            "data": base64.b64encode(pdf_content).decode()
        }
    ]
}
```

**Expected:**
- ✅ Email received with attachment
- ✅ Attachment downloadable and named correctly
- ✅ Metrics: `gmail_attachment_bytes_total{result="accepted"}`

### Scenario 5: Full Complexity (HTML + Inline + Attachments)

**Purpose:** Verify nested multipart structure

**Test:**
```python
params = {
    "to": "relay-test@yourdomain.com",
    "subject": "E2E Test: Full Complexity",
    "text": "Fallback text with [inline image] and attachment",
    "html": '<html><body><h1>Report</h1><img src="cid:chart" /></body></html>',
    "inline": [
        {
            "cid": "chart",
            "filename": "chart.png",
            "content_type": "image/png",
            "data": base64.b64encode(red_pixel).decode()
        }
    ],
    "attachments": [
        {
            "filename": "data.csv",
            "content_type": "text/csv",
            "data": base64.b64encode(b"col1,col2\nval1,val2\n").decode()
        }
    ]
}
```

**Expected:**
- ✅ All content types delivered correctly
- ✅ Inline image in HTML, attachment separate
- ✅ MIME structure: `multipart/mixed` > `multipart/related` > `multipart/alternative`

### Scenario 6: Validation Errors

**Purpose:** Verify structured error handling

**Test Cases:**
```python
# 6a: Oversized attachment (26MB)
params = {
    "to": "relay-test@yourdomain.com",
    "subject": "E2E Test: Oversized",
    "text": "Body",
    "attachments": [{"filename": "huge.bin", "content_type": "application/octet-stream", "data": base64.b64encode(b"x" * 26_000_000).decode()}]
}
# Expected: ValueError with error_code="validation_error_attachment_too_large"

# 6b: Blocked MIME type (.exe)
params = {
    "to": "relay-test@yourdomain.com",
    "subject": "E2E Test: Blocked MIME",
    "text": "Body",
    "attachments": [{"filename": "malware.exe", "content_type": "application/x-msdownload", "data": base64.b64encode(b"MZ").decode()}]
}
# Expected: ValueError with error_code="validation_error_blocked_mime_type"

# 6c: Orphan CID
params = {
    "to": "relay-test@yourdomain.com",
    "subject": "E2E Test: Orphan CID",
    "text": "Body",
    "html": '<img src="cid:missing" />',
    "inline": [{"cid": "wrong", "filename": "img.png", "content_type": "image/png", "data": "..."}]
}
# Expected: ValueError with error_code="validation_error_missing_inline_image"
```

**Expected:**
- ✅ Errors caught at preview stage (no Gmail API call)
- ✅ Structured error payloads returned with correlation_id
- ✅ Metrics: `action_error_total{provider="google", action="gmail.send", reason=<error_code>}`

### Scenario 7: Internal-Only Controls

**Purpose:** Verify recipient domain filtering

**Test:**
```python
# 7a: Allowed internal domain
params = {"to": "user@example.com", "subject": "Test", "text": "Body"}
# Expected: Succeeds (if example.com in GOOGLE_INTERNAL_ALLOWED_DOMAINS)

# 7b: Blocked external domain
params = {"to": "external@notallowed.com", "subject": "Test", "text": "Body"}
# Expected: ValueError with error_code="internal_only_recipient_blocked"

# 7c: Test recipient bypass
params = {"to": "your-test-email@gmail.com", "subject": "Test", "text": "Body"}
# Expected: Succeeds (if in GOOGLE_INTERNAL_TEST_RECIPIENTS)
```

**Expected:**
- ✅ Domain allowlist enforced
- ✅ Test recipient bypass works
- ✅ Clear error message with allowed domains in details

### Scenario 8: Rollout Controller Observation (Dry-Run)

**Purpose:** Verify controller observes metrics without making changes

**Setup:**
```bash
ROLLOUT_DRY_RUN=true
redis-cli SET flags:google:rollout_percent 10  # Controller should observe but not change
```

**Test:**
- Run scenarios 1-5 (10 successful sends)
- Check Prometheus metrics:
  - `action_latency_seconds` (P95 < 2s)
  - `action_error_total` (should be 0)
- Wait for controller evaluation cycle (default 5 minutes)

**Expected:**
- ✅ Controller logs: "DRY_RUN: Would promote google from 10% to 20%"
- ✅ Rollout percent remains at 10% (no actual change)
- ✅ Audit log entry created with `dry_run: true`
- ✅ Pushgateway shows controller metrics

## Metrics to Monitor

### Action Metrics (Prometheus)
```promql
# P95 latency
histogram_quantile(0.95, rate(action_latency_seconds_bucket{provider="google", action="gmail.send"}[5m]))

# Error rate
rate(action_error_total{provider="google", action="gmail.send"}[5m])
  / rate(action_execution_total{provider="google", action="gmail.send"}[5m])

# Success count
increase(action_execution_total{provider="google", action="gmail.send", status="ok"}[1h])
```

### MIME Builder Metrics
```promql
# Build time P95
histogram_quantile(0.95, rate(gmail_mime_build_seconds_bucket[5m]))

# Attachment throughput
rate(gmail_attachment_bytes_total[5m])

# Sanitization activity
rate(gmail_html_sanitization_changes_total{change_type="tag_removed"}[5m])

# CID mismatch rate
rate(gmail_inline_refs_total{result="orphan_cid"}[5m])
  / rate(gmail_inline_refs_total[5m])
```

### Rollout Controller Metrics (Pushgateway)
```promql
# Controller evaluation results
rollout_controller_evaluation_total{provider="google"}

# Current rollout percent
rollout_feature_percent{provider="google"}

# Promotion/rollback counts
rollout_controller_action_total{provider="google", action="promote"}
rollout_controller_action_total{provider="google", action="rollback"}
```

## Test Execution Steps

### Step 1: Environment Setup (Local)

```bash
# 1. Start infrastructure
docker-compose up -d  # Redis, Pushgateway, Prometheus

# 2. Set environment variables
export PROVIDER_GOOGLE_ENABLED=true
export GOOGLE_INTERNAL_ONLY=true
export ROLLOUT_DRY_RUN=true
export TELEMETRY_ENABLED=true
# ... (see "Environment Variables" section)

# 3. Initialize Redis
redis-cli SET flags:google:rollout_percent 0
redis-cli SET flags:google:rollout_enabled true

# 4. Run database migrations
alembic upgrade head

# 5. Verify OAuth tokens exist
python -c "from src.auth.oauth.tokens import OAuthTokenCache; import asyncio; print(asyncio.run(OAuthTokenCache().get_tokens_with_auto_refresh('google', '<workspace-id>', '<actor-id>')))"
```

### Step 2: Run E2E Test Script

```bash
# Create and run E2E test script
python scripts/e2e_gmail_test.py --scenarios all --verbose

# Or run specific scenarios
python scripts/e2e_gmail_test.py --scenarios 1,2,3 --dry-run
```

### Step 3: Verify Telemetry

```bash
# Check Prometheus metrics
curl http://localhost:9090/api/v1/query?query=action_execution_total

# Check Pushgateway
curl http://localhost:9091/metrics | grep rollout

# Check Redis state
redis-cli GET flags:google:rollout_percent
```

### Step 4: Monitor Controller (24-48 hours)

```bash
# Tail controller logs
tail -f logs/rollout_controller.log

# Watch for dry-run entries
grep "DRY_RUN:" logs/rollout_controller.log

# Check audit log
tail -f audit/audit-$(date +%Y-%m-%d).jsonl | jq 'select(.event=="rollout_decision")'
```

### Step 5: Gradual Enable

After 24-48 hours of stable dry-run observation:

```bash
# Disable dry-run mode
export ROLLOUT_DRY_RUN=false

# Controller will now actually update Redis
# Watch it promote from 0% → 10% → 20% → ...

# Monitor carefully
watch -n 30 'redis-cli GET flags:google:rollout_percent'
```

## Success Criteria

### Phase 3 Complete When:

1. ✅ All 8 E2E scenarios pass (text, HTML, inline, attachments, full, errors, controls)
2. ✅ Emails received and correctly formatted in Gmail inbox
3. ✅ Telemetry metrics flowing to Prometheus/Pushgateway
4. ✅ Controller observes metrics in dry-run mode (no regressions)
5. ✅ Audit logs contain expected entries
6. ✅ No unexpected errors in logs
7. ✅ P95 latency < 2 seconds
8. ✅ Error rate < 1% (should be 0% for internal testing)

## Rollback Plan

### If Issues Found:

**Immediate:**
```bash
# Stop all traffic
redis-cli SET flags:google:rollout_percent 0
# or
export PROVIDER_GOOGLE_ENABLED=false
```

**Investigate:**
- Check logs: `tail -f logs/*.jsonl`
- Check metrics: Prometheus dashboard
- Check Gmail inbox: Are emails malformed?
- Check MIME structure: Save raw message, parse with email.parser

**Fix and Retry:**
- Fix code issue
- Run unit tests again
- Re-run specific E2E scenario
- Verify fix before re-enabling

## Timeline

**Day 1-2:** Environment setup, OAuth token verification
**Day 3:** Run E2E scenarios 1-7 (all tests)
**Day 4-5:** Monitor controller in dry-run mode (24-48 hours)
**Day 6:** Review metrics, decide to proceed or iterate
**Day 7:** Disable dry-run, observe first automated promotion

**Total:** ~1 week for complete Phase 3 validation

## Next Phase Preview

After Phase 3 completes:
- **Phase 4:** Observability enhancements (Prometheus rules, Grafana dashboards)
- **Phase 5:** Gradual public rollout (flip `GOOGLE_INTERNAL_ONLY=false`)
- **Phase 6:** Studio UX integration (rich email composer)

---

## Appendix: E2E Test Script Template

See `scripts/e2e_gmail_test.py` for implementation.

Key features:
- Parametrized test scenarios
- Automatic metric verification
- Gmail inbox verification (via IMAP if needed)
- Detailed logging with correlation IDs
- JSON output for CI integration

---

**STATUS:** Ready to implement
**OWNER:** Engineering team
**REVIEWS:** Product (acceptance criteria), SRE (monitoring), Security (OAuth/permissions)
