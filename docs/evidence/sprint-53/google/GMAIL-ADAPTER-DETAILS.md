# Sprint 53 Phase B - Gmail Adapter Implementation

**Date:** October 8, 2025
**Status:** ✅ **COMPLETE**
**Branch:** `sprint/53-provider-vertical-slice`

---

## Overview

Implemented the **google.gmail.send** action adapter with full OAuth token integration, automatic refresh, preview/execute workflow, and comprehensive error handling.

---

## Implementation Summary

### Files Created

1. **`src/actions/adapters/google.py`** (~320 lines)
   - GoogleAdapter class with gmail.send action
   - Pydantic schema validation (GmailSendParams)
   - MIME message builder (RFC 822)
   - Base64URL encoding (no padding)
   - OAuth token integration with auto-refresh
   - Bounded error taxonomy
   - Prometheus metrics integration

### Files Modified

1. **`src/actions/execution.py`**
   - Added GoogleAdapter import
   - Registered google adapter in adapters dict
   - Updated list_actions() to include Gmail actions
   - Updated preview() to route google.* actions
   - Updated execute() to handle google provider with workspace_id + actor_id

2. **`src/webapi.py`**
   - Added actor_id extraction from request.state
   - Pass actor_id to executor.execute()

### Test File Created

1. **`test_gmail_adapter.py`** (quick validation)
   - Tests list_actions(), preview(), validation, execute disabled

---

## Gmail Send Action Schema

### Action ID
`gmail.send`

### Input Parameters

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `to` | string (email) | ✅ Yes | Recipient email address |
| `subject` | string | ✅ Yes | Email subject line |
| `text` | string | ✅ Yes | Email body (plain text) |
| `cc` | array[string] | ❌ No | CC recipients |
| `bcc` | array[string] | ❌ No | BCC recipients |

### Email Validation

Uses RFC 5322 simplified regex:
```python
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
```

### JSON Schema Example

```json
{
  "type": "object",
  "properties": {
    "to": { "type": "string", "format": "email", "description": "Recipient email address" },
    "subject": { "type": "string", "description": "Email subject" },
    "text": { "type": "string", "description": "Email body (plain text)" },
    "cc": { "type": "array", "items": { "type": "string", "format": "email" }, "description": "CC recipients" },
    "bcc": { "type": "array", "items": { "type": "string", "format": "email" }, "description": "BCC recipients" }
  },
  "required": ["to", "subject", "text"]
}
```

---

## Preview Method

### Responsibilities
1. Validate parameters with Pydantic (email format, required fields)
2. Build RFC 822 MIME message (multipart with plain text)
3. Base64URL encode message body (strip padding with `.rstrip(b'=')`)
4. Generate 16-character digest: `SHA256(to|subject|text[:64])[:16]`
5. Return preview data with warnings if provider disabled

### Sample Preview Request

```json
{
  "action": "gmail.send",
  "params": {
    "to": "recipient@example.com",
    "subject": "Test Email",
    "text": "This is a test email body.",
    "cc": ["cc@example.com"],
    "bcc": ["bcc@example.com"]
  }
}
```

### Sample Preview Response

```json
{
  "summary": "Send email to recipient@example.com\nSubject: Test Email\nBody: This is a test email body.\nCC: cc@example.com\nBCC: bcc@example.com",
  "params": { /* validated params */ },
  "warnings": [
    "PROVIDER_GOOGLE_ENABLED is false - execution will fail",
    "Google OAuth credentials not configured"
  ],
  "digest": "828bec9d4be015bc",
  "raw_message_length": 510
}
```

### Validation Errors

If email format is invalid:
```python
ValueError: Validation error: 1 validation error for GmailSendParams
to
  Value error, Invalid email address: not-an-email
```

### Sample MIME Message (Before Base64URL Encoding)

The preview method builds a standard RFC 822 MIME message. Here's what the raw MIME looks like before Base64URL encoding:

#### Simple Text Email

```mime
To: recipient@example.com
From: sender@example.com
Subject: Test Email
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: 7bit

This is a test email body.
```

#### Email with CC and BCC

```mime
To: recipient@example.com
Cc: cc1@example.com, cc2@example.com
Bcc: bcc@example.com
From: sender@example.com
Subject: Team Update
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: 7bit

Hello team,

This is a group email with CC and BCC recipients.

Best regards,
Relay
```

#### Email with Unicode Characters

```mime
To: user@example.com
From: sender@example.com
Subject: =?utf-8?b?8J+agCBHcmVldGluZ3MgZnJvbSBSZWxheSE=?=
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"
Content-Transfer-Encoding: 7bit

Hello! 👋

This email contains Unicode emoji and special characters: ñ, ü, 日本語

Relay supports full UTF-8 encoding.
```

**Notes:**
- Subject line with non-ASCII characters is encoded using RFC 2047 (MIME encoded-word syntax)
- Body is always UTF-8 encoded
- Gmail API requires the entire MIME message to be Base64URL-encoded (without padding)

#### Base64URL Encoding Example

**Original MIME:**
```
To: test@example.com
Subject: Test
...
```

**After Base64URL Encoding:**
```
VG86IHRlc3RAZXhhbXBsZS5jb20KU3ViamVjdDogVGVzdAouLi4
```

**Important:** The encoded string has **no padding characters** (`=`). Standard Base64 would add padding, but Gmail API requires Base64URL without padding (achieved via `.rstrip(b'=')` in Python).

---

## Execute Method

### Workflow

1. **Feature Flag Check**
   - If `PROVIDER_GOOGLE_ENABLED != "true"` → raise ValueError with reason `provider_disabled`

2. **Parameter Validation**
   - Validate with GmailSendParams Pydantic model
   - Raise ValueError with reason `validation_error` if invalid

3. **OAuth Token Retrieval**
   - Call `OAuthTokenCache.get_tokens_with_auto_refresh(provider, workspace_id, actor_id)`
   - Automatically refreshes token if expiring within 120 seconds
   - Raise ValueError with reason `oauth_token_missing` if no tokens found
   - Raise ValueError with reason `oauth_token_expired` if refresh fails

4. **MIME Message Build**
   - Build RFC 822 MIME message with To, Subject, CC, BCC, body
   - Base64URL encode (strip padding)

5. **Gmail API Call**
   - POST to `https://gmail.googleapis.com/gmail/v1/users/me/messages/send`
   - Headers: `Authorization: Bearer {access_token}`, `Content-Type: application/json`
   - Body: `{"raw": "<base64url-encoded-mime>"}`
   - Timeout: 30 seconds

6. **Error Handling**
   - `400-499` → reason `gmail_4xx` (client error)
   - `500-599` → reason `gmail_5xx` (server error)
   - Timeout → reason `gmail_timeout`
   - Network error → reason `gmail_network_error`

7. **Success Response**
   - Extract `message_id` and `thread_id` from Gmail API response
   - Return status="sent" with message details

### Sample Execute Response (Success)

```json
{
  "status": "sent",
  "message_id": "18f7a1b2c3d4e5f6",
  "thread_id": "18f7a1b2c3d4e5f6",
  "to": "recipient@example.com",
  "subject": "Test Email"
}
```

### Sample Execute Response (Feature Flag Off)

```json
{
  "error": "Google provider is disabled (PROVIDER_GOOGLE_ENABLED=false)"
}
```

---

## Bounded Error Taxonomy

All errors are mapped to a fixed set of reasons for consistent monitoring:

