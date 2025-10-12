# Sprint 54 Plan: Gmail Rich Email & Studio Connect UX (Phase C)

**Sprint:** 54 (Phase C)
**Date:** October 8, 2025
**Duration:** 10–12 working days
**Status:** Planning
**Depends On:** Sprint 53 Phase B (merged to main, flag OFF)

---

## Mission

Extend Gmail integration with HTML email body support, file attachments (regular + inline CID), and Studio "Connect Google" UX. Maintain feature-flagged architecture with safe rollout, comprehensive testing, and instant rollback capability.

**Guiding Principles:**
- **Robustness > Speed**: Validate all inputs, bound all resources
- **Privacy First**: Never log raw HTML/attachment bytes
- **Safe Rollout**: Shadow mode → canary → full production
- **Testability**: Unit + integration + E2E coverage

---

## Scope

### In Scope

#### 1. HTML Email Body
- Support HTML body parameter (`html` field in `gmail.send` params)
- Safe HTML subset (no `<script>`, `<iframe>`, `<object>`, external CSS)
- Sanitization via `bleach` library (allowlist-based)
- Multipart/alternative MIME (text fallback + HTML)
- Character encoding: UTF-8 only

#### 2. File Attachments
- **Regular attachments**: `attachments[]` array
  - Fields: `filename`, `content_type`, `data` (base64-encoded)
  - Max size: 25MB per attachment
  - Max count: 10 attachments per email
  - Allowed MIME types: PDF, images (PNG/JPG/GIF), Office docs, text files
  - Blocked types: executables (.exe, .bat, .sh, .ps1), archives (.zip, .rar)

- **Inline attachments**: `inline[]` array for images
  - Fields: `cid` (Content-ID), `filename`, `content_type`, `data`
  - Referenced in HTML via `<img src="cid:image1">`
  - Max size: 5MB per inline image
  - Max count: 20 inline images per email

#### 3. Studio "Connect Google" UX
- **Screens:**
  - Disconnected state with "Connect Google" CTA
  - OAuth consent flow (PKCE)
  - Connected state with account info + "Disconnect" button
  - Token refresh warning (when <120s until expiry)
  - Revoke flow with confirmation dialog

- **Features:**
  - Display connected Gmail address
  - Show OAuth scopes granted
  - Deep link to `/oauth/google/status` API for debugging
  - Error states: missing credentials, token expired, rate limited

#### 4. Security & Validation
- **Request size limits:**
  - Total payload: 50MB max (Gmail API limit)
  - Individual attachment: 25MB max
  - Inline image: 5MB max
  - HTML body: 5MB max

- **Content sanitization:**
  - HTML allowlist: `<p>`, `<div>`, `<span>`, `<a>`, `<img>`, `<table>`, `<tr>`, `<td>`, `<h1>`-`<h6>`, `<ul>`, `<ol>`, `<li>`, `<strong>`, `<em>`, `<br>`
  - Strip: `<script>`, `<iframe>`, `<object>`, `<embed>`, `<form>`, `<input>`
  - Remove: `onclick`, `onerror`, `onload` attributes
  - External CSS: blocked (inline styles allowed with strict parser)

- **Privacy:**
  - Never log raw HTML or attachment bytes
  - Audit logs: SHA256 digest + first 64 bytes only
  - Redact email addresses in non-prod logs

#### 5. OAuth Scope Review
- **Current scope:** `https://www.googleapis.com/auth/gmail.send`
- **Phase C scope:** Same (no additional scopes needed)
- **Future scopes** (not in Sprint 54):
  - `gmail.readonly` for inbox integration (Sprint 55+)
  - `gmail.labels` for folder management (Sprint 56+)

### Out of Scope (Future Sprints)

- Custom "From" address (requires domain verification)
- Scheduled sending (requires queue infrastructure)
- Email templates library (Sprint 55)
- Inbox read/reply actions (Sprint 56)
- Calendar integration (Sprint 57)

---

## Architecture

### 1. MIME Builder Module

**File:** `src/actions/adapters/google_mime.py`

**Responsibilities:**
- Build multipart/mixed MIME messages
- Support text-only, HTML-only, multipart/alternative (text + HTML)
- Attach regular files with proper Content-Disposition
- Attach inline images with Content-ID references
- Base64URL encoding (no padding)

**API Surface:**
```python
class MIMEBuilder:
    def build_text_email(to: str, subject: str, text: str) -> str
    def build_html_email(to: str, subject: str, text: str, html: str) -> str
    def build_email_with_attachments(to: str, subject: str, body: str, attachments: list) -> str
    def build_email_with_inline_images(to: str, subject: str, html: str, inline: list) -> str
    def build_full_email(to: str, subject: str, text: str, html: str, attachments: list, inline: list) -> str
```

