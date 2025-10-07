# Sprint 51 Phase 1 - Resume After Railway Postgres

**Purpose:** Paste-ready prompt to resume Sprint 51 Phase 1 after Railway Postgres is provisioned.

## Status Check

Before resuming, verify:
```bash
# 1. Railway Postgres provisioned
railway variables | grep DATABASE_URL
# Expected: DATABASE_URL=postgres://...

# 2. Branch still on sprint/51-phase1-secure-core
git branch --show-current
# Expected: sprint/51-phase1-secure-core

# 3. All commits pushed
git log --oneline -6
# Expected to see:
# 4bf501f S51 P1: Unit tests for RBAC, audit redaction, /audit filters & pagination
# 94d9045 S51 P1: GET /audit endpoint (admin-only) with filters + pagination
# 85b9891 S51 P1: Add OpenAPI security scheme and documentation
# 5f58fb3 S51 P1: Audit logging for preview/execute with redaction
# a88dc9a S51 P1: Auth middleware + scopes/RBAC (API-key + user sessions)
# f2e728a S51 P1: Alembic migrations + API key CLI + roles CLI
```

---

## Paste-Ready Resume Prompt

```
Resume Sprint 51 Phase 1 deployment (Steps 7-8).

Context:
- Steps 1-6 complete (migrations, CLI tools, auth, audit, GET /audit, unit tests)
- All code committed to branch: sprint/51-phase1-secure-core
- Railway Postgres now provisioned with DATABASE_URL set
- Evidence doc: docs/evidence/sprint-51/phase1/STEPS-5-6-COMPLETE.md

Task: Complete Step 7 (Railway deployment + migrations + smoke tests) and Step 8 (evidence + PR).

STEP 7 — RAILWAY DEPLOYMENT + MIGRATIONS

1. Apply Alembic migrations on Railway DB:
   railway run python -m alembic upgrade head

   Expected output:
   - Creates 4 ENUM types (actor_type_enum, role_enum, audit_status_enum, error_reason_enum)
   - Creates 3 tables (api_keys, roles, action_audit)
   - Shows "Running upgrade -> ce6ac882b60d"

2. Deploy backend to Railway:
   railway up --detach

   Wait for deployment to complete (~2-3 minutes).

3. Verify health endpoint:
   curl -s https://relay-production-f2a6.up.railway.app/_stcore/health | jq .

   Expected: {"status": "healthy"}

4. Create test API keys (admin and developer):
   TEST_WORKSPACE_ID="00000000-0000-0000-0000-000000000001"

   # Admin key
   railway run python scripts/api_keys_cli.py create-key --workspace $TEST_WORKSPACE_ID --role admin
   # Save output: ADMIN_KEY=relay_sk_...

   # Developer key
   railway run python scripts/api_keys_cli.py create-key --workspace $TEST_WORKSPACE_ID --role developer
   # Save output: DEV_KEY=relay_sk_...

5. Run production smoke tests:

   a) Test admin can read audit (empty at first):
   curl -si https://relay-production-f2a6.up.railway.app/audit \
     -H "Authorization: Bearer $ADMIN_KEY"
   # Expected: HTTP/1.1 200 OK, {"items":[],"limit":50,"offset":0,"next_offset":null,"count":0}

   b) Test developer can preview:
   PREV=$(curl -s https://relay-production-f2a6.up.railway.app/actions/preview \
     -H "Authorization: Bearer $DEV_KEY" \
     -H "Content-Type: application/json" \
     -d '{"action":"independent.webhook.save","params":{"url":"https://example.com","payload":{"test":"smoke"}}}')
   echo "$PREV" | jq .
   PID=$(echo "$PREV" | jq -r .preview_id)
   # Expected: preview_id present

   c) Test developer can execute:
   curl -si https://relay-production-f2a6.up.railway.app/actions/execute \
     -H "Authorization: Bearer $DEV_KEY" \
     -H "Content-Type: application/json" \
     -H "Idempotency-Key: smoke-test-$(date +%s)" \
     -d "{\"preview_id\":\"$PID\"}" | head -40
   # Expected: HTTP/1.1 200 OK, run_id present

   d) Test audit log populated:
   curl -s https://relay-production-f2a6.up.railway.app/audit \
     -H "Authorization: Bearer $ADMIN_KEY" | jq '.items | length'
   # Expected: >= 2 (preview + execute)

   e) Test audit filters work:
   curl -s https://relay-production-f2a6.up.railway.app/audit?status=ok \
     -H "Authorization: Bearer $ADMIN_KEY" | jq '.items[0].status'
   # Expected: "ok"

   f) Verify X-Request-ID headers:
   curl -si https://relay-production-f2a6.up.railway.app/actions/preview \
     -H "Authorization: Bearer $DEV_KEY" \
     -H "Content-Type: application/json" \
     -d '{"action":"independent.webhook.save","params":{"url":"https://example.com","payload":{}}}' | grep -i x-request-id
   # Expected: X-Request-ID: <uuid>

6. Check Railway logs for errors:
   railway logs | grep -i error | tail -20
   # Expected: No new 5xx errors

STEP 8 — EVIDENCE PACKAGE + PR

1. Generate smoke test evidence:
   Create: docs/evidence/sprint-51/phase1/PRODUCTION-SMOKE-TESTS.md
   Include:
   - Curl commands and outputs (mask API keys)
   - Audit query results
   - Health check status
   - Railway logs snippet (no errors)

2. Generate unit test results summary:
   pytest tests/test_sprint51_auth_audit.py -v --tb=short > docs/evidence/sprint-51/phase1/UNIT-TEST-RESULTS.txt
   Create: docs/evidence/sprint-51/phase1/UNIT-TEST-SUMMARY.md with summary

3. Generate OpenAPI changes summary:
   Create: docs/evidence/sprint-51/phase1/OPENAPI-CHANGES.md
   Document:
   - ApiKeyBearer security scheme added
   - /audit endpoint documented
   - Authentication requirements updated

4. Confirm no new metrics issues:
   Check Prometheus (if available):
   - Error rate ≤ 1%
   - No new 5xx errors
   - P95 latency < 500ms

5. Open pull request:
   gh pr create --title "Sprint 51 Phase 1: API Keys + RBAC + Audit Logging" --body "$(cat <<'EOF'
## Summary

Implements Sprint 51 Phase 1: Database-backed authentication, RBAC, and audit logging for Relay actions API.

## Changes

### Database Schema (Alembic migrations)
- **api_keys** table: Argon2 hashed API keys with workspace isolation and scopes
- **roles** table: User → Workspace → Role mapping for session auth
- **action_audit** table: Audit log for preview/execute with SHA256 redaction

### Authentication & Authorization
- API key authentication via `Authorization: Bearer relay_sk_<key>` header
- Argon2 constant-time verification for security
- `@require_scopes` decorator for endpoint protection
- Role-based scopes: viewer (preview), developer (preview+execute), admin (all+audit:read)

### Audit Logging
- Preview + Execute requests logged with redaction
- Stores: params_hash (SHA256), params_prefix64 (first 64 chars only)
- Never stores: full payloads, secrets, raw idempotency keys
- Bounded enums: status (ok|error), error_reason (timeout|validation|...)

### New Endpoints
- `GET /audit` (admin-only): Query audit logs with filters (provider, action_id, status, date range) and pagination

### CLI Tools
- `scripts/api_keys_cli.py`: Create/list/revoke API keys
- `scripts/roles_cli.py`: Add/list/remove user role assignments

## Testing

- ✅ 19 unit tests passed (auth, RBAC, audit redaction, /audit validation)
- ✅ Production smoke tests passed (preview, execute, audit query)
- ✅ All linting passed (ruff, black, pre-commit hooks)

## Security

- ✅ Argon2 constant-time API key verification
- ✅ Workspace isolation (all queries filter by workspace_id)
- ✅ Audit log redaction (no secrets stored)
- ✅ Bounded enums (database constraints)
- ✅ Parameterized SQL (no injection)

## Evidence

- [Steps 3-4 Complete](./docs/evidence/sprint-51/phase1/STEPS-3-4-COMPLETE.md)
- [Steps 5-6 Complete](./docs/evidence/sprint-51/phase1/STEPS-5-6-COMPLETE.md)
- [Production Smoke Tests](./docs/evidence/sprint-51/phase1/PRODUCTION-SMOKE-TESTS.md)
- [Unit Test Results](./docs/evidence/sprint-51/phase1/UNIT-TEST-SUMMARY.md)
- [OpenAPI Changes](./docs/evidence/sprint-51/phase1/OPENAPI-CHANGES.md)

## Rollback Plan

1. Revert branch: `git revert HEAD~6..HEAD`
2. Railway: Keep database (no data loss), redeploy previous commit
3. API keys remain valid but unused until re-deployment

## Checklist

- [x] Alembic migrations applied successfully
- [x] API keys CLI tested
- [x] Auth middleware enforces 401/403 correctly
- [x] Audit logs populated with redaction
- [x] GET /audit filters work
- [x] Unit tests pass (19 passed)
- [x] Production smoke tests pass
- [x] OpenAPI schema updated
- [x] No new 5xx errors in logs
- [ ] Code review approved

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
EOF
)"

6. Request code review and await approval.

---

Notes:
- All code already committed and pushed to sprint/51-phase1-secure-core
- Railway Postgres DATABASE_URL must be set before running migrations
- Test workspace ID can be any valid UUID for smoke tests
- Mask API keys in evidence documents (show only first 8 chars)
```

---

## Quick Verification Commands

After database provisioning, run these to confirm readiness:
```bash
# 1. Check DATABASE_URL exists
railway variables | grep DATABASE_URL

# 2. Test connection
railway run python -c "import os; print('DB URL:', os.getenv('DATABASE_URL')[:50])"

# 3. Verify migrations not yet applied
railway run python -m alembic current
# Expected: No current revision (empty)
```

Then paste the resume prompt above to continue.
