# Gmail Rich Email Integration - Continuation Tasks

**Status:** IN PROGRESS
**Completed:** Parameter models, structured errors, internal-only checks, MIME builder integration

## Remaining Tasks

### 1. Update _preview_gmail_send() to handle new parameters

**Location:** src/actions/adapters/google.py line ~250

**Changes needed:**
```python
def _preview_gmail_send(self, params: dict[str, Any]) -> dict[str, Any]:
    # Validate with Pydantic
    validated = GmailSendParams(**params)

    # Add recipient count validation
    validated.validate_recipient_count()

    # Check internal-only recipients
    self._check_internal_only_recipients(validated.to, validated.cc, validated.bcc)

    # Build MIME message (NEW: returns tuple)
    mime_message, sanitization_summary = self._build_mime_message(
        to=validated.to,
        subject=validated.subject,
        text=validated.text,
        html=validated.html,  # NEW
        cc=validated.cc,
        bcc=validated.bcc,
        attachments=validated.attachments,  # NEW
        inline=validated.inline,  # NEW
    )

    # ... rest of preview logic ...

    result = {
        "summary": summary,
        "params": params,
        "warnings": warnings,
        "digest": digest,
        "raw_message_length": len(raw_message),
    }

    # Add sanitization summary if HTML was provided
    if sanitization_summary:
        result["sanitization_summary"] = sanitization_summary

    return result
```

### 2. Update _execute_gmail_send() to handle new parameters

**Location:** src/actions/adapters/google.py line ~396

**Changes needed:**
```python
async def _execute_gmail_send(self, params: dict[str, Any], workspace_id: str, actor_id: str):
    # ... existing guards ...

    # Validate parameters
    validated = GmailSendParams(**params)
    validated.validate_recipient_count()

    # Check internal-only recipients
    self._check_internal_only_recipients(validated.to, validated.cc, validated.bcc)

    # Fetch OAuth tokens ...

    # Build MIME message (NEW: handle tuple return + correlation_id)
    correlation_id = str(uuid.uuid4())
    try:
        mime_message, sanitization_summary = self._build_mime_message(
            to=validated.to,
            subject=validated.subject,
            text=validated.text,
            html=validated.html,  # NEW
            cc=validated.cc,
            bcc=validated.bcc,
            attachments=validated.attachments,  # NEW
            inline=validated.inline,  # NEW
        )
    except ValueError as e:
        # Log structured error with correlation_id
        error_payload = json.loads(str(e))
        error_payload["correlation_id"] = correlation_id

        record_action_error(provider="google", action="gmail.send", reason=error_payload["error_code"])
        duration = time.perf_counter() - start_time
        record_action_execution(provider="google", action="gmail.send", status="error", duration_seconds=duration)

        # Log for ops (include correlation_id)
        import logging
        logging.error(f"Gmail send failed: {error_payload}", extra={"correlation_id": correlation_id})

        raise ValueError(json.dumps(error_payload)) from e

    # ... rest of execution ...

    return {
        "status": "sent",
        "message_id": response_data.get("id"),
        "thread_id": response_data.get("threadId"),
        "to": validated.to,
        "subject": validated.subject,
        # NOTE: Don't expose correlation_id in API response (only in logs)
    }
```

### 3. Update list_actions() schema

**Location:** src/actions/adapters/google.py line ~186

**Add to schema:**
```python
"html": {
    "type": "string",
    "description": "HTML body (optional, will be sanitized)",
},
"attachments": {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "filename": {"type": "string"},
            "content_type": {"type": "string"},
            "data": {"type": "string", "description": "Base64-encoded"},
        },
        "required": ["filename", "content_type", "data"],
    },
    "description": "Attachments (max 10, 25MB each)",
},
"inline": {
    "type": "array",
    "items": {
        "type": "object",
        "properties": {
            "cid": {"type": "string"},
            "filename": {"type": "string"},
            "content_type": {"type": "string"},
            "data": {"type": "string", "description": "Base64-encoded"},
        },
        "required": ["cid", "filename", "content_type", "data"],
    },
    "description": "Inline images (max 20, 5MB each)",
},
```

### 4. Create unit test for structured error payload

**File:** tests/actions/test_google_adapter_errors.py (NEW)

