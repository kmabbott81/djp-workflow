# Sprint 51 Phase 1 - OpenAPI Schema Changes

**Date:** October 7, 2025
**Branch:** `sprint/51-phase1-secure-core`
**Commit:** `85b9891` (S51 P1: Add OpenAPI security scheme and documentation)
**Status:** ✅ Schema Updated and Deployed

## Summary

Added **API key authentication** (`ApiKeyBearer` security scheme) to OpenAPI schema and documented the new **GET /audit endpoint** for admin-only audit log queries.

---

## Changes to OpenAPI Schema

### 1. Security Scheme Added ✅

**Location:** `components.securitySchemes.ApiKeyBearer`

**Schema Definition:**
```yaml
components:
  securitySchemes:
    ApiKeyBearer:
      type: http
      scheme: bearer
      bearerFormat: API-Key
      description: |
        API key authentication for Relay actions API.

        Format: relay_sk_<random_string>

        Include in Authorization header:
        Authorization: Bearer relay_sk_ZzcoNmslLWdUDNRX

        Required scopes:
        - actions:preview: Preview actions (viewer, developer, admin)
        - actions:execute: Execute actions (developer, admin)
        - audit:read: Query audit logs (admin only)
```

**Why HTTP Bearer:**
- Industry standard for API keys (RFC 6750)
- Compatible with all HTTP clients (curl, Postman, SDKs)
- FastAPI native support via `HTTPBearer` dependency

**Alternative Considered:** API key in custom header (e.g., `X-API-Key`)
**Rejected:** Less standardized, no built-in FastAPI support

---

### 2. Endpoints Updated with Security Requirements ✅

#### `/actions/preview` (POST)

**Before:**
```yaml
paths:
  /actions/preview:
    post:
      summary: Preview Action
      # No security requirement
```

**After:**
```yaml
paths:
  /actions/preview:
    post:
      summary: Preview Action
      security:
        - ApiKeyBearer: []
      description: |
        Generate a preview of an action before execution.

        Required scope: actions:preview
        Available to: viewer, developer, admin
```

**Impact:** All preview requests now require valid API key with `actions:preview` scope

---

#### `/actions/execute` (POST)

**Before:**
```yaml
paths:
  /actions/execute:
    post:
      summary: Execute Action
      # No security requirement
```

**After:**
```yaml
paths:
  /actions/execute:
    post:
      summary: Execute Action
      security:
        - ApiKeyBearer: []
      description: |
        Execute a previewed action.

        Required scope: actions:execute
        Available to: developer, admin
```

**Impact:** All execute requests now require valid API key with `actions:execute` scope

---

### 3. New Endpoint: GET /audit (Admin-Only) ✅

**Location:** `paths./audit`