**Performance Target:**
- Build time: <50ms p99 for 2MB total payload
- Memory ceiling: 100MB per request (stream large attachments)

### 2. Attachment Storage Strategy

**Option A: Direct Upload to Backend (Recommended)**
- Studio POSTs attachments as multipart/form-data to `/actions/preview`
- Backend validates, sanitizes, stores in memory during preview
- Execute uses cached attachments from preview_id
- **Pros:** Simple, no external storage dependency, ephemeral (10-min TTL)
- **Cons:** 50MB request size limit (acceptable for Gmail)

**Option B: Presigned Upload to S3/R2**
- Studio gets presigned URL from backend
- Uploads directly to object storage
- Backend fetches from storage during execute
- **Pros:** Scales to larger files, offloads bandwidth
- **Cons:** Adds complexity, requires S3/R2 setup, cleanup job needed

**Decision:** Use **Option A** for Sprint 54 (simpler, meets 50MB Gmail limit)

### 3. Studio Upload Flow

**Flow:**
1. User selects files in Studio (drag & drop or file picker)
2. Studio validates: file size, count, MIME type
3. Studio base64-encodes files client-side
4. Studio POSTs to `/actions/preview` with `attachments[]` array
5. Backend validates, generates preview_id, caches for 10 minutes
6. User confirms preview
7. Studio POSTs to `/actions/execute` with preview_id
8. Backend retrieves cached attachments, builds MIME, sends via Gmail API

**Trade-offs:**
- **Memory:** Attachments cached in Redis (with 10-min TTL)
- **Security:** Backend validates MIME type, size, content (virus scan stub)
- **UX:** Fast preview (<1s), no presigned URL complexity

### 4. Feature Flags

**New Flags:**
- `PROVIDER_GOOGLE_RICH_EMAIL_ENABLED` (default: false)
  - Gates HTML body + attachments in execute
  - Preview always shows warnings if disabled

- `ATTACHMENTS_ENABLED` (default: false)
  - Independent toggle for attachments (can enable HTML without attachments)

**Flag Matrix:**

| RICH_EMAIL | ATTACHMENTS | Behavior |
|------------|-------------|----------|
| false | false | Text-only emails (Sprint 53 behavior) |
| true | false | HTML body only, no attachments |
| true | true | HTML + attachments + inline images |
| false | true | ERROR (attachments require rich email flag) |

---

## Data Model Impacts

**No database changes required.**

Attachments are ephemeral (cached in Redis during preview, discarded after execute). No persistent storage needed.

**Redis Keys:**
- `preview:{preview_id}:attachments` - Cached attachment data (10-min TTL)
- `preview:{preview_id}:inline` - Cached inline images (10-min TTL)

---

## UX Flows

### Happy Path: Send HTML Email with Attachment

1. Studio: User clicks "Connect Google" → OAuth consent flow → tokens stored
2. Studio: User composes email with HTML body + attaches PDF
3. Studio: POSTs to `/actions/preview`
4. Backend: Validates, builds MIME preview, returns `preview_id`
5. Studio: Shows preview with file list
6. User: Clicks "Send"
7. Studio: POSTs to `/actions/execute` with `preview_id`
8. Backend: Retrieves attachments from cache, sends via Gmail API
9. Studio: Shows success toast with message_id

### Error Flow: Attachment Too Large

1. Studio: User attaches 30MB file
2. Studio: Client-side validation fails → shows error: "File too large (max 25MB)"
3. User: Removes file or compresses it
4. Flow continues normally

### Error Flow: Missing OAuth

1. Studio: User tries to send email without connecting Google
2. Studio: Checks `/oauth/google/status` → returns `linked: false`
3. Studio: Shows "Connect Google" modal
4. User: Completes OAuth flow
5. Flow continues normally

### Error Flow: Token Refresh Needed

1. Backend: Token expires during send
2. Backend: Auto-refresh triggers (Redis lock prevents stampede)
3. Backend: Refreshed token used for Gmail API call
4. User: Sees no interruption (seamless)

### Error Flow: Gmail API Rate Limit

1. Backend: Gmail API returns 429 Too Many Requests
2. Backend: Records metric `gmail_send_errors_total{reason="rate_limited"}`
3. Backend: Returns 429 to Studio with Retry-After header
4. Studio: Shows error: "Gmail rate limit reached. Try again in 60 seconds."
5. User: Waits and retries

---

## Rollout Strategy