**Test cases:**
1. `test_oversized_attachment_returns_structured_error`
2. `test_cid_mismatch_returns_structured_error`
3. `test_recipient_count_exceeded_returns_structured_error`
4. `test_internal_only_blocks_external_recipient`
5. `test_internal_only_allows_test_recipient`
6. `test_structured_error_has_all_fields`

**Example:**
```python
def test_oversized_attachment_returns_structured_error():
    adapter = GoogleAdapter()

    # Create 26MB attachment (exceeds 25MB limit)
    params = {
        "to": "test@example.com",
        "subject": "Test",
        "text": "Body",
        "attachments": [{
            "filename": "huge.bin",
            "content_type": "application/octet-stream",
            "data": base64.b64encode(b"x" * (26 * 1024 * 1024)).decode(),
        }]
    }

    with pytest.raises(ValueError) as exc_info:
        adapter._preview_gmail_send(params)

    error = json.loads(str(exc_info.value))
    assert error["error_code"] == "validation_error_attachment_too_large"
    assert "correlation_id" in error
    assert error["retriable"] is False
    assert error["source"] == "gmail.adapter"
```

### 5. Add error code to HTTP status mapping helper

**Location:** src/actions/adapters/google.py

```python
def _error_code_to_http_status(self, error_code: str) -> int:
    """Map error codes to HTTP status codes for Studio UI.

    Args:
        error_code: Error code from structured error

    Returns:
        HTTP status code
    """
    if error_code.startswith("validation_"):
        return 422  # Unprocessable Entity
    elif error_code.startswith("auth_") or error_code.startswith("oauth_"):
        return 401  # Unauthorized
    elif error_code == "provider_rate_limit":
        return 429  # Too Many Requests
    elif error_code == "provider_unavailable":
        return 503  # Service Unavailable
    elif error_code == "internal_only_recipient_blocked":
        return 403  # Forbidden
    else:
        return 500  # Internal Server Error
```

## Testing Checklist

- [ ] Unit test: Oversized attachment (26MB)
- [ ] Unit test: Blocked MIME type (.exe)
- [ ] Unit test: CID mismatch
- [ ] Unit test: Recipient count > 100
- [ ] Unit test: Internal-only blocks external
- [ ] Unit test: Internal-only allows test recipient
- [ ] Unit test: Structured error has all required fields
- [ ] Integration test: Preview with HTML + inline image
- [ ] Integration test: Preview returns sanitization summary
- [ ] E2E test: Send text-only email
- [ ] E2E test: Send HTML + inline image
- [ ] E2E test: Send HTML + inline + 2 attachments

## Environment Variables Required

```bash
# Existing
PROVIDER_GOOGLE_ENABLED=true
GOOGLE_CLIENT_ID=<oauth-client-id>
GOOGLE_CLIENT_SECRET=<oauth-client-secret>

# New for Sprint 54
GOOGLE_INTERNAL_ONLY=true
GOOGLE_INTERNAL_ALLOWED_DOMAINS=example.com,internal.example.com
GOOGLE_INTERNAL_TEST_RECIPIENTS=you@personal.com,test@external.com

# Telemetry
TELEMETRY_ENABLED=true
```

## Next Steps After Code Complete

1. Run all unit tests
2. Test preview endpoint manually
3. Set up E2E test environment
4. Run E2E tests against real Gmail
5. Deploy Prometheus rules
6. Create Grafana dashboard
7. Enable rollout controller (remove DRY_RUN)
8. Monitor metrics for 24h
9. Gradual rollout 0→10→50→100%

## Files Modified

- [x] src/actions/adapters/google.py (parameters, MIME integration, guards)
- [ ] src/actions/adapters/google.py (_preview_gmail_send update)
- [ ] src/actions/adapters/google.py (_execute_gmail_send update)
- [ ] src/actions/adapters/google.py (list_actions schema update)
- [ ] tests/actions/test_google_adapter_errors.py (NEW)

## Files Already Complete

- ✅ src/validation/attachments.py
- ✅ src/validation/html_sanitization.py
- ✅ src/actions/adapters/google_mime.py
- ✅ src/telemetry/prom.py (metrics)
- ✅ tests/validation/* (96 passing tests)
- ✅ docs/specs/GMAIL-RICH-EMAIL-INTEGRATION-DESIGN.md
