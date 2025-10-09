# Sprint 53 Phase B - Progress Checkpoint

**Date:** October 8, 2025
**Branch:** `sprint/53-provider-vertical-slice`
**Status:** ⏳ **IN PROGRESS** (Async integration complete, Gmail adapter pending)

---

## ✅ Completed Work

### 1. Database Migration ✅
- **File:** `migrations/versions/bb51836389e7_add_oauth_tokens_table.py`
- **Applied:** Yes (local dev database)
- **Table:** `oauth_tokens` with 11 columns, 2 indexes, unique constraint
- **ENUM Reuse:** Fixed with `postgresql.ENUM(..., create_type=False)`
- **Evidence:** `docs/evidence/sprint-53/oauth/MIGRATION-APPLIED.md`

### 2. OAuth Endpoints ✅
- **`GET /oauth/google/authorize`**
  - Creates CSRF state token with PKCE (SHA-256)
  - Stores state in Redis (10-minute TTL)
  - Builds Google OAuth URL with code_challenge
  - Returns authorize_url for user redirect

- **`GET /oauth/google/callback`**
  - Validates state token (one-time use)
  - Exchanges authorization code for tokens
  - Stores encrypted tokens in DB + Redis cache
  - Emits oauth_events_total metrics

- **`GET /oauth/google/status`**
  - Checks if workspace has Google OAuth connection
  - Returns linked status and granted scopes

### 3. OAuth Metrics ✅
- **Metric:** `oauth_events_total{provider, event}`
- **Events tracked:**
  - `authorize_started`
  - `callback_error`
  - `invalid_state`
  - `token_exchange_failed`
  - `token_exchange_timeout`
  - `missing_access_token`
  - `tokens_stored`
- **Integration:** Prometheus + Grafana ready

### 4. OAuthTokenCache DB Methods ✅
- **Implemented:**
  - `async def store_tokens(...)` - Encrypt + upsert to DB, cache in Redis
  - `async def get_tokens(...)` - Check Redis first, fallback to DB, warm cache
  - `async def _store_in_db(...)` - INSERT ... ON CONFLICT UPDATE
  - `async def _get_from_db(...)` - SELECT + decrypt tokens
  - `async def _delete_from_db(...)` - DELETE from oauth_tokens table

- **Encryption:** Fernet (AES-128) using `OAUTH_ENCRYPTION_KEY`
- **Cache Pattern:** Write-through (DB first, then Redis)
- **TTL:** Matches token expiry (default 3600s)

### 5. Async Integration ✅
- **Fixed:** All OAuth endpoint calls now use `await` properly
- **Files Modified:**
  - `src/webapi.py` (lines 1172, 1211)
  - `src/auth/oauth/tokens.py` (all DB methods now async)

### 6. Alembic Environment Fixes ✅
- **Issue 1:** Added `dotenv` loading for DATABASE_URL
- **Issue 2:** Escaped `%` characters for ConfigParser
- **File:** `migrations/env.py`

---

## ⏳ Remaining Work (In Priority Order)

### 1. Token Refresh with Redis Lock 🔴 HIGH PRIORITY
**Why:** Prevents refresh stampedes, ensures safe token renewal
**What to implement:**
- Check `expires_at <= now() + 120s` before returning tokens
- Redis lock key: `oauth:refresh:{workspace_id}:{actor_type}:{provider}`
- Lock TTL: 10 seconds
- If lock held: wait 1s, retry once, return current token or 401
- Call Google token refresh endpoint with refresh_token
- Update DB + Redis with new tokens
- Emit metrics: `oauth_events_total{event="refresh_start|refresh_ok|refresh_failed|refresh_locked"}`

**Files to modify:**
- `src/auth/oauth/tokens.py` - Add `async def refresh_token_if_needed(...)`
- `src/auth/oauth/tokens.py` - Modify `get_tokens()` to check expiry and call refresh

**Code skeleton:**
```python
async def get_tokens_with_auto_refresh(self, provider: str, workspace_id: str, actor_id: str) -> Optional[dict]:
    tokens = await self.get_tokens(provider, workspace_id, actor_id)
    if not tokens:
        return None

    # Check if expiring soon (within 2 minutes)
    expires_at = tokens["expires_at"]
    if expires_at <= datetime.utcnow() + timedelta(seconds=120):
        # Try to acquire refresh lock
        lock_key = f"oauth:refresh:{workspace_id}:user:{provider}"
        if self.redis_client.set(lock_key, "1", nx=True, ex=10):
            # We got the lock, perform refresh
            try:
                refreshed = await self._perform_refresh(provider, workspace_id, actor_id, tokens["refresh_token"])
                return refreshed
            finally:
                self.redis_client.delete(lock_key)
        else:
            # Lock held by another request
            # Wait 1s and return current tokens if still valid
            await asyncio.sleep(1)
            if expires_at > datetime.utcnow():
                return tokens
            else:
                raise HTTPException(401, "token_expired")

    return tokens

async def _perform_refresh(self, provider: str, workspace_id: str, actor_id: str, refresh_token: str) -> dict:
    # POST to https://oauth2.googleapis.com/token
    # grant_type=refresh_token, refresh_token=..., client_id=..., client_secret=...
    # Store new tokens, emit metrics
    pass
```