### Phase 1: Shadow Mode (Days 1-3)
- Deploy code with flags OFF
- Monitor baseline metrics (no behavior change)
- Run integration tests in staging environment
- Verify no regressions in plain-text email flow

### Phase 2: Internal Canary (Days 4-6)
- Enable `PROVIDER_GOOGLE_RICH_EMAIL_ENABLED=true` for 1 test workspace
- Send test emails (HTML + attachments) to internal team
- Monitor:
  - `gmail_mime_build_seconds` (p95 < 50ms)
  - `gmail_attachment_bytes_total` (no spikes)
  - `gmail_send_errors_total{reason="attachment_*"}` (should be 0)
- Collect feedback on Studio UX

### Phase 3: Limited Beta (Days 7-9)
- Enable for 5-10 beta workspaces (opt-in)
- Monitor for 48 hours:
  - Error rates < 1%
  - Latency p99 < 2s
  - No Gmail API quota exceeded errors
- Gather UX feedback and iterate

### Phase 4: Full Rollout (Days 10-12)
- Enable `PROVIDER_GOOGLE_RICH_EMAIL_ENABLED=true` globally
- Monitor for 24 hours:
  - All golden signals within SLO
  - No unusual error patterns
  - User adoption rate (% emails using HTML/attachments)
- Document lessons learned

### Rollback Steps (Instant)

**Option 1: Disable Rich Email Flag**
```bash
railway variables set PROVIDER_GOOGLE_RICH_EMAIL_ENABLED=false
```
Effect: Reverts to text-only emails, no data loss

**Option 2: Disable Attachments Only**
```bash
railway variables set ATTACHMENTS_ENABLED=false
```
Effect: HTML still works, attachments rejected

**Option 3: Full Rollback (Code Revert)**
```bash
git revert <sprint-54-commit-sha>
git push origin main
railway deploy
```
Effect: Removes all Phase C code

---

## Risks & Mitigations

### Risk 1: Token Scope Creep
**Risk:** Users might expect additional Gmail features (read inbox, labels)
**Impact:** Medium (feature requests)
**Mitigation:**
- Document scope clearly in UX ("Send only")
- Add tooltip: "We can only send emails. Reading inbox requires additional permissions."
- Plan Sprint 55 for inbox read if demand is high

### Risk 2: Oversize Payloads
**Risk:** Users attach 50MB+ files, overwhelming backend
**Impact:** High (memory exhaustion, crashes)
**Mitigation:**
- Client-side validation in Studio (reject before upload)
- Backend validation in preview endpoint (400 Bad Request)
- Rate limiting on /actions endpoints (100 req/min per workspace)
- Memory monitoring alerts (> 80% usage triggers warning)

### Risk 3: Gmail API Quotas
**Risk:** High volume users hit Gmail send quota (500/day for free, 2000/day for Workspace)
**Impact:** Medium (user frustration)
**Mitigation:**
- Display quota status in Studio (if available via API)
- Graceful error handling (429 → "Rate limit reached, try later")
- Document quota limits in help docs
- Offer batch sending as future feature (Sprint 55)

### Risk 4: Abuse Vectors
**Risk:** Users send spam or phishing emails via Gmail send
**Impact:** High (account suspension, reputation damage)
**Mitigation:**
- Rate limiting per workspace (100 emails/day initially)
- Content scanning hooks (stub in Sprint 54, implement in Sprint 55)
- Audit logging (who sent what, when, to whom)
- Abuse reporting mechanism (future)
- Gmail's built-in spam filters (inherited from Google)

### Risk 5: HTML Sanitization Bypass
**Risk:** Malicious HTML escapes sanitization, executes XSS
**Impact:** Critical (security vulnerability)
**Mitigation:**
- Use `bleach` library with strict allowlist
- Unit tests for known XSS vectors
- Security review before rollout
- CSP headers in Studio (prevent reflected XSS)
- Penetration testing post-rollout

---

## Timeline & Phase Gates

### Days 1-2: MIME Builder Implementation
- **Deliverables:**
  - `src/actions/adapters/google_mime.py` implemented
  - Unit tests (20+ tests covering all MIME variants)
  - Performance benchmarks (build time < 50ms)

- **Gate:**
  - All unit tests passing
  - No memory leaks in stress test (1000 emails)

### Days 3-4: API Extensions & Validation
- **Deliverables:**
  - Extend `gmail.send` schema for `html`, `attachments[]`, `inline[]`
  - Validation logic (size, count, MIME type checks)
  - Error taxonomy updates (new bounded reasons)

- **Gate:**
  - API schema documented
  - Validation tests passing (happy path + negatives)

