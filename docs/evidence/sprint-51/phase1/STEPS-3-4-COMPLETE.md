# Sprint 51 Phase 1 - Steps 3-4 Complete

**Date:** October 6, 2025
**Branch:** `sprint/51-phase1-secure-core`
**Status:** ⏸️ PAUSED FOR REVIEW (Steps 3-4 complete, awaiting approval for Step 5)

## Summary

Successfully implemented **Auth Middleware + RBAC + Audit Logging** for Sprint 51 Phase 1. All code committed, OpenAPI updated. Ready for local smoke tests once DATABASE_URL is configured.

## Commits

```
85b9891 S51 P1: Add OpenAPI security scheme and documentation
5f58fb3 S51 P1: Audit logging for preview/execute with redaction
a88dc9a S51 P1: Auth middleware + scopes/RBAC (API-key + user sessions)
f2e728a S51 P1: Alembic migrations + API key CLI + roles CLI
```

**Total Changes:** `105 files changed, 13887 insertions(+), 28 deletions(-)`

## Step 3: Auth Middleware + RBAC ✅

### Files Created

- `src/auth/__init__.py` - Auth module init
- `src/auth/security.py` - Complete auth implementation (210 lines)

### Implementation Details

**`parse_bearer_token(request)`**
- Extracts token from `Authorization: Bearer <key>` header
- Returns None if missing or malformed

**`load_api_key(token)`**
- Verifies API key using Argon2 constant-time hash comparison
- Queries all non-revoked keys from database
- Returns `(key_id, workspace_id, scopes)` or None
- Security: Uses `argon2.PasswordHasher().verify()` for constant-time

**`load_user_scopes(user_id, workspace_id)`**
- Loads user's role from roles table
- Derives scopes from role using `ROLE_SCOPES` mapping
- Returns empty list if no role assigned

**`@require_scopes(required_scopes)` Decorator**
- FastAPI decorator for endpoint protection
- Try API key auth first (Bearer token path)
- Fall back to user/session auth (dev/staging)
- Stores auth context in `request.state`:
  - `actor_type` ('api_key' | 'user')
  - `actor_id` (key UUID or user_id)
  - `workspace_id` (UUID)
  - `scopes` (list of strings)
- Raises 401 if no valid auth
- Raises 403 if insufficient scopes

**Role-to-Scopes Mapping:**
```python
ROLE_SCOPES = {
    "admin": ["actions:preview", "actions:execute", "audit:read"],
    "developer": ["actions:preview", "actions:execute"],
    "viewer": ["actions:preview"],
}
```

### Integration

**Updated Endpoints:**
- `POST /actions/preview` → `@require_scopes(["actions:preview"])`
- `POST /actions/execute` → `@require_scopes(["actions:execute"])`
- `GET /actions` → Public (no auth required)

### Error Map

| HTTP | Condition | Meaning |
|------|-----------|---------|
| 401 | No auth or invalid key | Missing/invalid authentication |
| 403 | Insufficient scopes | Scope check failed |
| 409 | Idempotency conflict | Preserved from Sprint 50 Day 1 |
| 501 | Provider not configured | Microsoft/Google not ready |
| 504 | Timeout | Execution timeout |

## Step 4: Audit Logging with Redaction ✅

### Files Created

- `src/audit/__init__.py` - Audit module init
- `src/audit/logger.py` - Audit logging implementation (110 lines)

### Implementation Details

**`canonical_json(obj)`**
- Converts Python object to stable JSON
- `sort_keys=True`, `ensure_ascii=False`
- Used for consistent hashing

**`sha256_hex(data)`**
- Hashes string with SHA256
- Returns hex digest

**`write_audit(...)`**
- Async function to insert audit log rows
- **Redaction:**
  - `params_hash` = SHA256 hex of canonical JSON
  - `params_prefix64` = First 64 chars of canonical JSON
  - `idempotency_key_hash` = SHA256 hex (if present)
  - **NEVER** stores secrets or full payloads
- Inserts into `action_audit` table with bounded enums

### Integration

**`POST /actions/preview`**
- Wrapped in try/except/finally
- Tracks `start_time`, `duration_ms`
- Maps exceptions to `error_reason` enum:
  - ValueError → `validation`
  - General Exception → `other`
- Captures:
  - `run_id` = None (preview has no run)
  - `preview_id` (from result)
  - `provider`, `action_id` (parsed from request)
  - `signature_present` = bool(`X-Signature` in headers)
  - `params_hash`, `params_prefix64` (redacted)
  - `status` ('ok' | 'error')
  - `http_status` (200 | 400 | 500)
