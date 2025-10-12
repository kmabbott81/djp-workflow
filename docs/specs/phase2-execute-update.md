# Phase 2 - _execute_gmail_send Update Summary

## Changes Made

### 1. Added recipient count validation (after Pydantic validation)
```python
validated.validate_recipient_count()
```

### 2. Added internal-only recipient check (after rollout gate)
```python
self._check_internal_only_recipients(validated.to, validated.cc, validated.bcc)
```

### 3. Updated MIME builder call with correlation_id tracking
```python
correlation_id = str(uuid.uuid4())

try:
    mime_message, _ = self._build_mime_message(
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
    # Parse structured error
    try:
        error_payload = json.loads(str(e))
        error_payload["correlation_id"] = correlation_id
    except json.JSONDecodeError:
        # Fallback for non-JSON errors
        error_payload = self._create_structured_error(
            error_code="unknown_error",
            message=str(e),
            retriable=False,
        )
        error_payload["correlation_id"] = correlation_id

    # Record metrics
    record_action_error(provider="google", action="gmail.send", reason=error_payload["error_code"])
    duration = time.perf_counter() - start_time
    record_action_execution(provider="google", action="gmail.send", status="error", duration_seconds=duration)

    # Log for ops with correlation_id
    import logging
    logger = logging.getLogger(__name__)
    logger.error(
        f"Gmail send failed: {error_payload['error_code']}",
        extra={
            "correlation_id": correlation_id,
            "error_code": error_payload["error_code"],
            "workspace_id": workspace_id,
            "actor_id": actor_id,
        },
    )

    # Return structured error to caller
    raise ValueError(json.dumps(error_payload)) from e
```

### 4. Added correlation_id logging on success
```python
# Success case (after Gmail API returns 200)
logger = logging.getLogger(__name__)
logger.info(
    f"Gmail sent successfully",
    extra={
        "correlation_id": correlation_id,
        "message_id": response_data.get("id"),
        "workspace_id": workspace_id,
        "actor_id": actor_id,
    },
)

# NOTE: correlation_id is NOT included in API response (only in logs)
return {
    "status": "sent",
    "message_id": response_data.get("id"),
    "thread_id": response_data.get("threadId"),
    "to": validated.to,
    "subject": validated.subject,
}
```

## Key Points

- correlation_id generated once at start of MIME build
- Logged on both success and failure
- NOT exposed in API response (security/privacy)
- Structured errors include correlation_id for ops tracing
- All validation errors wrapped in structured format
