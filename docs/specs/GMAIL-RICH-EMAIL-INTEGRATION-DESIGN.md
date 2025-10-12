# Gmail Rich Email Integration - Design Document

**Date:** 2025-10-09
**Sprint:** 54 - Phase C Integration
**Status:** DESIGN PHASE

## 1. Integration Points

### 1.1 Function Signature

**MIME Builder (src/actions/adapters/google_mime.py):**
```python
class MimeBuilder:
    def build_message(
        self,
        to: str,
        subject: str,
        text: str,
        html: Optional[str] = None,
        cc: Optional[List[str]] = None,
        bcc: Optional[List[str]] = None,
        attachments: Optional[List[Attachment]] = None,
        inline: Optional[List[InlineImage]] = None,
    ) -> str:
        """Build RFC822 MIME message.

        Raises:
            ValueError: If validation fails (with structured error code)
        """
```

### 1.2 Integration in google.py

**Current implementation (lines 164-186):**
```python
def _build_mime_message(self, to, subject, text, cc, bcc) -> str:
    """Build RFC822 MIME message."""
    message = MIMEMultipart()
    message["To"] = to
    message["Subject"] = subject
    # ... uses email.mime.multipart
    return message.as_string()
```

**Replacement strategy:**
- **Line 164-186:** Replace `_build_mime_message()` implementation
- **Line 127-133:** Call from `_preview_gmail_send()`
- **Line 266-272:** Call from `_execute_gmail_send()`

**New signature:**
```python
def _build_mime_message(
    self,
    to: str,
    subject: str,
    text: str,
    cc: Optional[list[str]] = None,
    bcc: Optional[list[str]] = None,
    html: Optional[str] = None,
    attachments: Optional[list[dict]] = None,
    inline: Optional[list[dict]] = None,
) -> str:
    """Build RFC822 MIME message using MimeBuilder.

    Raises:
        ValueError: With structured error payload (see section 2)
    """
```

## 2. Structured Error Payload

### 2.1 Error Shape

All validation/sanitization errors follow this structure:

```python
{
    "error_code": str,  # From GMAIL-RICH-EMAIL-SPEC.md
    "message": str,     # Human-readable description
    "field": Optional[str],  # Which field failed (e.g., "attachments[0]")
    "details": dict,    # Additional context
    "remediation": str,  # How to fix
}
```

### 2.2 Error Code Taxonomy (from spec)

**Attachment Errors:**
- `validation_error_attachment_too_large` - File exceeds 25MB
- `validation_error_attachment_count_exceeded` - More than 10 attachments
- `validation_error_blocked_mime_type` - Executable or dangerous MIME type
- `validation_error_invalid_filename` - Filename too long or invalid
- `validation_error_total_size_exceeded` - Total payload > 50MB

**Inline Image Errors:**
- `validation_error_inline_too_large` - Image exceeds 5MB
- `validation_error_inline_count_exceeded` - More than 20 inline images
- `validation_error_invalid_cid` - CID empty or too long
- `validation_error_duplicate_cid` - Duplicate CID values
- `validation_error_missing_inline_image` - HTML references CID not provided
- `validation_error_cid_not_referenced` - Inline image CID not used in HTML

**HTML Errors:**
- `validation_error_html_too_large` - HTML body exceeds limits
- `sanitization_warning_tags_removed` - Dangerous tags stripped
- `sanitization_warning_scripts_blocked` - javascript: protocol blocked

### 2.3 Error Mapping Examples

```python
# Example 1: Oversized attachment
{
    "error_code": "validation_error_attachment_too_large",
    "message": "Attachment 'report.pdf' exceeds 25MB limit",
    "field": "attachments[0]",
    "details": {
        "filename": "report.pdf",
        "size_bytes": 27262976,
        "limit_bytes": 26214400
    },
    "remediation": "Reduce attachment size to under 25MB or use a file-sharing link"
}

# Example 2: CID mismatch
{
    "error_code": "validation_error_missing_inline_image",
    "message": "HTML references CID 'logo' but no inline image provided",
    "field": "inline",
    "details": {
        "referenced_cids": ["logo", "banner"],
        "provided_cids": ["banner"]
    },
    "remediation": "Add inline image with cid='logo' or remove <img src='cid:logo'> from HTML"
}

# Example 3: Blocked MIME type
{
    "error_code": "validation_error_blocked_mime_type",
    "message": "Attachment type 'application/x-msdownload' (.exe) is not allowed",
    "field": "attachments[2]",
    "details": {
        "filename": "installer.exe",
        "content_type": "application/x-msdownload",
        "blocked_types": ["application/x-msdownload", "application/zip", "..."]
    },
    "remediation": "Remove executable file or convert to allowed format (PDF, DOCX, etc.)"
}
```

### 2.4 User-Facing vs. Internal Logging

