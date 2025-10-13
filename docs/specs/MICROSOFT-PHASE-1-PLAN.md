# Microsoft Integration - Phase 1 Plan

**Sprint:** 55
**Status:** PLANNING
**Start Date:** 2025-10-11
**Target Completion:** Sprint 55 End

---

## Executive Summary

Phase 1 establishes the foundation for Microsoft Outlook email integration with feature parity to Gmail Sprint 53/54 work. This includes Azure AD OAuth with PKCE, `outlook.send` adapter supporting rich email (HTML, inline images, attachments), production-grade telemetry, and rollout controller compatibility.

**Key Principle:** Reuse Gmail patterns (auth, MIME, telemetry, rollout) with provider-specific adaptations for Microsoft Graph API.

---

## Scope

### In Scope
- **Azure AD OAuth** (single tenant) with PKCE + offline refresh
- **outlook.send adapter** with rich email parity (HTML, inline images, attachments)
- **Telemetry parity** (exec/error/latency metrics, structured errors)
- **Recording rules + alerts** (error rate, latency, with traffic guards)
- **Rollout controller integration** (feature="microsoft", flags, gates)
- **Unit tests + 1 gated integration test**
- **Documentation** (OAuth setup, telemetry, completion evidence)

### Out of Scope (Future Phases)
- **Phase 2:** Advanced features (read receipts, categories, importance flags)
- **Phase 3:** Batch send API (up to 20 messages/request)
- **Phase 4:** Exchange Online vs Office 365 tenant detection
- **Phase 5:** Multi-tenant support (customer-provided tenant IDs)

---

## Technical Design

### 1. Authentication & Authorization

#### Azure AD OAuth Flow
**File:** `src/auth/oauth/ms_tokens.py`

**Pattern:** Reuse Gmail OAuth patterns from Sprint 53
- Authorization Code flow with PKCE (S256)
- Offline access for refresh tokens
- Redis-backed token cache with TTL
- Distributed lock for refresh (prevent thundering herd)

**Scopes Required:**
```
Mail.Send         # Send emails on behalf of user
offline_access    # Get refresh token
openid           # OIDC authentication
email            # User email claim
profile          # User profile info
```

**Environment Variables:**
```bash
# Azure AD App Registration
MS_CLIENT_ID=<app-id>
MS_CLIENT_SECRET=<client-secret>
MS_TENANT_ID=<tenant-id>  # Single tenant for Phase 1
MS_REDIRECT_URI=http://localhost:8003/oauth/microsoft/callback

# Provider flags
PROVIDER_MICROSOFT_ENABLED=false  # Default disabled until rollout
```

**Redis Keys:**
```
oauth:microsoft:access_token:<user_id>    # TTL 1h
oauth:microsoft:refresh_token:<user_id>   # TTL 90d
oauth:microsoft:lock:<user_id>            # Refresh lock, TTL 10s
```

**Key Methods:**
```python
class MicrosoftTokenManager:
    async def get_access_token(user_id: str) -> str:
        """Get valid access token, refresh if expired."""

    async def refresh_access_token(user_id: str) -> str:
        """Refresh token with distributed lock."""

    async def exchange_code_for_tokens(code: str, code_verifier: str) -> TokenPair:
        """Exchange auth code for access + refresh tokens."""

    async def revoke_tokens(user_id: str):
        """Revoke tokens and clear cache."""
```

---

### 2. Outlook Send Adapter

#### File Structure
```
src/actions/adapters/
├── microsoft.py          # Main adapter (outlook.send action)
├── microsoft_mime.py     # Graph API payload builder (reuses Gmail MIME output)
└── microsoft_errors.py   # Error code mapping
```

#### Action Interface
**File:** `src/actions/adapters/microsoft.py`

**Pattern:** Parity with Gmail adapter from Sprint 53

```python
@action("outlook.send")
async def outlook_send(
    to: list[EmailAddress],
    subject: str,
    body_html: str | None = None,
    body_text: str | None = None,
    cc: list[EmailAddress] | None = None,
    bcc: list[EmailAddress] | None = None,
    attachments: list[Attachment] | None = None,
    inline_images: list[InlineImage] | None = None,
    reply_to: list[EmailAddress] | None = None,
    user_id: str,
) -> SendResult:
    """
    Send rich email via Microsoft Graph API.

    Constraints:
    - Max 150 recipients (to + cc + bcc combined, Graph API limit)
    - Max 4 MB total message size (including attachments)
    - Max 20 attachments
    - Inline images use Content-ID (cid:) references
    """
```

