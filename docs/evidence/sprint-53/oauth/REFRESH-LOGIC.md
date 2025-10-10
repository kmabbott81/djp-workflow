# OAuth Token Refresh with Redis Lock

**Sprint 53 Phase B**
**Date:** October 8, 2025
**Feature:** Automatic token refresh with distributed lock (stampede prevention)

## Overview

This document describes the OAuth token refresh mechanism implemented in Sprint 53 Phase B. The refresh logic automatically renews expiring OAuth tokens (within 120 seconds of expiry) using a Redis-based distributed lock to prevent token refresh stampedes across multiple backend instances.

## Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────┐
│ Action Execution (e.g., gmail.send)                                 │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ GoogleAdapter.execute()                                             │
│  ├─ Call: get_tokens_with_auto_refresh()                            │
└─────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────┐
│ OAuthTokenCache.get_tokens_with_auto_refresh()                      │
│  ├─ 1. Fetch current tokens from cache                              │
│  ├─ 2. Check if expires_at is within 120 seconds                    │
│  └─ 3. Decision: Refresh needed?                                    │
└─────────────────────────────────────────────────────────────────────┘
                      │                                │
                      │ No (>120s remaining)           │ Yes (<120s)
                      ▼                                ▼
         ┌─────────────────────┐       ┌─────────────────────────────┐
         │ Return current      │       │ Attempt Redis Lock          │
         │ tokens (no refresh) │       │ Key: oauth:refresh:         │
         └─────────────────────┘       │   {workspace}:user:{prov}   │
                                       │ NX=true, EX=10s              │
                                       └─────────────────────────────┘
                                                      │
                                   ┌──────────────────┴──────────────────┐
                                   │                                     │
                          Lock Acquired?                       Lock Already Held
                                   │                                     │
                                  Yes                                   No
                                   │                                     │
                                   ▼                                     ▼
                  ┌──────────────────────────────┐      ┌──────────────────────────┐
                  │ Perform Token Refresh        │      │ Wait & Retry (3 attempts)│
                  │  ├─ POST to Google token EP  │      │  ├─ Sleep 500ms          │
                  │  ├─ grant_type=refresh_token │      │  ├─ Re-fetch tokens      │
                  │  ├─ client_id, client_secret │      │  └─ Check if refreshed   │
                  │  └─ refresh_token            │      └──────────────────────────┘
                  └──────────────────────────────┘                     │
                                   │                                    │
                                   ▼                                    ▼
                  ┌──────────────────────────────┐      ┌──────────────────────────┐
                  │ Parse Response               │      │ Tokens Refreshed?        │
                  │  ├─ access_token (new)       │      │  Yes: Return new tokens  │
                  │  ├─ expires_in (seconds)     │      │  No: Raise error         │
                  │  └─ scope                    │      └──────────────────────────┘
                  └──────────────────────────────┘
                                   │
                                   ▼
                  ┌──────────────────────────────┐
                  │ Store Tokens                 │
                  │  ├─ Save to Redis            │
                  │  ├─ TTL = expires_in         │
                  │  └─ Emit metrics             │
                  └──────────────────────────────┘
                                   │
                                   ▼
                  ┌──────────────────────────────┐
                  │ Release Redis Lock           │
                  │  DEL oauth:refresh:...       │
                  └──────────────────────────────┘
                                   │
                                   ▼
                  ┌──────────────────────────────┐
                  │ Return Refreshed Tokens      │
                  └──────────────────────────────┘
```

## Key Components

### 1. Refresh Trigger Logic

**File:** `src/auth/oauth/tokens.py`
**Method:** `get_tokens_with_auto_refresh()`

**Condition:** Token expires within 120 seconds

```python
def _should_refresh(expires_at: datetime) -> bool:
    """Check if token should be refreshed."""
    time_until_expiry = expires_at - datetime.utcnow()
    return time_until_expiry.total_seconds() < 120
```

### 2. Redis Lock (Stampede Prevention)

**Purpose:** Prevent multiple backend instances from refreshing the same token simultaneously.

**Lock Key Format:**
```
oauth:refresh:{workspace_id}:user:{provider}
```

**Lock Parameters:**
- **NX (Not Exists):** Only set if key doesn't exist (first caller wins)
- **EX (Expiry):** 10 seconds TTL (auto-cleanup if process crashes)

**Implementation:**
```python
lock_key = f"oauth:refresh:{workspace_id}:user:{provider}"
acquired = redis_client.set(lock_key, "1", nx=True, ex=10)

if acquired:
    try:
        # Perform refresh
        new_tokens = await _perform_refresh(...)
        return new_tokens
    finally:
        redis_client.delete(lock_key)  # Always release lock
else:
    # Lock held by another process - wait and retry
    for attempt in range(3):
        await asyncio.sleep(0.5)
        tokens = await get_tokens(provider, workspace_id, user_email)
        if not _should_refresh(tokens["expires_at"]):
            return tokens  # Another process refreshed successfully

    raise HTTPException(503, "Token refresh in progress, retry later")
```

### 3. Token Refresh Execution

**Endpoint:** `https://oauth2.googleapis.com/token`

**Request:**
```json
{
    "grant_type": "refresh_token",
    "refresh_token": "<USER_REFRESH_TOKEN>",
    "client_id": "<GOOGLE_CLIENT_ID>",
    "client_secret": "<GOOGLE_CLIENT_SECRET>"
}
```