**User-facing (Studio UI):**
- `error_code` → Icon/color (red for error, yellow for warning)
- `message` → Displayed prominently
- `remediation` → Shown as help text or tooltip

**Internal logs:**
- Full payload logged with `details` for debugging
- Metrics: `action_error_total{provider="google", action="gmail.send", reason=<error_code>}`

## 3. Flag Threading

### 3.1 Three Guards

**Guard 1: Provider Enabled (line 226)**
```python
if not self.enabled:  # PROVIDER_GOOGLE_ENABLED=false
    record_action_error(provider="google", action="gmail.send", reason="provider_disabled")
    raise ValueError("Google provider is disabled")
```

**Guard 2: Rollout Gate (line 231-235)**
```python
if self.rollout_gate is not None:
    context = {"actor_id": actor_id, "workspace_id": workspace_id}
    if not self.rollout_gate.allow("google", context):
        record_action_error(provider="google", action="gmail.send", reason="rollout_gated")
        raise ValueError("Gmail send not rolled out to this user")
```

**Guard 3: internal_only Check (NEW)**
```python
# After rollout gate check (line 236)
internal_only = os.getenv("GOOGLE_INTERNAL_ONLY", "true").lower() == "true"
if internal_only and not self._is_internal_user(actor_id):
    record_action_error(provider="google", action="gmail.send", reason="internal_only")
    raise ValueError("Gmail send only available to internal users during beta")
```

### 3.2 Internal User Detection

```python
def _is_internal_user(self, actor_id: str) -> bool:
    """Check if actor is internal (based on email domain)."""
    # Simplest: whitelist of internal domains
    internal_domains = os.getenv("INTERNAL_EMAIL_DOMAINS", "").split(",")
    if not internal_domains:
        return False  # No domains configured = no internal users

    # Check if actor_id (email) ends with internal domain
    return any(actor_id.endswith(f"@{domain}") for domain in internal_domains)
```

### 3.3 Flag Precedence

```
PROVIDER_GOOGLE_ENABLED=false → Always blocks (override all)
    ↓
GOOGLE_INTERNAL_ONLY=true → Blocks external users
    ↓
rollout_gate.allow() → Gradual rollout (0-100%)
    ↓
Validation → Rich email validation
    ↓
Execution → Gmail API call
```

## 4. Fallback Behavior

### 4.1 Rich Email Failure Strategy

**Question:** If MIME build fails (validation error), should we:
- **Option A:** Return error immediately (fail-fast)
- **Option B:** Fall back to text-only and send anyway

**Recommendation:** **Option A (fail-fast)** for validation errors

**Rationale:**
- Validation errors indicate user misconfiguration (e.g., oversized file)
- Silently stripping attachments would be confusing
- User needs to fix the issue (e.g., reduce file size)
- HTML sanitization already happens transparently (remove dangerous tags, keep safe content)

**Implementation:**
```python
try:
    mime_message = self._build_mime_message(...)
except ValueError as e:
    # Parse structured error from exception message
    if "validation_error_" in str(e):
        # Extract error payload and return to user
        record_action_error(provider="google", action="gmail.send", reason="validation_error")
        raise  # Re-raise with structured payload
    else:
        # Unknown error, log and fail
        raise
```

### 4.2 HTML Sanitization (Non-Blocking)

HTML sanitization is **transparent** - dangerous content is removed, safe content is kept:
- `<script>` tags → Stripped silently
- `onclick` handlers → Stripped silently
- Safe HTML → Preserved

**Metrics emitted:**
- `gmail_html_sanitization_changes_total{change_type="tag_removed"}`
- `gmail_html_sanitization_changes_total{change_type="script_blocked"}`

## 5. Parameter Schema Extension

### 5.1 Current GmailSendParams

```python
class GmailSendParams(BaseModel):
    to: str
    subject: str
    text: str
    cc: Optional[list[str]] = None
    bcc: Optional[list[str]] = None
```

### 5.2 Extended Schema (NEW)

```python
class GmailSendParams(BaseModel):
    to: str
    subject: str
    text: str
    html: Optional[str] = None  # NEW: HTML body
    cc: Optional[list[str]] = None
    bcc: Optional[list[str]] = None
    attachments: Optional[list[AttachmentInput]] = None  # NEW
    inline: Optional[list[InlineImageInput]] = None  # NEW

class AttachmentInput(BaseModel):
    """Attachment input (before validation)."""
    filename: str
    content_type: str
    data: str  # Base64-encoded

class InlineImageInput(BaseModel):
    """Inline image input (before validation)."""
    cid: str
    filename: str
    content_type: str
    data: str  # Base64-encoded
```

### 5.3 Conversion to Internal Types