**Gating Logic:**
```python
# Provider flag check
if not prefs.PROVIDER_MICROSOFT_ENABLED:
    raise ActionDisabledError("Provider microsoft is disabled")

# Internal-only domain check (Phase 1)
if not is_internal_domain(to[0].address):
    raise ActionDisabledError("Microsoft provider is internal-only during rollout")

# Rollout gate check
if not await rollout_gate.allow("microsoft", user_id):
    raise ActionGatedError("User not in microsoft rollout")
```

**Graph API Call:**
```python
# POST /v1.0/me/sendMail
# https://learn.microsoft.com/en-us/graph/api/user-sendmail

POST https://graph.microsoft.com/v1.0/me/sendMail
Authorization: Bearer {access_token}
Content-Type: application/json

{
  "message": {
    "subject": "...",
    "body": {
      "contentType": "HTML",
      "content": "..."
    },
    "toRecipients": [{"emailAddress": {"address": "..."}}],
    "ccRecipients": [...],
    "bccRecipients": [...],
    "attachments": [
      {
        "@odata.type": "#microsoft.graph.fileAttachment",
        "name": "document.pdf",
        "contentBytes": "base64-encoded-content",
        "contentType": "application/pdf",
        "contentId": "cid-123"  # For inline images
      }
    ]
  },
  "saveToSentItems": true
}
```

---

#### MIME to Graph Translation
**File:** `src/actions/adapters/microsoft_mime.py`

**Strategy:** Reuse Gmail MIME builder output, translate to Graph JSON

```python
def translate_mime_to_graph(mime_output: MimeOutput) -> dict:
    """
    Translate Gmail MIME builder output to Graph API payload.

    Mappings:
    - HTML body → message.body.content (contentType="HTML")
    - Attachments → fileAttachment with base64 contentBytes
    - Inline images → fileAttachment with contentId + isInline=true
    - Recipients → toRecipients/ccRecipients/bccRecipients
    """
```

**Inline Image Handling:**
```python
# Gmail MIME uses Content-ID headers
# Graph uses contentId field + isInline flag

{
  "@odata.type": "#microsoft.graph.fileAttachment",
  "name": "logo.png",
  "contentType": "image/png",
  "contentBytes": "base64-data",
  "contentId": "logo123",     # Maps to cid:logo123 in HTML
  "isInline": true
}
```

---

#### Error Mapping
**File:** `src/actions/adapters/microsoft_errors.py`

**Pattern:** Map Graph API error codes to structured error codes

```python
ERROR_CODE_MAP = {
    # Auth errors
    "InvalidAuthenticationToken": "MS_AUTH_INVALID",
    "ExpiredAuthenticationToken": "MS_AUTH_EXPIRED",
    "InsufficientPermissions": "MS_AUTH_INSUFFICIENT_PERMS",

    # Rate limiting
    "TooManyRequests": "MS_API_THROTTLED_429",
    "ServiceUnavailable": "MS_API_UNAVAILABLE_503",

    # Validation errors
    "InvalidRecipients": "INVALID_RECIPIENT",
    "RequestBodyTooLarge": "ATTACHMENT_TOO_LARGE",
    "AttachmentSizeLimitExceeded": "ATTACHMENT_TOO_LARGE",

    # Policy blocks
    "MessageBlocked": "MS_PROVIDER_POLICY_BLOCKED",
    "RecipientNotFound": "RECIPIENT_NOT_FOUND",
}

def map_graph_error(error_code: str, error_message: str) -> StructuredError:
    """Map Graph API error to structured error with provider context."""
```

---

### 3. Telemetry & Observability

#### Metrics Emitted
**File:** `src/actions/adapters/microsoft.py`

**Pattern:** Identical to Gmail metrics, provider="microsoft"