### 2. Gmail Adapter (google.gmail.send) 🔴 HIGH PRIORITY
**Why:** Core deliverable for Sprint 53 vertical slice

**File:** `src/actions/adapters/google.py`

**Schema:**
```python
{
    "to": "email (required)",
    "subject": "string (required)",
    "text": "string (required)",
    "cc": ["email?"],
    "bcc": ["email?"]
}
```

**Methods:**
- `preview(params)` - Validate, build MIME, Base64URL encode (NO SEND)
- `execute(preview_id)` - Fetch tokens (auto-refresh), POST to Gmail API
- Check `PROVIDER_GOOGLE_ENABLED=true` before execute (501 if false)

**Gmail API endpoint:**
```
POST https://gmail.googleapis.com/gmail/v1/users/me/messages/send
Authorization: Bearer {access_token}
Content-Type: application/json

{"raw": "<base64url-encoded-MIME>"}
```

**Metrics to emit:**
- `action_exec_total{provider="google",action="gmail.send",status="ok|error"}`
- `action_error_total{provider="google",action="gmail.send",reason}`
- `action_latency_seconds{provider="google",action="gmail.send"}`

**Bounded error reasons:**
- `provider_disabled` (PROVIDER_GOOGLE_ENABLED=false)
- `oauth_token_missing` (no tokens found)
- `oauth_token_expired` (refresh failed)
- `gmail_4xx` (bad request, unauthorized, forbidden, etc.)
- `gmail_5xx` (server error, service unavailable)
- `validation_error` (invalid email, missing fields)

### 3. Unit Tests 🟡 MEDIUM PRIORITY
**Files to create:**
- `tests/auth/test_token_cache_async.py`
  - `test_get_from_redis_hit_is_fast_and_not_db`
  - `test_db_fallback_warms_redis`
  - `test_refresh_happens_when_close_to_expiry`
  - `test_refresh_lock_prevents_stampede`
  - `test_encryption_roundtrip_and_no_plaintext_in_db`

- `tests/actions/test_google_preview.py`
  - `test_mime_assembly_valid`
  - `test_validation_failures`
  - `test_base64url_no_padding`

- `tests/actions/test_google_execute_unit.py`
  - Mock HTTP client
  - Assert metrics + audit
  - Test 501 when flag off
  - Test 4xx/5xx error mapping

### 4. Integration Tests 🟡 MEDIUM PRIORITY
**File:** `tests/integration/test_google_send_flow.py`
**Mark:** `@pytest.mark.integration` (skipped in CI)
**Requires:** `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`, `PROVIDER_GOOGLE_ENABLED=true`

### 5. Smoke Test Updates 🟢 LOW PRIORITY
**File:** `scripts/post_alignment_validation.sh`
**Add:**
- Hit `/oauth/google/authorize` (no follow)
- Assert state in Redis
- Preview + execute `google.gmail.send` if env configured
- Print PromQL snippets for Grafana

**Evidence:** `docs/evidence/sprint-53/smoke/SMOKE-RESULTS.md`

### 6. Evidence Documentation 🟢 LOW PRIORITY
**Files to create:**
- `docs/evidence/sprint-53/oauth/ASYNC-CACHE-INTEGRATION.md`
- `docs/evidence/sprint-53/google/GMAIL-ADAPTER-DETAILS.md`
- `docs/evidence/sprint-53/tests/PHASE-B-TESTS-PASSING.md`
- `docs/evidence/sprint-53/oauth/TOKEN-REFRESH-FLOW.md`

### 7. Phase B Completion Summary 🟢 LOW PRIORITY
**File:** `docs/evidence/sprint-53/PHASE-B-COMPLETE.md`
**Include:**
- All deliverables
- Test results
- Metrics definitions
- Manual setup instructions (env vars)
- Rollback plan
- PR checklist

---

## Environment Variables Needed (Production)

**Already Set:**
- ✅ `OAUTH_ENCRYPTION_KEY` (Fernet key: `Mvwr_5P4VoevQaR7WcNUom56zII1QuECnErU0PfBSSE=`)
- ✅ `REDIS_URL` (redis.railway.internal)
- ✅ `DATABASE_URL`