- Audit write failure does NOT break request (wrapped in try/except)

**`POST /actions/execute`**
- Same pattern as preview
- Additional error mappings:
  - NotImplementedError → `provider_unconfigured` (501)
  - TimeoutError → `timeout` (504)
  - "5xx" in exception → `downstream_5xx`
- Captures:
  - `run_id` (from execute result)
  - `preview_id` (from request body)
  - `idempotency_key_hash` (if provided)
  - `workspace_id` (from auth context)

### Audit Schema

```sql
action_audit:
  - id (uuid)
  - run_id (text, null for preview)
  - request_id (text, from X-Request-ID)
  - workspace_id (uuid)
  - actor_type (enum: 'user' | 'api_key')
  - actor_id (text)
  - provider (text)
  - action_id (text)
  - preview_id (text, null)
  - idempotency_key_hash (text, null)
  - signature_present (bool)
  - params_hash (text, SHA256)
  - params_prefix64 (text, first 64 chars)
  - status (enum: 'ok' | 'error')
  - error_reason (enum: 'timeout' | 'provider_unconfigured' | 'validation' | 'downstream_5xx' | 'other' | 'none')
  - http_status (int)
  - duration_ms (int)
  - created_at (timestamptz)
```

## OpenAPI Updates ✅

**Commit:** `85b9891`

### Changes

**Security Scheme Added:**
```yaml
components:
  securitySchemes:
    ApiKeyBearer:
      type: http
      scheme: bearer
      bearerFormat: API-Key
      description: "API key in format: relay_sk_<random>"
```

**Endpoints Marked:**
- `/actions/preview` → `security: [ApiKeyBearer]`
- `/actions/execute` → `security: [ApiKeyBearer]`

**Documentation Added:**
- Authentication section (Authorization header format)
- Scopes reference (preview, execute, audit:read)
- Roles reference (viewer, developer, admin)
- Error codes (401, 403, 409, 501, 504)

**Export:**
- OpenAPI schema available at `GET /openapi.json`
- Updated automatically via custom `openapi()` function

## Local Smoke Tests

**Status:** ⚠️ REQUIRES DATABASE_URL

### Prerequisites

1. Set DATABASE_URL environment variable:
   ```bash
   export DATABASE_URL="postgresql://user:pass@host:5432/dbname"
   ```

2. Run migrations:
   ```bash
   alembic upgrade head
   ```

3. Create test API keys:
   ```bash
   TEST_WORKSPACE_ID="00000000-0000-0000-0000-000000000001"

   # Viewer
   python scripts/api_keys_cli.py create-key --workspace $TEST_WORKSPACE_ID --role viewer
   # Save output: VIEWER_KEY=relay_sk_...

   # Developer
   python scripts/api_keys_cli.py create-key --workspace $TEST_WORKSPACE_ID --role developer
   # Save output: DEV_KEY=relay_sk_...

   # Admin
   python scripts/api_keys_cli.py create-key --workspace $TEST_WORKSPACE_ID --role admin
   # Save output: ADMIN_KEY=relay_sk_...
   ```

### Test Plan

**Test 1: Viewer - Preview OK, Execute Forbidden**
```bash
# Preview should succeed
curl -s -X POST http://127.0.0.1:8000/actions/preview \
  -H "Authorization: Bearer $VIEWER_KEY" \
  -H "Content-Type: application/json" \
  -d '{"action":"independent.webhook.save","params":{"url":"https://example.com","payload":{"a":1}}}' \
  | jq .

# Execute should fail with 403
curl -si -X POST http://127.0.0.1:8000/actions/execute \
  -H "Authorization: Bearer $VIEWER_KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-viewer" \
  -d '{"preview_id":"deadbeef"}' \
  | head -20
# Expected: HTTP/1.1 403 Forbidden
```

**Test 2: Developer - Preview + Execute OK**
```bash
# Preview
PREV=$(curl -s -X POST http://127.0.0.1:8000/actions/preview \
  -H "Authorization: Bearer $DEV_KEY" \
  -H "Content-Type: application/json" \
  -d '{"action":"independent.webhook.save","params":{"url":"https://example.com","payload":{"test":"sprint51"}}}')

PID=$(echo "$PREV" | jq -r .preview_id)
echo "Preview ID: $PID"

# Execute
curl -si -X POST http://127.0.0.1:8000/actions/execute \
  -H "Authorization: Bearer $DEV_KEY" \
  -H "Content-Type: application/json" \
  -H "Idempotency-Key: test-dev-$(date +%s)" \
  -d "{\"preview_id\":\"$PID\"}" \
  | head -40
# Expected: HTTP/1.1 200 OK
```