```python
# Execution counter
action_exec_total.labels(
    provider="microsoft",
    action="outlook.send",
    status="ok" | "error"
).inc()

# Error counter
action_error_total.labels(
    provider="microsoft",
    action="outlook.send"
).inc()

# Latency histogram
action_latency_seconds.labels(
    provider="microsoft",
    action="outlook.send",
    status="ok" | "error"
).observe(duration)

# Structured errors
structured_error_total.labels(
    provider="microsoft",
    action="outlook.send",
    code="MS_AUTH_INVALID",
    source="adapter"
).inc()
```

---

#### Recording Rules
**File:** `config/prometheus/prometheus-recording-microsoft.yml`

**Pattern:** Copy Gmail recording rules with label changes

```yaml
groups:
- name: outlook_send_recording
  interval: 30s
  rules:
  # Execution rate (base metric for guards)
  - record: job:outlook_send_exec_rate:5m
    expr: sum(rate(action_exec_total{provider="microsoft",action="outlook.send"}[5m]))

  # Latency histogram rate
  - record: job:outlook_send_latency_seconds:rate5m
    expr: sum(rate(action_latency_seconds_bucket{provider="microsoft",action="outlook.send"}[5m])) by (le)

  # P95 latency
  - record: job:outlook_send_latency_p95:5m
    expr: histogram_quantile(0.95, job:outlook_send_latency_seconds:rate5m)

  # P95 latency by result (success vs error)
  - record: job:outlook_send_latency_p95_by_result:5m
    expr: histogram_quantile(0.95, sum(rate(action_latency_seconds_bucket{provider="microsoft",action="outlook.send"}[5m])) by (le, status))

  # Error rate with floor
  - record: job:outlook_send_errors_rate:5m
    expr: |
      sum(rate(action_error_total{provider="microsoft",action="outlook.send"}[5m]))
      / clamp_min(job:outlook_send_exec_rate:5m, 1)

  # Top 5 structured error codes (cardinality guard)
  - record: job:structured_error_rate_top5_codes_microsoft:5m
    expr: topk(5, sum(rate(structured_error_total{provider="microsoft",action="outlook.send"}[5m])) by (code))
```

---

#### Alert Rules
**File:** `config/prometheus/prometheus-alerts-microsoft.yml`

**Pattern:** Copy Gmail alerts with label changes

```yaml
groups:
- name: outlook_send_alerts
  rules:
  # Error rate warning
  - alert: OutlookSendHighErrorRateWarning
    expr: (job:outlook_send_exec_rate:5m > 0.1) and (job:outlook_send_errors_rate:5m > 0.01)
    for: 10m
    labels:
      severity: warning
      service: relay
      component: outlook
      provider: microsoft
      action: outlook.send
    annotations:
      summary: "Outlook send error rate >1% (warn)"
      description: "Error rate is {{ $value | humanizePercentage }} over the last 5 minutes (threshold: 1%, traffic: {{ query `job:outlook_send_exec_rate:5m` | first | value | humanize }}req/s)"
      runbook_url: "docs/runbooks/outlook-send-high-error-rate.md"

  # Error rate critical
  - alert: OutlookSendHighErrorRateCritical
    expr: (job:outlook_send_exec_rate:5m > 0.1) and (job:outlook_send_errors_rate:5m > 0.05)
    for: 10m
    labels:
      severity: critical
      service: relay
      component: outlook
      provider: microsoft
      action: outlook.send
    annotations:
      summary: "Outlook send error rate >5% (critical)"
      description: "Error rate is {{ $value | humanizePercentage }} over the last 5 minutes (threshold: 5%, traffic: {{ query `job:outlook_send_exec_rate:5m` | first | value | humanize }}req/s)"
      runbook_url: "docs/runbooks/outlook-send-high-error-rate.md"

  # Latency warning
  - alert: OutlookSendHighLatencyWarning
    expr: job:outlook_send_latency_p95:5m > 0.5
    for: 10m
    labels:
      severity: warning
      service: relay
      component: outlook
      provider: microsoft
      action: outlook.send
    annotations:
      summary: "Outlook send P95 > 500ms (warn)"
      description: "P95 latency is {{ $value }}s (threshold: 0.5s)"
      runbook_url: "docs/runbooks/outlook-send-high-latency.md"

  # Latency critical
  - alert: OutlookSendHighLatencyCritical
    expr: job:outlook_send_latency_p95:5m > 2.0
    for: 10m
    labels:
      severity: critical
      service: relay
      component: outlook
      provider: microsoft
      action: outlook.send
    annotations:
      summary: "Outlook send P95 > 2s (critical)"
      description: "P95 latency is {{ $value }}s (threshold: 2.0s)"
      runbook_url: "docs/runbooks/outlook-send-high-latency.md"
```