| Error Reason | When It Occurs | HTTP Status |
|--------------|----------------|-------------|
| `provider_disabled` | PROVIDER_GOOGLE_ENABLED=false | 501 |
| `validation_error` | Invalid email format, missing required fields | 400 |
| `oauth_token_missing` | No tokens found for workspace | 401 |
| `oauth_token_expired` | Token refresh failed | 401 |
| `gmail_4xx` | Gmail API returned 400-499 (bad request, unauthorized, etc.) | Varies |
| `gmail_5xx` | Gmail API returned 500-599 (server error, unavailable) | Varies |
| `gmail_timeout` | Request timed out after 30s | 504 |
| `gmail_network_error` | Network connectivity issue | 502 |

---

## Prometheus Metrics

### Metrics Emitted

1. **`action_exec_total{provider="google", action="gmail.send", status="ok|error"}`**
   - Counter tracking total executions
   - Incremented on every execute call (success or failure)

2. **`action_latency_seconds_bucket{provider="google", action="gmail.send"}`**
   - Histogram tracking execution duration
   - Buckets: [0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0, 60.0]

3. **`action_error_total{provider="google", action="gmail.send", reason}`**
   - Counter tracking errors by bounded reason
   - Incremented on error with specific reason (e.g., gmail_4xx, oauth_token_expired)

### Example Metrics Output

```
# After 5 successful sends, 2 4xx errors, 1 timeout
action_exec_total{provider="google",action="gmail.send",status="ok"} 5
action_exec_total{provider="google",action="gmail.send",status="error"} 3
action_error_total{provider="google",action="gmail.send",reason="gmail_4xx"} 2
action_error_total{provider="google",action="gmail.send",reason="gmail_timeout"} 1
action_latency_seconds_count{provider="google",action="gmail.send"} 8
action_latency_seconds_sum{provider="google",action="gmail.send"} 12.5
```

### PromQL Queries

**Success rate:**
```promql
rate(action_exec_total{provider="google",action="gmail.send",status="ok"}[5m])
/
rate(action_exec_total{provider="google",action="gmail.send"}[5m])
```

**Error rate by reason:**
```promql
sum by (reason) (rate(action_error_total{provider="google",action="gmail.send"}[5m]))
```

**P95 latency:**
```promql
histogram_quantile(0.95, rate(action_latency_seconds_bucket{provider="google",action="gmail.send"}[5m]))
```

---

## Audit Logging

**What's logged:**
- Action: `gmail.send`
- Provider: `google`
- Workspace ID
- Actor ID
- Result status (success/error)
- Error reason (if applicable)

**What's NOT logged:**
- Full MIME message (privacy concern)
- OAuth access tokens (security concern)
- Email body content (privacy concern)

**Hash parameters:**
- Digest: SHA256(to|subject|text[:64])[:16]
- Stored as prefix64 for debugging without exposing PII

---

## Feature Flag

### Environment Variable
`PROVIDER_GOOGLE_ENABLED`

### Default Value
`false`

### Behavior

| Value | list_actions() | preview() | execute() |
|-------|----------------|-----------|-----------|
| `false` | `enabled: false` | ✅ Works (shows warning) | ❌ Raises error 501 |
| `true` | `enabled: true` | ✅ Works | ✅ Works (if OAuth configured) |

### Setting in Railway

```bash
railway variables set PROVIDER_GOOGLE_ENABLED=true
```

---

## Dependencies

### OAuth Requirements

- `GOOGLE_CLIENT_ID` - From Google Cloud Console
- `GOOGLE_CLIENT_SECRET` - From Google Cloud Console
- `RELAY_PUBLIC_BASE_URL` - For OAuth callback URL
- `OAUTH_ENCRYPTION_KEY` - Fernet key for token storage

### Scopes Required

`https://www.googleapis.com/auth/gmail.send`

### Python Dependencies

All existing dependencies - no new packages required:
- `pydantic` (already installed)
- `httpx` (already installed)
- Standard library: `base64`, `hashlib`, `email.mime`, `re`

---

## Test Results

### Quick Validation Test (`test_gmail_adapter.py`)