**Not Yet Set (Required for Live Testing):**
- ⏳ `GOOGLE_CLIENT_ID` (from Google Cloud Console)
- ⏳ `GOOGLE_CLIENT_SECRET` (from Google Cloud Console)
- ⏳ `RELAY_PUBLIC_BASE_URL` (https://relay-production-f2a6.up.railway.app)
- ⏳ `PROVIDER_GOOGLE_ENABLED` (default: false, set to `true` for live test)

**Callback URL:** `${RELAY_PUBLIC_BASE_URL}/oauth/google/callback`

---

## Files Modified/Created So Far

### Modified:
```
src/webapi.py                         (+210 lines: 3 OAuth endpoints)
src/auth/oauth/tokens.py             (+150 lines: async DB methods)
src/telemetry/prom.py                (+10 lines: oauth_events metric)
src/telemetry/__init__.py            (+25 lines: oauth_events proxy)
migrations/env.py                    (+5 lines: dotenv + % escaping)
```

### Created:
```
migrations/versions/bb51836389e7_add_oauth_tokens_table.py
docs/evidence/sprint-53/oauth/MIGRATION-APPLIED.md
docs/evidence/sprint-53/PHASE-B-PROGRESS-CHECKPOINT.md (this file)
```

### Pending Creation:
```
src/actions/adapters/google.py       (Gmail adapter - ~300 lines estimated)
tests/auth/test_token_cache_async.py (~200 lines)
tests/actions/test_google_preview.py (~150 lines)
tests/actions/test_google_execute_unit.py (~200 lines)
tests/integration/test_google_send_flow.py (~100 lines)
docs/evidence/sprint-53/oauth/ASYNC-CACHE-INTEGRATION.md
docs/evidence/sprint-53/google/GMAIL-ADAPTER-DETAILS.md
docs/evidence/sprint-53/tests/PHASE-B-TESTS-PASSING.md
docs/evidence/sprint-53/oauth/TOKEN-REFRESH-FLOW.md
docs/evidence/sprint-53/PHASE-B-COMPLETE.md
```

---

## Estimated Remaining Effort

| Task | Complexity | Est. Time |
|------|------------|-----------|
| Token refresh + lock | Medium | 2-3 hours |
| Gmail adapter | High | 3-4 hours |
| Unit tests | Medium | 2-3 hours |
| Integration tests | Low | 1 hour |
| Smoke tests | Low | 1 hour |
| Evidence docs | Low | 1-2 hours |
| **TOTAL** | | **10-16 hours** |

---

## Next Steps (Immediate)

1. **Implement token refresh with Redis lock** (2-3 hours)
   - Prevents production issues with stale tokens
   - Enables auto-refresh during Gmail send

2. **Implement Gmail adapter** (3-4 hours)
   - Core deliverable for vertical slice
   - Depends on token refresh being complete

3. **Write unit tests** (2-3 hours)
   - Ensures correctness before live testing
   - Prevents flaky bugs

4. **Manual live test** (1 hour)
   - Set Google Cloud credentials in Railway
   - Test authorize → callback → send flow
   - Verify metrics in Grafana

5. **Create PR** (1 hour)
   - Merge to main
   - Deploy to production (behind flag)

---

## Risk Assessment

**Low Risk ✅:**
- Migration applied cleanly
- Async integration complete
- Metrics wired correctly
- No breaking changes to existing features

**Medium Risk ⚠️:**
- Token refresh logic complex (race conditions possible)
- Gmail API integration untested (need credentials)
- No live OAuth flow testing yet

**High Risk 🔴:**
- None identified (feature flag provides safety)

---

## Rollback Plan

If issues arise after deployment:

1. **Immediate:** Set `PROVIDER_GOOGLE_ENABLED=false` in Railway
   - Disables Gmail action execution
   - OAuth endpoints remain available (safe)

2. **If needed:** Revert migration:
   ```bash
   alembic downgrade ce6ac882b60d
   ```
   - Drops oauth_tokens table
   - Does NOT affect existing features

3. **Nuclear option:** Revert branch merge on main

---

## Questions for User

1. **Priority:** Should we focus on token refresh + Gmail adapter first, or comprehensive tests?
2. **Google Credentials:** Do you have a Google Cloud project ready for OAuth setup?
3. **Testing:** Would you like to do a live OAuth test before completing all unit tests?
4. **Timeline:** What's the target completion date for Phase B?

---

**Status Summary:**
✅ Foundation complete (DB, endpoints, async, metrics)
⏳ Core logic pending (refresh, Gmail adapter)
⏳ Quality pending (tests, evidence docs)

**Ready for:** Token refresh implementation → Gmail adapter → Live testing