---

### 4. Rollout Controller Integration

#### Feature Flag
**File:** `src/flags/rollout.py`

**Add Microsoft feature:**
```python
ROLLOUT_FEATURES = {
    "google": RolloutFeature(
        name="google",
        provider="google",
        action="gmail.send",
        initial_percent=0,
        slo_error_rate_threshold=0.01,  # 1%
        slo_latency_p95_ms=500,
    ),
    "microsoft": RolloutFeature(
        name="microsoft",
        provider="microsoft",
        action="outlook.send",
        initial_percent=0,
        slo_error_rate_threshold=0.01,  # 1%
        slo_latency_p95_ms=500,
    ),
}
```

#### Redis Flags
```
flags:microsoft:enabled = false        # Provider master switch
flags:microsoft:internal_only = true   # Restrict to internal domains (Phase 1)
flags:microsoft:rollout_percent = 0    # Rollout percentage (0-100)
flags:microsoft:paused = false         # Emergency stop
```

#### Controller Compatibility
**Pattern:** Controller already supports multiple features via PromQL label filters

**Query for Microsoft SLOs:**
```promql
# Error rate
sum(rate(action_error_total{provider="microsoft",action="outlook.send"}[5m]))
/ clamp_min(sum(rate(action_exec_total{provider="microsoft",action="outlook.send"}[5m])), 1)

# P95 latency
histogram_quantile(0.95, sum(rate(action_latency_seconds_bucket{provider="microsoft",action="outlook.send"}[5m])) by (le))
```

**No controller code changes needed** - just add feature config!

---

### 5. Testing Strategy

#### Unit Tests
**File:** `tests/actions/test_microsoft_adapter_unit.py`

**Coverage:**
- MIME to Graph translation (HTML, attachments, inline images)
- Error code mapping (Graph errors → structured errors)
- Recipient validation (max 150 recipients, valid email format)
- Attachment size limits (4 MB total, max 20 attachments)
- Gating logic (provider flag, internal-only, rollout gate)
- Orphan CID detection (inline images referenced but not attached)

#### Integration Test (Gated)
**File:** `tests/actions/test_microsoft_adapter_integration.py`

**Pattern:** Behind `INTEGRATION_TESTS_ENABLED=true` env var

```python
@pytest.mark.skipif(not INTEGRATION_TESTS_ENABLED, reason="Integration tests disabled")
@pytest.mark.skipif(not MS_INTEGRATION_TOKEN, reason="No Microsoft token")
async def test_outlook_send_happy_path():
    """Send one real email to internal test address."""
    result = await outlook_send(
        to=[EmailAddress(address="test@internal.com")],
        subject="Integration test",
        body_html="<p>Test email</p>",
        user_id="test_user",
    )
    assert result.success
    assert result.message_id
```

**Safety:** Test emails only sent to `@internal.com` addresses

---

### 6. Documentation

#### OAuth Setup Guide
**File:** `docs/specs/MS-OAUTH-SETUP-GUIDE.md`

**Contents:**
1. Azure AD App Registration steps
2. Required API permissions (Mail.Send, offline_access, openid, email, profile)
3. Redirect URI configuration
4. Client secret generation
5. Environment variable setup
6. Testing OAuth flow locally

#### Telemetry Documentation
**File:** `docs/observability/MS-RECORDING-RULES-AND-ALERTS.md`

**Contents:**
1. Recording rules list (15+ rules)
2. Alert rules list (4 alerts: error warn/crit, latency warn/crit)
3. Example PromQL queries
4. Grafana dashboard panel suggestions

#### Completion Evidence
**File:** `docs/evidence/sprint-55/PHASE-1-COMPLETION.md`

**Contents:**
1. Acceptance criteria checklist
2. Test results (unit + integration)
3. Metrics screenshots (exec rate, error rate, latency)
4. Alert validation (synthetic test results)
5. Known limitations (Phase 1 scope)
6. Phase 2 recommendations

---

## Implementation Checklist