```python
# In _build_mime_message()
attachments_validated = None
if attachments:
    attachments_validated = [
        Attachment(
            filename=att.filename,
            content_type=att.content_type,
            data=base64.b64decode(att.data)  # Decode from base64
        )
        for att in attachments
    ]

inline_validated = None
if inline:
    inline_validated = [
        InlineImage(
            cid=img.cid,
            filename=img.filename,
            content_type=img.content_type,
            data=base64.b64decode(img.data)
        )
        for img in inline
    ]
```

## 6. E2E Test Credentials Setup

### 6.1 GCP Project

**Option:** Use existing GCP project (already has OAuth configured from Sprint 53)

**Required:**
- OAuth Client ID: `GOOGLE_CLIENT_ID`
- OAuth Client Secret: `GOOGLE_CLIENT_SECRET`
- OAuth Scopes: `https://www.googleapis.com/auth/gmail.send`

### 6.2 Test Account

**Create dedicated test account:**
- Email: `relay-test@<your-domain>.com` (or Gmail address)
- Purpose: Receive test emails, verify MIME structure
- Tokens stored in database via existing OAuth flow

### 6.3 Credential Storage

**Environment variables (already in use):**
```bash
GOOGLE_CLIENT_ID=<oauth-client-id>
GOOGLE_CLIENT_SECRET=<oauth-client-secret>
PROVIDER_GOOGLE_ENABLED=true
GOOGLE_INTERNAL_ONLY=true
INTERNAL_EMAIL_DOMAINS=<your-domain>.com
```

**Token storage:** Database (existing `oauth_tokens` table from Sprint 53)

## 7. Performance Baseline

### 7.1 Target End-to-End Latency

**Components:**
- MIME build time: < 250ms (P95 for 1MB)
- Gmail API call: ~500-1000ms (network + processing)
- **Total E2E: < 2 seconds for 1MB payload**

### 7.2 Breakdown

```
User submits action
  ↓ 10-50ms: Parameter validation
  ↓ 10-100ms: OAuth token fetch (cached)
  ↓ 50-250ms: MIME build (HTML sanitization + validation)
  ↓ 500-1000ms: Gmail API call
  ↓ 10ms: Response processing
= 580-1410ms total (well under 2s target)
```

### 7.3 Monitoring

**Metrics to track:**
- `action_latency_seconds{provider="google", action="gmail.send"}` - Total E2E
- `gmail_mime_build_seconds` - MIME build only
- `external_api_duration_seconds{service="gmail", operation="send"}` - Gmail API only

**Alert if:** P95 total latency > 2 seconds

## 8. Implementation Checklist

- [ ] Extend `GmailSendParams` with `html`, `attachments`, `inline`
- [ ] Add `AttachmentInput` and `InlineImageInput` Pydantic models
- [ ] Add `_is_internal_user()` helper
- [ ] Add `GOOGLE_INTERNAL_ONLY` guard in `_execute_gmail_send()`
- [ ] Replace `_build_mime_message()` to use `MimeBuilder`
- [ ] Add structured error payload extraction
- [ ] Update `list_actions()` schema to include new fields
- [ ] Add unit test for structured error payload
- [ ] Update `_preview_gmail_send()` to support rich email
- [ ] Add metrics tracking for MIME build errors

## 9. Rollback Plan

### 9.1 Rollback Triggers

**Automatic (via controller):**
- P95 latency > 500ms for 10 minutes
- Error rate > 5% for 10 minutes
- OAuth refresh failures > 10 in 15 minutes

**Manual:**
- Set `flags:google:rollout_percent=0` in Redis
- OR set `PROVIDER_GOOGLE_ENABLED=false`

### 9.2 Rollback Test

```bash
# Set rollout to 0%
redis-cli SET flags:google:rollout_percent 0

# Verify no new sends use rich email
# (existing sends in-flight may complete)

# Confirm metric stops incrementing
curl http://localhost:9090/api/v1/query?query=gmail_mime_build_seconds_count

# Restore
redis-cli SET flags:google:rollout_percent 10
```

### 9.3 Partial Rollback

If only rich email features are broken (not OAuth):
- Keep provider enabled
- Fall back to text-only by wrapping MIME build in try/catch:

```python
try:
    mime_message = self._build_mime_message_rich(...)
except Exception as e:
    # Log error, fall back to text-only
    mime_message = self._build_mime_message_simple(to, subject, text, cc, bcc)
```

**Decision:** Implement if needed post-launch (not in initial version)

---

## 10. Next Steps

1. **Get approval on this design**
2. **Implement integration** (modify google.py)
3. **Add unit test** for structured error payload
4. **Run E2E tests** against real Gmail
5. **Deploy observability** (Prometheus rules + Grafana dashboard)
6. **Enable rollout controller** (not dry-run)

**Questions for review:**
- Approve fallback strategy (fail-fast for validation errors)?
- Approve internal_only logic (email domain check)?
- Approve error payload structure?