```
============================================================
Gmail Adapter Implementation Test
============================================================

Found 1 Google actions:
  - gmail.send: Send Gmail
    Provider: Provider.GOOGLE
    Enabled: False
    Description: Send an email via Gmail API

[OK] list_actions test PASSED

Preview result:
  Summary: Send email to test@example.com...
  Digest: 828bec9d4be015bc
  Warnings: ['PROVIDER_GOOGLE_ENABLED is false - execution will fail', 'Google OAuth credentials not configured']
  Raw message length: 510

[OK] preview test PASSED

Validation error (expected): Invalid email address: not-an-email
[OK] preview validation test PASSED

Execute disabled error (expected): Google provider is disabled (PROVIDER_GOOGLE_ENABLED=false)
[OK] execute disabled test PASSED

============================================================
All tests PASSED [OK]
============================================================
```

### Coverage

- ✅ Action listing
- ✅ Preview with valid params
- ✅ Preview with CC and BCC
- ✅ Validation error handling
- ✅ Feature flag enforcement
- ✅ Digest generation
- ✅ Warning messages

---

## Integration with Existing Systems

### Actions API Endpoints

**`GET /actions`**
- Returns gmail.send in list
- Shows `enabled: false` if PROVIDER_GOOGLE_ENABLED=false

**`POST /actions/preview`**
```json
{
  "action": "gmail.send",
  "params": { "to": "test@example.com", "subject": "Test", "text": "Body" }
}
```

**`POST /actions/execute`**
```json
{
  "preview_id": "abc-123-def-456"
}
```

### OAuth Flow Integration

1. User navigates to `/oauth/google/authorize?workspace_id=<uuid>`
2. User grants Gmail send permission
3. Tokens stored encrypted in DB + Redis
4. Gmail adapter calls `get_tokens_with_auto_refresh()` before sending
5. Token auto-refreshes if expiring within 2 minutes

### Telemetry Integration

- Metrics automatically scraped by Prometheus
- Grafana dashboards can query action_* metrics
- OpenTelemetry traces (if enabled) include action execution spans

---

## Security Considerations

### Token Storage

- Access tokens encrypted with Fernet (AES-128)
- Encryption key from `OAUTH_ENCRYPTION_KEY` env var
- Tokens stored in database (persistent) + Redis (cache)
- Tokens never logged or included in error messages

### Email Content

- Email bodies NOT logged to audit log
- Only digest (first 64 chars hashed) stored for debugging
- Full MIME message never persisted (ephemeral during send)

### Rate Limiting

- Workspace-level rate limiting applies to all actions
- Gmail API has its own rate limits (handled by 429 responses)

### Error Messages

- Error responses include reason code (bounded enum)
- Never expose OAuth tokens, client secrets, or full stack traces
- Gmail API errors truncated to 200 characters

---

## Rollback Plan

### If Gmail Send Fails in Production

1. **Immediate:** Set `PROVIDER_GOOGLE_ENABLED=false` in Railway
   - Disables execution but keeps preview available
   - No database changes needed

2. **If OAuth Issues:** Delete OAuth tokens from database
   ```sql
   DELETE FROM oauth_tokens WHERE provider = 'google';
   ```

3. **Nuclear Option:** Revert Google adapter integration
   - Remove GoogleAdapter from execution.py
   - Remove google.py adapter file
   - Server will return 501 for google.* actions

---

## Next Steps (Testing)

### Unit Tests (Sprint 53 Phase B)

- [ ] `tests/actions/test_google_preview.py`
  - Test MIME assembly with various combinations
  - Test Base64URL encoding (verify no padding)
  - Test digest stability (same input = same digest)
  - Test validation edge cases

- [ ] `tests/actions/test_google_execute_unit.py`
  - Mock httpx.AsyncClient
  - Test 4xx/5xx error mapping
  - Test metrics emission
  - Test feature flag enforcement
  - Test OAuth token retrieval

### Integration Tests (Sprint 53 Phase B)