**Test 3: Check Audit Logs**
```bash
# Query database directly
psql $DATABASE_URL -c "
SELECT
  created_at,
  actor_type,
  provider,
  action_id,
  status,
  error_reason,
  http_status,
  duration_ms,
  params_prefix64,
  request_id
FROM action_audit
ORDER BY created_at DESC
LIMIT 5;
"
```

**Expected Audit Rows:**
- 2-3 preview entries (viewer + developer)
- 1 execute entry (developer)
- 1 execute error entry (viewer with 403)
- All with `params_hash`, `params_prefix64`, no secrets
- `signature_present` = false (no X-Signature header in tests)

## Files Changed Summary

### New Files (Sprint 51 Phase 1 Only)

```
alembic.ini                                         (118 lines)
migrations/env.py                                   (83 lines)
migrations/versions/ce6ac882b60d_*.py               (117 lines)
scripts/api_keys_cli.py                             (166 lines)
scripts/roles_cli.py                                (120 lines)
src/auth/__init__.py                                (1 line)
src/auth/security.py                                (210 lines)
src/audit/__init__.py                               (1 line)
src/audit/logger.py                                 (110 lines)
src/db/__init__.py                                  (1 line)
src/db/connection.py                                (65 lines)
docs/SPRINT-51-SPEC.md                              (667 lines)
docs/SPRINT-51-52-BACKLOG.md                        (885 lines)
```

### Modified Files

```
src/webapi.py                                       (+479 lines)
  - Import require_scopes
  - Add @require_scopes decorators to preview/execute
  - Integrate audit logging in preview/execute
  - Add custom OpenAPI schema with security

requirements.in                                     (+5 lines)
  - asyncpg>=0.30.0
  - alembic>=1.13.0
  - sqlalchemy>=2.0.30
  - argon2-cffi>=23.1.0
  - psycopg2-binary>=2.9.9
```

## Database Schema

**Tables Created:**
- `api_keys` (7 columns + indexes)
- `roles` (5 columns + index)
- `action_audit` (16 columns + 2 indexes)

**ENUM Types:**
- `actor_type_enum` ('user', 'api_key')
- `role_enum` ('admin', 'developer', 'viewer')
- `audit_status_enum` ('ok', 'error')
- `error_reason_enum` ('timeout', 'provider_unconfigured', 'validation', 'downstream_5xx', 'other', 'none')

## Security Notes

✅ **Argon2 constant-time verification** for API keys
✅ **Scopes enforce least privilege** (viewer < developer < admin)
✅ **Audit logs redact secrets** (hash + prefix64 only)
✅ **Request IDs for tracing** (from Sprint 50 Day 1 middleware)
✅ **Revoked keys rejected** (revoked_at IS NULL check)
✅ **Workspace isolation** (workspace_id from auth context)

## Next Steps (Awaiting Review Approval)

**Step 5:** Implement `GET /audit` endpoint (admin-only)
- Query action_audit table with filters
- Pagination with limit/offset
- Sort by created_at DESC
- Requires `audit:read` scope

**Step 6:** Unit tests
- Test auth middleware (401/403 cases)
- Test RBAC (viewer/dev/admin permissions)
- Test audit logging (redaction, enum mapping)

**Step 7:** Deploy to Railway + smoke tests
- Apply migrations on Railway database
- Deploy updated service
- Run production smoke tests
- Validate audit logs populated

**Step 8:** Evidence package + PR
- Generate final evidence with metrics
- Create PR with checklist
- Request code review

---

## 🛑 PAUSED FOR REVIEW

**What's Complete:**
- ✅ Alembic migrations (3 tables, 4 enums)
- ✅ CLI tools (api_keys_cli, roles_cli)
- ✅ Auth middleware (API-key + user sessions)
- ✅ RBAC (viewer/developer/admin roles)
- ✅ Audit logging (preview + execute with redaction)
- ✅ OpenAPI security scheme

**What's Needed to Continue:**
- DATABASE_URL for local smoke tests
- Review approval for Step 5-8 implementation
- Decision on deployment timeline

**Awaiting:** User review and go/no-go for Steps 5-8

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

*Report generated: 2025-10-06 07:15 UTC*