### Days 5-6: Studio UX Implementation
- **Deliverables:**
  - "Connect Google" flow
  - File upload component (drag & drop)
  - Preview UI for attachments
  - Error states & loading spinners

- **Gate:**
  - UX review with design team
  - Accessibility audit (WCAG AA compliance)
  - Mobile responsive

### Days 7-8: Integration Testing
- **Deliverables:**
  - Integration tests (OAuth + send with attachments)
  - E2E smoke tests (Studio → Backend → Gmail)
  - Load testing (100 concurrent sends)

- **Gate:**
  - Integration tests passing
  - p99 latency < 2s under load
  - No Gmail API errors

### Days 9-10: Canary Rollout
- **Deliverables:**
  - Enable for internal test workspace
  - Send 50+ test emails (various HTML/attachment combos)
  - Monitor metrics for 48 hours

- **Gate:**
  - Error rate < 1%
  - No production incidents
  - Positive feedback from internal team

### Days 11-12: Documentation & Launch
- **Deliverables:**
  - Evidence docs (implementation summary, metrics, lessons learned)
  - User-facing help docs (how to use HTML/attachments)
  - Runbook for ops team (monitoring, troubleshooting)

- **Gate:**
  - All docs complete
  - Ops team trained on rollback procedure
  - Go/No-Go decision approved

---

## Definition of Done

### Code Quality
- [ ] All unit tests passing (100+ tests)
- [ ] Integration tests passing (10+ tests, quarantined with env gates)
- [ ] Linting clean (black + ruff)
- [ ] No hardcoded secrets or PII in logs
- [ ] Performance benchmarks met (p99 latency < 2s)

### Security
- [ ] HTML sanitization reviewed by security team
- [ ] Content scanning hooks implemented (stub)
- [ ] Rate limiting in place (100 emails/day per workspace)
- [ ] Audit logging complete (SHA256 digest, no raw bytes)

### Observability
- [ ] Metrics implemented (MIME build time, attachment bytes, error reasons)
- [ ] Dashboards created (Grafana panels)
- [ ] Alerts configured (error rate, latency, quota exceeded)
- [ ] Runbook documented (playbooks for common issues)

### UX
- [ ] Studio UX reviewed and approved
- [ ] Accessibility audit passed (WCAG AA)
- [ ] Mobile responsive
- [ ] Error messages clear and actionable

### Documentation
- [ ] API spec complete (`GMAIL-RICH-EMAIL-SPEC.md`)
- [ ] Studio UX flows documented (`STUDIO-GOOGLE-UX.md`)
- [ ] Evidence docs created (`PHASE-C-EVIDENCE.md`)
- [ ] User help docs published (how-to guides)

### Rollout
- [ ] Canary rollout successful (48 hours, no incidents)
- [ ] Beta feedback collected and addressed
- [ ] Go/No-Go decision approved by stakeholders
- [ ] Feature flags enabled globally (or reverted if issues)

---

## Success Metrics (SLOs)

### Availability
- **Target:** 99.5% uptime for Gmail send with attachments
- **Measurement:** `(successful_sends / total_attempts) >= 0.995`

### Latency
- **Target:** p95 < 1.5s, p99 < 2s
- **Measurement:** `histogram_quantile(0.99, gmail_send_duration_seconds) < 2.0`

### Error Rate
- **Target:** <1% overall error rate
- **Measurement:** `(gmail_send_errors_total / gmail_send_total) < 0.01`

### User Adoption
- **Target:** 20% of emails use HTML or attachments within 2 weeks
- **Measurement:** `(rich_emails / total_emails) >= 0.20`

---

## Open Questions

1. **Virus scanning:** Should we integrate ClamAV or external scanning service in Sprint 54, or stub and defer to Sprint 55?
   - **Recommendation:** Stub in 54, implement in 55 (adds 2-3 days if done now)

2. **Attachment caching:** Redis OK for 50MB payloads, or should we use S3/R2?
   - **Recommendation:** Redis for Sprint 54 (simpler), migrate to S3 in Sprint 55 if needed

3. **HTML editor:** Should Studio include a rich text editor (TinyMCE, Quill), or just textarea for now?
   - **Recommendation:** Textarea for Sprint 54 (faster), rich editor in Sprint 55

4. **Email templates:** Should we include pre-built templates (newsletter, invoice, etc.) in Sprint 54?
   - **Recommendation:** No templates in Sprint 54 (scope creep), add in Sprint 55

5. **Inline image limits:** 20 images seems high. Should we lower to 10?
   - **Recommendation:** Start with 10, increase if user feedback demands it

---

**Sprint 54 Plan Complete**
**Next Step:** Review plan with team, approve scope, then proceed to implementation.