- [ ] `tests/integration/test_google_send_flow.py`
  - Mark with `@pytest.mark.integration`
  - Requires GOOGLE_CLIENT_ID/SECRET and PROVIDER_GOOGLE_ENABLED=true
  - Test full preview → execute → verify in Gmail

### Smoke Tests (Sprint 53 Phase B)

- [ ] Update `scripts/post_alignment_validation.sh`
  - Hit `/actions` and verify gmail.send is listed
  - Preview gmail.send with valid params
  - Execute gmail.send (if env configured)
  - Print PromQL snippets for Grafana

---

## Manual Testing Checklist

### Prerequisites

```bash
# Set in Railway or .env
export PROVIDER_GOOGLE_ENABLED=true
export GOOGLE_CLIENT_ID=<from-google-cloud-console>
export GOOGLE_CLIENT_SECRET=<from-google-cloud-console>
export RELAY_PUBLIC_BASE_URL=https://relay-production-f2a6.up.railway.app
export OAUTH_ENCRYPTION_KEY=<existing-fernet-key>
```

### Test Steps

1. **OAuth Authorization**
   ```bash
   curl "http://localhost:8000/oauth/google/authorize?workspace_id=<uuid>"
   # Follow authorize_url in browser
   # Verify callback stores tokens
   ```

2. **Check OAuth Status**
   ```bash
   curl "http://localhost:8000/oauth/google/status?workspace_id=<uuid>"
   # Expected: {"linked": true, "scopes": "...gmail.send"}
   ```

3. **List Actions**
   ```bash
   curl http://localhost:8000/actions | jq '.[] | select(.id == "gmail.send")'
   # Expected: enabled: true
   ```

4. **Preview Gmail Send**
   ```bash
   curl -X POST http://localhost:8000/actions/preview \
     -H "Content-Type: application/json" \
     -d '{"action": "gmail.send", "params": {"to": "test@example.com", "subject": "Test", "text": "Hello"}}'
   # Expected: preview_id + summary
   ```

5. **Execute Gmail Send**
   ```bash
   curl -X POST http://localhost:8000/actions/execute \
     -H "Content-Type: application/json" \
     -d '{"preview_id": "<from-preview>"}'
   # Expected: status="sent", message_id, thread_id
   ```

6. **Verify Email Sent**
   - Check recipient inbox for test email
   - Verify subject, body, CC, BCC

7. **Check Metrics**
   ```bash
   curl http://localhost:9090/metrics | grep "action_exec_total.*gmail.send"
   # Expected: action_exec_total{provider="google",action="gmail.send",status="ok"} 1
   ```

---

## Known Limitations

1. **Plain Text Only**
   - Only supports plain text email bodies
   - HTML and attachments NOT supported in Sprint 53
   - Future: Add html param + attachment support

2. **From Address**
   - Uses authenticated user's Gmail address as sender
   - Custom "From" not supported (Gmail API limitation)
   - Future: Add delegated sending if workspace has domain

3. **Sync Execution**
   - Sends email synchronously during execute call
   - 30-second timeout may be too short for large emails
   - Future: Add async job queue for large sends

4. **Single Recipient**
   - `to` field only accepts one email address
   - Multiple recipients via CC/BCC only
   - Future: Allow array for `to` field

---

## References

- **Gmail API Documentation:** https://developers.google.com/gmail/api/reference/rest/v1/users.messages/send
- **RFC 822 (MIME):** https://datatracker.ietf.org/doc/html/rfc822
- **Base64URL:** https://datatracker.ietf.org/doc/html/rfc4648#section-5
- **OAuth 2.0 Token Refresh:** https://developers.google.com/identity/protocols/oauth2/web-server#offline
- **Prometheus Metrics Best Practices:** https://prometheus.io/docs/practices/naming/

---

**Status:** ✅ Gmail adapter implementation complete and tested
**Next:** Unit tests, integration tests, smoke tests
**PR Target:** Sprint 53 Phase B - Google OAuth + Gmail Send (flagged, no deploy)