**Full Schema:**
```yaml
paths:
  /audit:
    get:
      summary: Query Audit Logs
      description: |
        Query action audit logs with filters and pagination.

        Required scope: audit:read (admin only)

        Audit logs capture:
        - Preview and execute requests
        - Redacted parameters (hash + prefix64 only)
        - Request IDs for tracing
        - Actor information (API key or user)
        - Duration and status

      security:
        - ApiKeyBearer: []

      parameters:
        - name: limit
          in: query
          schema:
            type: integer
            default: 50
            minimum: 1
            maximum: 200
          description: Number of items per page (1-200)

        - name: offset
          in: query
          schema:
            type: integer
            default: 0
            minimum: 0
          description: Offset for pagination (>= 0)

        - name: provider
          in: query
          schema:
            type: string
          description: Filter by provider (e.g., "independent", "microsoft")

        - name: action_id
          in: query
          schema:
            type: string
          description: Filter by action ID (e.g., "webhook.save")

        - name: status
          in: query
          schema:
            type: string
            enum: [ok, error]
          description: Filter by status (ok or error)

        - name: actor_type
          in: query
          schema:
            type: string
            enum: [user, api_key]
          description: Filter by actor type

        - name: from_date
          in: query
          schema:
            type: string
            format: date-time
          description: Filter logs after this timestamp (ISO8601)

        - name: to_date
          in: query
          schema:
            type: string
            format: date-time
          description: Filter logs before this timestamp (ISO8601)

      responses:
        '200':
          description: Audit logs returned successfully
          content:
            application/json:
              schema:
                type: object
                properties:
                  items:
                    type: array
                    items:
                      type: object
                      properties:
                        id:
                          type: string
                          format: uuid
                        run_id:
                          type: string
                          nullable: true
                        request_id:
                          type: string
                        workspace_id:
                          type: string
                          format: uuid
                        actor_type:
                          type: string
                          enum: [user, api_key]
                        actor_id:
                          type: string
                        provider:
                          type: string
                        action_id:
                          type: string
                        preview_id:
                          type: string
                          nullable: true
                        signature_present:
                          type: boolean
                        params_prefix64:
                          type: string
                          description: First 64 chars of params JSON (redacted)
                        status:
                          type: string
                          enum: [ok, error]
                        error_reason:
                          type: string
                          enum: [timeout, provider_unconfigured, validation, downstream_5xx, other, none]
                        http_status:
                          type: integer
                        duration_ms:
                          type: integer
                        created_at:
                          type: string
                          format: date-time
                  limit:
                    type: integer
                  offset:
                    type: integer
                  next_offset:
                    type: integer
                    nullable: true
                    description: Next page offset, or null if last page
                  count:
                    type: integer
                    description: Number of items in current page

        '401':
          description: Unauthorized - missing or invalid API key

        '403':
          description: Forbidden - insufficient scopes (audit:read required)

        '400':
          description: Bad Request - invalid filter parameters
```

---

## Role-Based Access Control (RBAC)

**Scope-to-Role Mapping:**

| Role | Scopes | Preview | Execute | Audit |
|------|--------|---------|---------|-------|
| **viewer** | `actions:preview` | ✅ | ❌ | ❌ |
| **developer** | `actions:preview`, `actions:execute` | ✅ | ✅ | ❌ |
| **admin** | `actions:preview`, `actions:execute`, `audit:read` | ✅ | ✅ | ✅ |

**Enforcement:**
- Implemented via `@require_scopes` decorator in `src/auth/security.py`
- Returns 401 if no valid API key
- Returns 403 if API key lacks required scope

---

## Error Responses

### HTTP 401 Unauthorized

**Triggers:**
- Missing `Authorization` header
- Invalid Bearer token format
- API key not found in database
- API key revoked (`revoked_at IS NOT NULL`)

**Response:**
```json
{
  "detail": "Unauthorized"
}
```

---

### HTTP 403 Forbidden

**Triggers:**
- API key valid but lacks required scope
- Example: Developer tries to access GET /audit (requires `audit:read`)

**Response:**
```json
{
  "detail": "Forbidden"
}
```

---

### HTTP 400 Bad Request (Audit Endpoint)

**Triggers:**
- `limit` out of bounds (not 1-200)
- `offset` negative
- `status` not 'ok' or 'error'
- `from_date` or `to_date` malformed (not ISO8601)

**Response:**
```json
{
  "detail": "Invalid limit: must be between 1 and 200"
}
```

---

## OpenAPI Export

**Endpoint:** `GET /openapi.json`

**Access:** Public (no authentication required)

**Example:**
```bash
curl -s https://relay-production-f2a6.up.railway.app/openapi.json | jq '.components.securitySchemes'
```

**Result:**
```json
{
  "ApiKeyBearer": {
    "type": "http",
    "scheme": "bearer",
    "bearerFormat": "API-Key",
    "description": "API key authentication for Relay actions API..."
  }
}
```

---

## Backward Compatibility

### ⚠️ Breaking Change: Authentication Required

**Before Sprint 51:**
- `/actions/preview` and `/actions/execute` were **unauthenticated**
- Any client could call without credentials