**Response:**
```json
{
    "access_token": "ya29.a0AfH6SMBx...",
    "expires_in": 3600,
    "scope": "https://www.googleapis.com/auth/gmail.send",
    "token_type": "Bearer"
}
```

**Note:** Google may or may not return a new `refresh_token`. If not provided, the existing refresh token is reused.

### 4. Token Storage

**Cache Key Format:**
```
oauth:tokens:{workspace_id}:{provider}:{user_email}
```

**Stored Data:**
```json
{
    "access_token": "encrypted_access_token",
    "refresh_token": "encrypted_refresh_token",
    "expires_at": "2025-10-08T12:34:56.789Z",
    "scope": "https://www.googleapis.com/auth/gmail.send"
}
```

**TTL:** Set to `expires_in` seconds (typically 3600 seconds = 1 hour)

## Error Handling

### Refresh Errors

| Error Reason | HTTP Status | Description | Bounded Reason |
|--------------|-------------|-------------|----------------|
| Invalid grant | 400 | Refresh token expired or revoked | `oauth_refresh_invalid_grant` |
| Invalid client | 401 | Client credentials incorrect | `oauth_refresh_invalid_client` |
| Network error | 503 | Google API unreachable | `oauth_refresh_network_error` |
| Timeout | 504 | Request exceeded timeout | `oauth_refresh_timeout` |
| Lock contention | 503 | Too many concurrent refresh attempts | `oauth_refresh_lock_contention` |

### Metrics Emitted

All refresh errors emit metrics to track error distribution:

```python
relay_oauth_token_refresh_errors_total{
    provider="google",
    reason="oauth_refresh_invalid_grant"
} 1
```

## Degraded Mode (No Redis)

If Redis is unavailable, the refresh logic still works but without lock protection:

- Each backend instance may attempt refresh independently
- Risk of token refresh stampede
- Potential for rate limiting from OAuth provider
- Still better than forcing users to re-authenticate

**Recommendation:** Always deploy with Redis in production for optimal behavior.

## Test Coverage

### Unit Tests

**File:** `tests/auth/test_oauth_refresh_lock.py`

1. ✅ `test_concurrent_refresh_only_one_performs_refresh` - Verify only one caller refreshes
2. ✅ `test_refresh_lock_acquisition_and_release` - Verify lock lifecycle
3. ✅ `test_refresh_lock_contention_retry_logic` - Verify retry mechanism
4. ✅ `test_refresh_token_not_expiring_no_refresh` - Verify no refresh when not needed
5. ✅ `test_refresh_without_redis_still_works` - Verify degraded mode
6. ✅ `test_perform_refresh_calls_google_endpoint` - Verify Google API call
7. ✅ `test_perform_refresh_handles_google_error` - Verify error handling
8. ✅ `test_refresh_lock_key_format` - Verify lock key format

**Status:** All 8 tests passing

### Integration Tests

**File:** `tests/integration/test_google_send_flow.py`

- ✅ Integration test with skip gate (requires all OAuth envs)
- ✅ Documents manual OAuth consent flow
- ✅ Tests full flow: authorize → callback → status → preview → execute

**Status:** Quarantined by default (skipped unless `PROVIDER_GOOGLE_ENABLED=true`)

## Performance Characteristics

### Refresh Latency

- **Typical:** 200-500ms (Google token endpoint response time)
- **With Lock Contention:** +500ms per retry (max 3 retries)
- **Worst Case:** ~2 seconds (lock held + 3 retries)

### Cache Behavior

- **Hot Path (no refresh):** <5ms (Redis read only)
- **Cold Path (refresh):** 200-500ms (Google API call + Redis write)

### Lock Duration

- **Typical:** 200-500ms (time to complete refresh)
- **Max TTL:** 10 seconds (prevents orphaned locks)

## Security Considerations

### Encryption

- All tokens (access + refresh) encrypted with Fernet before Redis storage
- Encryption key: `OAUTH_ENCRYPTION_KEY` environment variable
- Key rotation: Supported via key versioning (not implemented in Phase B)

### Lock Safety

- Lock key includes `workspace_id` for tenant isolation
- Short TTL (10s) prevents DoS from orphaned locks
- Lock released in `finally` block to handle crashes

### Token Scope

- Refresh only renews tokens with existing scope
- Cannot escalate privileges during refresh
- Scope stored with tokens for validation

## Production Recommendations

1. **Redis Deployment:** Always deploy with Redis for lock coordination
2. **Monitoring:** Track `relay_oauth_token_refresh_total` and `relay_oauth_token_refresh_errors_total`
3. **Alerting:** Alert on high `oauth_refresh_invalid_grant` rate (indicates mass revocation)
4. **Key Rotation:** Plan for encryption key rotation in future sprint
5. **TTL Tuning:** Monitor cache hit rates and adjust TTL if needed

## References

- RFC 6749 (OAuth 2.0): https://datatracker.ietf.org/doc/html/rfc6749
- Google OAuth 2.0: https://developers.google.com/identity/protocols/oauth2
- Redis SET NX: https://redis.io/commands/set/
- Fernet Encryption: https://cryptography.io/en/latest/fernet/

---

**Sprint 53 Phase B** | OAuth Token Refresh with Redis Lock | **Complete**
