# Sprint 51 Specification: Authentication, Authorization & Audit

**Version:** 1.0
**Author:** System Architecture Team
**Date:** October 6, 2025
**Status:** Draft
**Predecessor:** Sprint 50 Day 1 (Security & Reliability Hardening)

## Executive Summary

Sprint 51 implements the remaining security and auditability features from Sprint 50 that require database infrastructure. This includes API key management, role-based access control, audit logging, rate limiting, and OAuth integrations for Microsoft and Google.

## Background

### What We Completed in Sprint 50 Day 1

Sprint 50 Day 1 successfully deployed three high-impact changes without database dependencies:

1. **Idempotency-first flow** - 24h replay window (PR #27)
2. **CORS header hardening** - Authorization header + observability headers
3. **Request tracing** - X-Request-ID on all responses

**Status:** ✅ DEPLOYED TO PRODUCTION (Railway, commit fd10548)

### What Remains for Sprint 51

All remaining Sprint 50 work requires **Postgres database** for:
- API key storage and validation
- Role-based access control (RBAC) tables
- Audit log persistence
- OAuth token storage and refresh

**Decision:** Defer database-backed work to Sprint 51 per "Option A" plan.

## Goals

1. **Authentication** - API key management with workspace isolation
2. **Authorization** - Role-based access control for actions and templates
3. **Audit** - Comprehensive audit logging with retention policies
4. **Rate Limiting** - Workspace-level request throttling
5. **OAuth Integration** - Microsoft Graph API and Google Workspace
6. **Observability** - Enhanced tracing with Tempo integration
7. **Studio Updates** - Auth guard, 501 error UX, CSP headers

## Scope

### In Scope (Sprint 51)

**Backend**
- ✅ Postgres database setup (Railway add-on)
- ✅ API key CRUD endpoints
- ✅ RBAC middleware and decorators
- ✅ Audit log service with retention
- ✅ Rate limiting middleware
- ✅ Microsoft OAuth flow (Graph API)
- ✅ Google OAuth flow (Gmail/Calendar)
- ✅ Tempo trace integration

**Frontend (Studio)**
- ✅ Auth guard component
- ✅ 501 error handling UX
- ✅ CSP headers and nonce support
- ✅ API key management UI

**Testing & Operations**
- ✅ Integration tests for auth flows
- ✅ Prometheus alerts for auth failures
- ✅ Database migration scripts
- ✅ Smoke tests for OAuth flows

### Out of Scope (Future Sprints)

- SAML/SSO integration (Sprint 52+)
- Multi-factor authentication (Sprint 53+)
- Workspace billing and usage limits (Sprint 54+)
- Advanced audit analytics/dashboards (Sprint 55+)

## Architecture

### Database Schema

**Table: `api_keys`**
```sql
CREATE TABLE api_keys (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id VARCHAR(255) NOT NULL,
    key_hash VARCHAR(255) NOT NULL UNIQUE,  -- bcrypt hash
    key_prefix VARCHAR(16) NOT NULL,         -- relay_sk_1234 (for display)
    name VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL,               -- admin, editor, viewer
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ,
    last_used_at TIMESTAMPTZ,
    revoked_at TIMESTAMPTZ,
    created_by VARCHAR(255),                 -- user/service that created key

    INDEX idx_workspace_id (workspace_id),
    INDEX idx_key_hash (key_hash),
    INDEX idx_expires_at (expires_at) WHERE revoked_at IS NULL
);
```

**Table: `audit_logs`**
```sql
CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id VARCHAR(255) NOT NULL,
    request_id UUID NOT NULL,                -- From X-Request-ID header
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    actor_type VARCHAR(50) NOT NULL,         -- api_key, oauth_user, system
    actor_id VARCHAR(255) NOT NULL,          -- key_prefix or user email
    action VARCHAR(100) NOT NULL,            -- action.execute, template.render, etc.
    resource_type VARCHAR(100) NOT NULL,     -- webhook, email, template
    resource_id VARCHAR(255),
    status VARCHAR(50) NOT NULL,             -- success, failed, denied
    error_reason TEXT,
    metadata JSONB,                          -- Full request/response details
    ip_address INET,
    user_agent TEXT,

    INDEX idx_workspace_timestamp (workspace_id, timestamp DESC),
    INDEX idx_request_id (request_id),
    INDEX idx_actor_id (actor_id),
    INDEX idx_timestamp (timestamp) -- For retention cleanup
);
```

**Table: `rate_limits`**
```sql
CREATE TABLE rate_limits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id VARCHAR(255) NOT NULL,
    window_start TIMESTAMPTZ NOT NULL,       -- Start of current rate limit window
    endpoint_pattern VARCHAR(255) NOT NULL,  -- /actions/execute, /api/templates, etc.
    request_count INTEGER NOT NULL DEFAULT 0,

    UNIQUE (workspace_id, window_start, endpoint_pattern),
    INDEX idx_workspace_window (workspace_id, window_start)
);
```

**Table: `oauth_tokens`**
```sql
CREATE TABLE oauth_tokens (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    workspace_id VARCHAR(255) NOT NULL,
    provider VARCHAR(50) NOT NULL,           -- microsoft, google
    user_id VARCHAR(255) NOT NULL,           -- Provider's user ID
    email VARCHAR(255) NOT NULL,
    access_token TEXT NOT NULL,              -- Encrypted at rest
    refresh_token TEXT,                      -- Encrypted at rest
    expires_at TIMESTAMPTZ NOT NULL,
    scopes TEXT[] NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    UNIQUE (workspace_id, provider, user_id),
    INDEX idx_workspace_provider (workspace_id, provider),
    INDEX idx_expires_at (expires_at)
);
```

### API Endpoints

#### Authentication

```
POST /api/auth/keys
Body: {name, role, expires_in_days?}
Headers: Authorization: Bearer <admin_key>
Response: {key_id, key: "relay_sk_...", prefix: "relay_sk_1234", expires_at}

GET /api/auth/keys
Headers: Authorization: Bearer <admin_key>
Response: [{key_id, prefix, name, role, created_at, last_used_at, expires_at}, ...]

DELETE /api/auth/keys/{key_id}
Headers: Authorization: Bearer <admin_key>
Response: {revoked_at}

POST /api/auth/validate
Headers: Authorization: Bearer <key>
Response: {workspace_id, role, key_prefix}
```

#### OAuth (Microsoft)

```
GET /oauth/microsoft/authorize
Query: ?redirect_uri=...
Response: Redirect to Microsoft login

GET /oauth/microsoft/callback
Query: ?code=...&state=...
Response: {access_token, refresh_token, expires_at, email}

POST /oauth/microsoft/refresh
Body: {refresh_token}
Response: {access_token, expires_at}
```

#### OAuth (Google)

```
GET /oauth/google/authorize
Query: ?redirect_uri=...&scopes=gmail,calendar
Response: Redirect to Google consent screen

GET /oauth/google/callback
Query: ?code=...&state=...
Response: {access_token, refresh_token, expires_at, email}

POST /oauth/google/refresh
Body: {refresh_token}
Response: {access_token, expires_at}
```

#### Audit Logs

```
GET /api/audit
Headers: Authorization: Bearer <admin_key>
Query: ?start_date=...&end_date=...&actor_id=...&action=...&limit=100
Response: {logs: [...], total, next_cursor}
```

### Middleware Stack (Updated)

```python
app.add_middleware(TelemetryMiddleware)        # Sprint 50 Day 1 ✅
app.add_middleware(AuthMiddleware)             # Sprint 51 - API key validation
app.add_middleware(RateLimitMiddleware)        # Sprint 51 - Workspace throttling
app.add_middleware(AuditLogMiddleware)         # Sprint 51 - Log all requests
app.add_middleware(CORSMiddleware)             # Existing
```

### RBAC Roles

| Role | Permissions |
|------|-------------|
| **admin** | Full access: Create API keys, manage workspace, execute all actions |
| **editor** | Execute actions, preview actions, render templates, read audit logs (own workspace) |
| **viewer** | Read-only: List actions, list templates, read audit logs (own workspace) |
| **system** | Internal: Used by background jobs, health checks, metrics scraping |

### Rate Limits

| Role | Endpoint | Limit |
|------|----------|-------|
| admin | All | 1000 req/5min |
| editor | /actions/execute | 100 req/5min |
| editor | /actions/preview | 200 req/5min |
| viewer | All | 50 req/5min |
| system | /metrics, /ready | Unlimited |

## Implementation Plan

### Phase 1: Database Setup (Days 1-2)

**Tasks:**
1. Add Railway Postgres add-on
2. Create database migration scripts (using Alembic)
3. Write seed data for development (test workspace + API keys)
4. Add connection pooling (asyncpg)
5. Update Railway environment variables

**Deliverables:**
- `migrations/001_initial_schema.sql`
- `src/db/connection.py` - Connection pool management
- `src/db/models.py` - SQLAlchemy models
- README update with database setup instructions

**Acceptance Criteria:**
- ✅ Postgres accessible from Railway production
- ✅ All 4 tables created with indexes
- ✅ Seed data inserted (1 test workspace, 3 API keys)
- ✅ Connection pool configured (min=2, max=10)

### Phase 2: API Key Management (Days 3-4)

**Tasks:**
1. Implement `POST /api/auth/keys` - Create API key
2. Implement `GET /api/auth/keys` - List API keys
3. Implement `DELETE /api/auth/keys/{key_id}` - Revoke API key
4. Implement `POST /api/auth/validate` - Validate API key
5. Write `AuthMiddleware` to enforce API key on protected endpoints
6. Add Prometheus metrics: `auth_requests_total`, `auth_failures_total`

**Deliverables:**
- `src/auth/keys.py` - API key CRUD logic
- `src/auth/middleware.py` - Auth middleware
- `src/auth/decorators.py` - `@require_role("admin")` decorator
- Integration tests for API key flows

**Acceptance Criteria:**
- ✅ API keys follow format `relay_sk_<16_random_chars>`
- ✅ Keys stored as bcrypt hashes (never plaintext)
- ✅ Middleware validates Authorization: Bearer header
- ✅ Invalid keys return 401 with error message
- ✅ Expired keys return 401 with "key expired" message
- ✅ Revoked keys return 403 with "key revoked" message

### Phase 3: RBAC & Authorization (Days 5-6)

**Tasks:**
1. Implement role-based access control in `AuthMiddleware`
2. Add `@require_role("admin")` decorator for admin-only endpoints
3. Add workspace isolation (keys can only access own workspace data)
4. Update `/actions/execute` to check role permissions
5. Add Prometheus metrics: `auth_denied_total{role, endpoint}`

**Deliverables:**
- `src/auth/rbac.py` - Role checker and decorators
- Updated middleware with role enforcement
- Integration tests for permission denial scenarios

**Acceptance Criteria:**
- ✅ Viewer role cannot execute actions (403)
- ✅ Editor role can execute but cannot create API keys (403)
- ✅ Admin role has full access
- ✅ Workspace isolation prevents cross-workspace access
- ✅ All permission denials logged to audit log

### Phase 4: Audit Logging (Days 7-8)

**Tasks:**
1. Implement `AuditLogMiddleware` to capture all requests
2. Implement `POST /internal/audit/log` - Write audit log entry
3. Implement `GET /api/audit` - Query audit logs
4. Add retention policy (delete logs > 90 days)
5. Add database indexes for efficient audit queries

**Deliverables:**
- `src/audit/middleware.py` - Audit log middleware
- `src/audit/service.py` - Audit log service
- `src/audit/retention.py` - Retention cleanup job
- Integration tests for audit log capture

**Acceptance Criteria:**
- ✅ All API requests logged (except /metrics, /ready)
- ✅ Logs include request_id, actor, action, status, latency
- ✅ Failed/denied requests logged with error_reason
- ✅ Audit query endpoint supports filtering by date/actor/action
- ✅ Retention job runs daily (delete logs > 90 days)

### Phase 5: Rate Limiting (Days 9-10)

**Tasks:**
1. Implement `RateLimitMiddleware` with sliding window algorithm
2. Use Postgres for rate limit counters (workspace_id + endpoint + window)
3. Return 429 Too Many Requests with Retry-After header
4. Add Prometheus metrics: `rate_limit_exceeded_total{workspace, endpoint}`
5. Add admin endpoint to view/reset rate limits

**Deliverables:**
- `src/ratelimit/middleware.py` - Rate limit middleware
- `src/ratelimit/service.py` - Rate limit counter logic
- Integration tests for rate limiting scenarios

**Acceptance Criteria:**
- ✅ Rate limits enforced per workspace + endpoint
- ✅ 429 response includes Retry-After header
- ✅ Rate limit counters persist in database
- ✅ Sliding window algorithm (5-minute windows)
- ✅ Admin keys have higher limits than editor/viewer

### Phase 6: Microsoft OAuth (Days 11-13)

**Tasks:**
1. Implement OAuth 2.0 authorization code flow for Microsoft
2. Register app in Azure AD (client_id, client_secret)
3. Implement `/oauth/microsoft/authorize` - Redirect to MS login
4. Implement `/oauth/microsoft/callback` - Exchange code for tokens
5. Implement `/oauth/microsoft/refresh` - Refresh access token
6. Update `microsoft.send_email` adapter to use OAuth tokens
7. Store tokens in `oauth_tokens` table (encrypted)

**Deliverables:**
- `src/oauth/microsoft.py` - OAuth flow implementation
- `src/actions/adapters/microsoft.py` - Updated adapter
- Environment variables: `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`
- Integration tests for OAuth flow

**Acceptance Criteria:**
- ✅ OAuth flow redirects to Microsoft login
- ✅ Callback exchanges code for access token + refresh token
- ✅ Tokens stored encrypted in database
- ✅ Refresh logic automatically renews expired tokens
- ✅ `microsoft.send_email` action returns 200 (not 501)

### Phase 7: Google OAuth (Days 14-16)

**Tasks:**
1. Implement OAuth 2.0 authorization code flow for Google
2. Register app in Google Cloud Console (client_id, client_secret)
3. Implement `/oauth/google/authorize` - Redirect to Google consent
4. Implement `/oauth/google/callback` - Exchange code for tokens
5. Implement `/oauth/google/refresh` - Refresh access token
6. Update `google.send_email` adapter to use OAuth tokens
7. Store tokens in `oauth_tokens` table (encrypted)

**Deliverables:**
- `src/oauth/google.py` - OAuth flow implementation
- `src/actions/adapters/google.py` - Updated adapter
- Environment variables: `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET`
- Integration tests for OAuth flow

**Acceptance Criteria:**
- ✅ OAuth flow redirects to Google consent screen
- ✅ Callback exchanges code for access token + refresh token
- ✅ Tokens stored encrypted in database
- ✅ Refresh logic automatically renews expired tokens
- ✅ `google.send_email` action returns 200 (not 501)

### Phase 8: Enhanced Observability (Days 17-18)

**Tasks:**
1. Add Tempo trace integration (environment: `TEMPO_URL`)
2. Update `TelemetryMiddleware` to build trace links
3. Add trace context propagation to OAuth requests
4. Add Grafana dashboard for auth/audit metrics
5. Add Prometheus alerts for auth failures

**Deliverables:**
- Updated `src/telemetry/middleware.py` with Tempo links
- `observability/templates/grafana-auth-dashboard.json`
- `observability/templates/alerts-auth.yml`

**Acceptance Criteria:**
- ✅ X-Trace-Link header includes Tempo trace URL
- ✅ OAuth requests include trace context headers
- ✅ Grafana dashboard shows auth success/failure rates
- ✅ Alert fires when auth failure rate > 5% over 5min

### Phase 9: Studio Updates (Days 19-21)

**Tasks:**
1. Create `AuthGuard` component (redirect to login if no API key)
2. Add 501 error handling UX (show "Provider not configured" message)
3. Add CSP headers with nonce support
4. Create API key management page in Studio
5. Add OAuth connection buttons (Connect Microsoft, Connect Google)

**Deliverables:**
- `studio/src/components/AuthGuard.tsx`
- `studio/src/pages/Settings/ApiKeys.tsx`
- `studio/src/pages/Settings/Integrations.tsx`
- Updated `studio/public/index.html` with CSP meta tag

**Acceptance Criteria:**
- ✅ Unauthenticated users redirected to login page
- ✅ 501 errors show friendly "Provider not available" message
- ✅ CSP headers block unsafe inline scripts
- ✅ API key management UI allows create/list/revoke keys
- ✅ OAuth connection buttons redirect to authorize endpoints

### Phase 10: Testing & Deployment (Days 22-25)

**Tasks:**
1. Write integration tests for auth flows
2. Write E2E tests for Studio auth guard
3. Run full test suite (unit + integration + E2E)
4. Deploy to Railway staging environment
5. Run smoke tests on staging
6. Deploy to Railway production
7. Monitor metrics for 24h
8. Generate evidence package

**Deliverables:**
- `tests/integration/test_auth.py`
- `tests/integration/test_oauth.py`
- `tests/e2e/studio/test_auth_guard.spec.ts`
- `SPRINT-51-COMPLETE-YYYY-MM-DD.md`

**Acceptance Criteria:**
- ✅ All tests passing (unit + integration + E2E)
- ✅ Smoke tests pass on staging
- ✅ Production deployment successful
- ✅ No errors in 24h monitoring window
- ✅ Evidence package generated with metrics

## Dependencies

### External Services

1. **Railway Postgres** - Database add-on ($10/month)
2. **Microsoft Azure AD** - OAuth app registration (free)
3. **Google Cloud Console** - OAuth app registration (free)
4. **Grafana Cloud Tempo** (optional) - Trace storage ($0-50/month)

### Python Packages

```txt
asyncpg==0.30.0           # Async Postgres driver
alembic==1.13.0           # Database migrations
sqlalchemy==2.0.30        # ORM
bcrypt==4.2.0             # Password hashing for API keys
cryptography==43.0.0      # Token encryption at rest
msal==1.31.0              # Microsoft Authentication Library
google-auth==2.35.0       # Google OAuth library
google-auth-oauthlib==1.2.1
```

### Studio (TypeScript/React)

```json
{
  "@microsoft/msal-react": "^2.1.0",
  "react-oauth2-code-pkce": "^1.20.0"
}
```

## Timeline

**Total Duration:** 25 days (5 weeks)

| Phase | Days | Status |
|-------|------|--------|
| Database Setup | 1-2 | Pending |
| API Key Management | 3-4 | Pending |
| RBAC & Authorization | 5-6 | Pending |
| Audit Logging | 7-8 | Pending |
| Rate Limiting | 9-10 | Pending |
| Microsoft OAuth | 11-13 | Pending |
| Google OAuth | 14-16 | Pending |
| Enhanced Observability | 17-18 | Pending |
| Studio Updates | 19-21 | Pending |
| Testing & Deployment | 22-25 | Pending |

**Milestones:**
- Day 10: Backend auth/audit complete
- Day 16: OAuth integrations complete
- Day 21: Full-stack feature complete
- Day 25: Production deployment validated

## Risks & Mitigations

### Risk 1: Database Performance

**Risk:** Audit log table grows quickly, slowing queries.

**Mitigation:**
- Add PostgreSQL partitioning by month on `timestamp` column
- Use time-series retention (delete > 90 days)
- Add read replica for audit queries (if needed)

### Risk 2: OAuth Token Security

**Risk:** Access tokens stored in database could leak.

**Mitigation:**
- Encrypt tokens at rest using `cryptography.fernet`
- Store encryption key in Railway secret (not in code)
- Implement token rotation every 24h

### Risk 3: Rate Limiting Accuracy

**Risk:** High concurrency could cause rate limit miscounts.

**Mitigation:**
- Use Postgres `SELECT FOR UPDATE` with row-level locking
- Implement sliding window algorithm (not fixed window)
- Add Redis cache layer in Sprint 52 if needed

### Risk 4: OAuth App Approval

**Risk:** Microsoft/Google may take 1-2 weeks to approve OAuth apps.

**Mitigation:**
- Submit OAuth app registration forms at start of sprint
- Use test/development apps for initial implementation
- Plan production app approval as non-blocking task

### Risk 5: Migration Complexity

**Risk:** Database migrations on production could cause downtime.

**Mitigation:**
- Write idempotent migration scripts
- Test migrations on staging environment first
- Use Railway's built-in backup/restore before migration
- Plan migration during low-traffic window (weekends)

## Success Criteria

### Functional Requirements

- ✅ API keys can be created, listed, revoked by admin role
- ✅ RBAC enforces role permissions (admin, editor, viewer)
- ✅ Audit logs capture all API requests with metadata
- ✅ Rate limiting prevents abuse (429 responses with Retry-After)
- ✅ Microsoft OAuth flow works end-to-end (send_email action)
- ✅ Google OAuth flow works end-to-end (send_email action)
- ✅ Studio auth guard redirects unauthenticated users
- ✅ Studio API key management UI functional

### Non-Functional Requirements

- ✅ Authentication latency < 10ms (API key validation)
- ✅ Audit log write latency < 50ms (async writes)
- ✅ Rate limit check latency < 20ms (Postgres + caching)
- ✅ OAuth flows complete in < 5 seconds
- ✅ Database queries use indexes (no full table scans)
- ✅ All endpoints return < 500ms P95 latency

### Operational Requirements

- ✅ Database migrations automated via Alembic
- ✅ Prometheus metrics for auth/audit/rate_limit
- ✅ Grafana dashboards for auth success/failure rates
- ✅ Alerts for auth failure rate > 5% over 5min
- ✅ Retention job runs daily (cleanup logs > 90 days)

## Rollback Plan

If critical issues arise during Sprint 51 deployment:

```bash
# Step 1: Revert backend code
cd C:\Users\kylem\openai-agents-workflows-2025.09.28-v1
git checkout main
git pull
railway up

# Step 2: Disable auth enforcement (feature flag)
railway variables set AUTH_ENABLED=false

# Step 3: Monitor for 15 minutes
railway logs
curl https://relay-production-f2a6.up.railway.app/ready

# Step 4: If database corrupted, restore from backup
# (Use Railway web UI: Database > Backups > Restore)

# Step 5: Re-enable Sprint 50 Day 1 baseline
railway variables set AUTH_ENABLED=false
railway variables set ACTIONS_ENABLED=true
```

## Open Questions

1. **Token Encryption Key Management**: Should we use Railway secrets or AWS Secrets Manager?
   - **Recommendation**: Railway secrets (simpler, no AWS dependency)

2. **Audit Log Retention**: 90 days sufficient, or need 1 year for compliance?
   - **Recommendation**: Start with 90 days, add configurable retention in Sprint 52

3. **OAuth Scopes**: Which Microsoft Graph / Google Workspace scopes do we need?
   - **Microsoft**: `Mail.Send`, `Mail.ReadWrite`, `User.Read`
   - **Google**: `https://www.googleapis.com/auth/gmail.send`, `https://www.googleapis.com/auth/calendar`

4. **Rate Limit Overrides**: Should we allow per-workspace rate limit customization?
   - **Recommendation**: Sprint 52 feature (add `rate_limit_overrides` table)

## References

- Sprint 50 Day 1 Evidence: `SPRINT-50-DAY1-COMPLETE-2025-10-06.md`
- Phase B Deployment: `PHASE-B-COMPLETE-2025-10-06.md`
- Sprint 50 Day 1 PR: https://github.com/kmabbott81/djp-workflow/pull/27
- Microsoft Graph API Docs: https://learn.microsoft.com/en-us/graph/
- Google OAuth 2.0 Docs: https://developers.google.com/identity/protocols/oauth2

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

*Spec authored: 2025-10-06 06:30 UTC*