### Auth & Flags
- [ ] Create `src/auth/oauth/ms_tokens.py` (token manager class)
- [ ] Add env vars to `src/config/prefs.py` (MS_CLIENT_ID, MS_TENANT_ID, etc.)
- [ ] Add Redis key patterns to docs
- [ ] Create OAuth flow endpoints (authorize, callback, refresh)
- [ ] Unit tests for token refresh + cache + lock

### Adapter
- [ ] Create `src/actions/adapters/microsoft.py` (outlook.send action)
- [ ] Create `src/actions/adapters/microsoft_mime.py` (MIME → Graph translator)
- [ ] Create `src/actions/adapters/microsoft_errors.py` (error mapper)
- [ ] Implement gating logic (provider flag, internal-only, rollout gate)
- [ ] Unit tests for translation + errors + limits

### Telemetry
- [ ] Emit metrics in adapter (exec, error, latency, structured_error)
- [ ] Create `config/prometheus/prometheus-recording-microsoft.yml` (15+ rules)
- [ ] Create `config/prometheus/prometheus-alerts-microsoft.yml` (4 alerts)
- [ ] Add Microsoft feature to `src/flags/rollout.py`

### Tests
- [ ] Unit tests: `tests/actions/test_microsoft_adapter_unit.py` (10+ tests)
- [ ] Integration test: `tests/actions/test_microsoft_adapter_integration.py` (1 gated test)
- [ ] Run tests: `pytest tests/actions/test_microsoft_*.py`

### Docs
- [ ] Create `docs/specs/MS-OAUTH-SETUP-GUIDE.md`
- [ ] Create `docs/observability/MS-RECORDING-RULES-AND-ALERTS.md`
- [ ] Create `docs/evidence/sprint-55/PHASE-1-COMPLETION.md` (template)
- [ ] Update main README with Microsoft provider info

---

## Acceptance Criteria

- [ ] **Auth works:** OAuth flow completes, tokens cached, refresh works
- [ ] **Send works:** One real email sent via integration test (manual or gated)
- [ ] **Gating works:** Provider flag, internal-only, rollout gate all enforced
- [ ] **Metrics flow:** Exec/error/latency metrics appear in Prometheus
- [ ] **Recording rules evaluate:** All 15+ recording rules return data
- [ ] **Alerts evaluate:** All 4 alerts show in Prometheus /alerts (pending state OK)
- [ ] **Unit tests pass:** 10+ tests covering translation, errors, limits
- [ ] **Integration test passes:** Happy path sends real email (behind gate)
- [ ] **Docs complete:** OAuth guide, telemetry docs, completion evidence

---

## Timeline

**Week 1 (Days 1-3):**
- Scaffold auth + adapter + telemetry stubs
- Unit tests pass (no external calls)
- Recording rules + alerts configured

**Week 2 (Days 4-7):**
- Azure AD app registration
- OAuth flow working locally
- Integration test passes (1 real send)
- Metrics flowing to Prometheus

**Week 3 (Days 8-10):**
- Documentation complete
- Completion evidence drafted
- PR review + merge

---

## Known Limitations (Phase 1)

1. **Single tenant only** - Multi-tenant support in Phase 5
2. **Internal-only domains** - Public rollout requires Phase 2 validation
3. **No batch send** - Graph API supports up to 20 messages/request (Phase 3)
4. **No advanced features** - Read receipts, importance, categories (Phase 2)
5. **No Exchange Online detection** - Assumes Office 365 (Phase 4)

---

## Phase 2 Preview

**Scope:** Advanced Outlook features + external domain rollout
- Read receipts (`isReadReceiptRequested: true`)
- Delivery receipts (`isDeliveryReceiptRequested: true`)
- Importance flags (low, normal, high)
- Categories (labels/tags)
- External domain validation (SPF/DKIM checks)
- Batch send API (up to 20 messages per request)

---

## References

- **Gmail Integration (Sprint 53/54):** `docs/specs/GMAIL-RICH-EMAIL-SPEC.md`
- **Microsoft Graph API:** https://learn.microsoft.com/en-us/graph/api/user-sendmail
- **Azure AD OAuth:** https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow
- **Rollout Controller:** `scripts/rollout_controller.py`
- **Telemetry Patterns:** `src/telemetry/prom.py`