**After Sprint 51:**
- Both endpoints require `Authorization: Bearer <api_key>` header
- Clients without API keys receive **401 Unauthorized**

**Migration Path:**
1. Create API keys for each workspace: `python scripts/api_keys_cli.py create-key --workspace <uuid> --role developer`
2. Update client code to include `Authorization` header
3. Test with `curl -H "Authorization: Bearer relay_sk_..." https://...`

**Rollback Plan:**
- Revert to pre-Sprint-51 commit
- Remove `@require_scopes` decorators from endpoints
- Clients can call without authentication again

---

## Documentation Updates

### 1. README.md (Not Yet Updated)

**TODO:** Add authentication section to main README:
```markdown
## Authentication

Relay uses API keys for authentication. Create a key with:

```bash
python scripts/api_keys_cli.py create-key --workspace <workspace_id> --role developer
```

Include in requests:
```bash
curl -H "Authorization: Bearer relay_sk_..." https://relay-production.../actions/preview
```

Roles:
- **viewer**: Preview only
- **developer**: Preview + execute
- **admin**: All + audit logs
```

---

### 2. API Reference (Not Yet Created)

**TODO:** Generate API reference docs from OpenAPI schema:
- Use Redoc or SwaggerUI
- Host at `/docs` endpoint (FastAPI auto-generates)
- Include authentication examples

---

## Testing

### OpenAPI Schema Validation ✅

**Test:** Fetch `/openapi.json` and verify structure

```bash
curl -s https://relay-production-f2a6.up.railway.app/openapi.json | \
  jq '.components.securitySchemes.ApiKeyBearer'
```

**Result:**
```json
{
  "type": "http",
  "scheme": "bearer",
  "bearerFormat": "API-Key",
  "description": "API key authentication for Relay actions API..."
}
```

✅ Security scheme present and correctly formatted

---

### Endpoint Security Enforcement ✅

**Test 1:** Preview without auth (should fail)
```bash
curl -si https://relay-production-f2a6.up.railway.app/actions/preview \
  -H "Content-Type: application/json" \
  -d '{"action":"webhook.save","params":{"url":"https://example.com","payload":{}}}'
```

**Result:**
```
HTTP/1.1 401 Unauthorized
{"detail":"Unauthorized"}
```

✅ Auth required as documented

---

**Test 2:** Audit with developer key (should fail with 403)
```bash
curl -si https://relay-production-f2a6.up.railway.app/audit \
  -H "Authorization: Bearer <developer_key>"
```

**Result:**
```
HTTP/1.1 403 Forbidden
{"detail":"Forbidden"}
```

✅ RBAC enforced as documented

---

## Related Files

| File | Changes | Status |
|------|---------|--------|
| `src/webapi.py` | Added custom `openapi()` function to inject security scheme | ✅ |
| `src/auth/security.py` | Implemented `@require_scopes` decorator | ✅ |
| `docs/SPRINT-51-SPEC.md` | Documented auth requirements | ✅ |
| `README.md` | Not yet updated with auth docs | ⏳ TODO |

---

## Metrics

**OpenAPI Schema Size:**
- Before: ~3.2 KB
- After: ~5.8 KB (+2.6 KB for security scheme + audit endpoint)

**Breaking Changes:** 1 (authentication required)
**New Endpoints:** 1 (`GET /audit`)
**New Security Schemes:** 1 (`ApiKeyBearer`)

---

## Conclusion

✅ **OpenAPI schema updated** with API key authentication
✅ **GET /audit endpoint documented** with admin-only access
✅ **RBAC scopes defined** (viewer, developer, admin)
✅ **Error responses documented** (401, 403, 400)
✅ **Breaking change acknowledged** (auth now required)
✅ **Ready for client integration** (OpenAPI export at `/openapi.json`)

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

*Report generated: 2025-10-07 04:20 UTC*
