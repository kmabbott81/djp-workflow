# Sprint 51-52 Backlog: Security & OAuth Implementation

**Version:** 1.0
**Date:** October 6, 2025
**Status:** Draft
**Related:** `docs/SPRINT-51-SPEC.md`

## Purpose

This backlog breaks down the Sprint 51 specification into actionable tickets for implementation. Each ticket includes acceptance criteria, dependencies, and effort estimates.

## Sprint 51: Authentication, Authorization & Audit (25 days)

### Phase 1: Database Setup

#### S51-001: Add Railway Postgres Add-on
**Type:** Infrastructure
**Priority:** P0 (Blocker)
**Effort:** 2 hours

**Description:**
Add Railway Postgres add-on to production environment and configure connection pooling.

**Acceptance Criteria:**
- [ ] Postgres add-on provisioned on Railway
- [ ] Database URL added to Railway environment variables
- [ ] Connection pool configured (min=2, max=10)
- [ ] Test connection from local development

**Dependencies:** None

---

#### S51-002: Create Database Migration Scripts
**Type:** Backend
**Priority:** P0 (Blocker)
**Effort:** 4 hours

**Description:**
Create Alembic migration scripts for all 4 tables: api_keys, audit_logs, rate_limits, oauth_tokens.

**Acceptance Criteria:**
- [ ] `migrations/001_initial_schema.sql` created
- [ ] All tables have indexes for query performance
- [ ] Foreign key constraints defined
- [ ] Migration tested on local Postgres instance

**Dependencies:** S51-001

---

#### S51-003: Implement Database Models
**Type:** Backend
**Priority:** P0 (Blocker)
**Effort:** 3 hours

**Description:**
Create SQLAlchemy models for all database tables.

**Acceptance Criteria:**
- [ ] `src/db/models.py` with ApiKey, AuditLog, RateLimit, OAuthToken models
- [ ] Type hints on all fields
- [ ] Relationships defined (e.g., ApiKey -> AuditLog via workspace_id)
- [ ] Unit tests for model validation

**Dependencies:** S51-002

---

#### S51-004: Seed Development Data
**Type:** Backend
**Priority:** P1
**Effort:** 2 hours

**Description:**
Create seed data script for local development and testing.

**Acceptance Criteria:**
- [ ] Script creates 1 test workspace
- [ ] Script creates 3 API keys (admin, editor, viewer roles)
- [ ] Script creates sample audit log entries
- [ ] Script is idempotent (safe to run multiple times)

**Dependencies:** S51-003

---

### Phase 2: API Key Management

#### S51-005: Implement API Key Creation Endpoint
**Type:** Backend
**Priority:** P0
**Effort:** 4 hours

**Description:**
Implement `POST /api/auth/keys` endpoint to create new API keys.

**Acceptance Criteria:**
- [ ] Endpoint generates keys in format `relay_sk_<16_random_chars>`
- [ ] Keys stored as bcrypt hashes (not plaintext)
- [ ] Only admin role can create keys
- [ ] Returns key_id, key (plaintext - only shown once), prefix, expires_at

**Dependencies:** S51-003

---

#### S51-006: Implement API Key Listing Endpoint
**Type:** Backend
**Priority:** P0
**Effort:** 2 hours

**Description:**
Implement `GET /api/auth/keys` endpoint to list all API keys for a workspace.

**Acceptance Criteria:**
- [ ] Returns list of keys (prefix, name, role, created_at, last_used_at, expires_at)
- [ ] Never returns key hashes or plaintext keys
- [ ] Filters by workspace_id from authenticated user
- [ ] Only admin and editor roles can list keys

**Dependencies:** S51-005

---

#### S51-007: Implement API Key Revocation Endpoint
**Type:** Backend
**Priority:** P0
**Effort:** 2 hours

**Description:**
Implement `DELETE /api/auth/keys/{key_id}` endpoint to revoke an API key.

**Acceptance Criteria:**
- [ ] Sets revoked_at timestamp (soft delete)
- [ ] Returns 404 if key_id not found
- [ ] Returns 403 if key belongs to different workspace
- [ ] Only admin role can revoke keys

**Dependencies:** S51-006

---

#### S51-008: Implement API Key Validation Endpoint
**Type:** Backend
**Priority:** P0
**Effort:** 3 hours

**Description:**
Implement `POST /api/auth/validate` endpoint to validate an API key.

**Acceptance Criteria:**
- [ ] Accepts Authorization: Bearer header
- [ ] Returns workspace_id, role, key_prefix if valid
- [ ] Returns 401 if key invalid, expired, or revoked
- [ ] Updates last_used_at timestamp
- [ ] Latency < 10ms (use database indexes)

**Dependencies:** S51-007

---

#### S51-009: Implement Auth Middleware
**Type:** Backend
**Priority:** P0
**Effort:** 5 hours

**Description:**
Create middleware to enforce authentication on protected endpoints.

**Acceptance Criteria:**
- [ ] Validates Authorization: Bearer header on all /api/* endpoints
- [ ] Adds workspace_id and role to request.state
- [ ] Returns 401 for missing/invalid keys
- [ ] Excludes /metrics, /ready, /version from auth
- [ ] Prometheus metrics: auth_requests_total, auth_failures_total

**Dependencies:** S51-008

---

### Phase 3: RBAC & Authorization

#### S51-010: Implement Role-Based Access Control
**Type:** Backend
**Priority:** P0
**Effort:** 4 hours

**Description:**
Add role checking to AuthMiddleware and create @require_role decorator.

**Acceptance Criteria:**
- [ ] AuthMiddleware checks role from database
- [ ] @require_role("admin") decorator for admin-only endpoints
- [ ] Returns 403 for insufficient permissions
- [ ] Prometheus metrics: auth_denied_total{role, endpoint}

**Dependencies:** S51-009

---

#### S51-011: Implement Workspace Isolation
**Type:** Backend
**Priority:** P0
**Effort:** 3 hours

**Description:**
Ensure all API queries filter by workspace_id to prevent cross-workspace access.

**Acceptance Criteria:**
- [ ] All database queries include workspace_id filter
- [ ] Integration tests verify cross-workspace access denied
- [ ] Audit logs record denied access attempts

**Dependencies:** S51-010

---

#### S51-012: Add Permission Checks to Actions Endpoints
**Type:** Backend
**Priority:** P0
**Effort:** 2 hours

**Description:**
Update /actions/execute and /actions/preview to check role permissions.

**Acceptance Criteria:**
- [ ] Viewer role cannot execute actions (403)
- [ ] Editor role can execute and preview actions
- [ ] Admin role has full access
- [ ] Permission denials logged to audit log

**Dependencies:** S51-011

---

### Phase 4: Audit Logging

#### S51-013: Implement Audit Log Middleware
**Type:** Backend
**Priority:** P0
**Effort:** 5 hours

**Description:**
Create middleware to capture all API requests and write to audit_logs table.

**Acceptance Criteria:**
- [ ] Captures request_id, actor, action, status, latency
- [ ] Excludes /metrics, /ready from audit logs
- [ ] Async write to database (non-blocking)
- [ ] Handles database write failures gracefully
- [ ] Write latency < 50ms

**Dependencies:** S51-003

---

#### S51-014: Implement Audit Query Endpoint
**Type:** Backend
**Priority:** P1
**Effort:** 4 hours

**Description:**
Implement `GET /api/audit` endpoint to query audit logs.

**Acceptance Criteria:**
- [ ] Supports filtering by date range, actor_id, action
- [ ] Pagination with cursor-based pagination
- [ ] Only admin role can query audit logs
- [ ] Query latency < 200ms (use database indexes)

**Dependencies:** S51-013

---

#### S51-015: Implement Audit Log Retention
**Type:** Backend
**Priority:** P2
**Effort:** 3 hours

**Description:**
Create daily job to delete audit logs older than 90 days.

**Acceptance Criteria:**
- [ ] Job runs daily at 2 AM UTC
- [ ] Deletes logs with timestamp < (NOW() - 90 days)
- [ ] Logs retention job execution to console
- [ ] Job is idempotent (safe to run multiple times)

**Dependencies:** S51-014

---

### Phase 5: Rate Limiting

#### S51-016: Implement Rate Limit Middleware
**Type:** Backend
**Priority:** P1
**Effort:** 6 hours

**Description:**
Create middleware to enforce rate limits using sliding window algorithm.

**Acceptance Criteria:**
- [ ] Rate limit by workspace_id + endpoint + 5min window
- [ ] Returns 429 with Retry-After header when limit exceeded
- [ ] Stores counters in rate_limits table
- [ ] Uses SELECT FOR UPDATE for accuracy
- [ ] Latency < 20ms

**Dependencies:** S51-003

---

#### S51-017: Configure Role-Based Rate Limits
**Type:** Backend
**Priority:** P1
**Effort:** 2 hours

**Description:**
Set rate limits per role: admin=1000, editor=100, viewer=50 req/5min.

**Acceptance Criteria:**
- [ ] Admin keys have 1000 req/5min limit
- [ ] Editor keys have 100 req/5min limit on /actions/execute
- [ ] Viewer keys have 50 req/5min limit on all endpoints
- [ ] System keys have unlimited access

**Dependencies:** S51-016

---

#### S51-018: Add Rate Limit Metrics
**Type:** Backend
**Priority:** P2
**Effort:** 2 hours

**Description:**
Add Prometheus metrics for rate limiting.

**Acceptance Criteria:**
- [ ] Metric: rate_limit_exceeded_total{workspace, endpoint}
- [ ] Metric: rate_limit_current{workspace, endpoint, window}
- [ ] Metrics visible in Grafana dashboard

**Dependencies:** S51-017

---

### Phase 6: Microsoft OAuth

#### S51-019: Register Microsoft OAuth App
**Type:** Infrastructure
**Priority:** P0
**Effort:** 1 hour

**Description:**
Register OAuth app in Azure AD and obtain client_id and client_secret.

**Acceptance Criteria:**
- [ ] App registered in Azure AD
- [ ] Redirect URI configured: https://relay-production-f2a6.up.railway.app/oauth/microsoft/callback
- [ ] Scopes requested: Mail.Send, Mail.ReadWrite, User.Read
- [ ] Client ID and secret added to Railway environment variables

**Dependencies:** None

---

#### S51-020: Implement Microsoft OAuth Authorize Endpoint
**Type:** Backend
**Priority:** P0
**Effort:** 3 hours

**Description:**
Implement `GET /oauth/microsoft/authorize` to redirect to Microsoft login.

**Acceptance Criteria:**
- [ ] Generates OAuth state parameter for CSRF protection
- [ ] Redirects to Microsoft consent screen
- [ ] Stores state in session/database for validation in callback

**Dependencies:** S51-019

---

#### S51-021: Implement Microsoft OAuth Callback Endpoint
**Type:** Backend
**Priority:** P0
**Effort:** 4 hours

**Description:**
Implement `GET /oauth/microsoft/callback` to exchange code for tokens.

**Acceptance Criteria:**
- [ ] Validates state parameter (CSRF protection)
- [ ] Exchanges authorization code for access + refresh tokens
- [ ] Stores tokens in oauth_tokens table (encrypted)
- [ ] Returns access_token, expires_at, email

**Dependencies:** S51-020

---

#### S51-022: Implement Microsoft OAuth Refresh
**Type:** Backend
**Priority:** P0
**Effort:** 3 hours

**Description:**
Implement `POST /oauth/microsoft/refresh` to refresh expired access tokens.

**Acceptance Criteria:**
- [ ] Uses refresh_token to obtain new access_token
- [ ] Updates oauth_tokens table with new tokens
- [ ] Returns new access_token and expires_at
- [ ] Handles refresh_token expiry gracefully

**Dependencies:** S51-021

---

#### S51-023: Update Microsoft Email Adapter
**Type:** Backend
**Priority:** P0
**Effort:** 4 hours

**Description:**
Update `microsoft.send_email` adapter to use OAuth tokens from database.

**Acceptance Criteria:**
- [ ] Queries oauth_tokens table for workspace_id + provider="microsoft"
- [ ] Uses access_token to send email via Microsoft Graph API
- [ ] Auto-refreshes token if expired (calls S51-022)
- [ ] Returns 200 on success (not 501)

**Dependencies:** S51-022

---

### Phase 7: Google OAuth

#### S51-024: Register Google OAuth App
**Type:** Infrastructure
**Priority:** P0
**Effort:** 1 hour

**Description:**
Register OAuth app in Google Cloud Console and obtain client_id and client_secret.

**Acceptance Criteria:**
- [ ] App registered in Google Cloud Console
- [ ] Redirect URI configured: https://relay-production-f2a6.up.railway.app/oauth/google/callback
- [ ] Scopes requested: gmail.send, calendar.events
- [ ] Client ID and secret added to Railway environment variables

**Dependencies:** None

---

#### S51-025: Implement Google OAuth Authorize Endpoint
**Type:** Backend
**Priority:** P0
**Effort:** 3 hours

**Description:**
Implement `GET /oauth/google/authorize` to redirect to Google consent screen.

**Acceptance Criteria:**
- [ ] Generates OAuth state parameter for CSRF protection
- [ ] Redirects to Google consent screen
- [ ] Stores state in session/database for validation in callback

**Dependencies:** S51-024

---

#### S51-026: Implement Google OAuth Callback Endpoint
**Type:** Backend
**Priority:** P0
**Effort:** 4 hours

**Description:**
Implement `GET /oauth/google/callback` to exchange code for tokens.

**Acceptance Criteria:**
- [ ] Validates state parameter (CSRF protection)
- [ ] Exchanges authorization code for access + refresh tokens
- [ ] Stores tokens in oauth_tokens table (encrypted)
- [ ] Returns access_token, expires_at, email

**Dependencies:** S51-025

---

#### S51-027: Implement Google OAuth Refresh
**Type:** Backend
**Priority:** P0
**Effort:** 3 hours

**Description:**
Implement `POST /oauth/google/refresh` to refresh expired access tokens.

**Acceptance Criteria:**
- [ ] Uses refresh_token to obtain new access_token
- [ ] Updates oauth_tokens table with new tokens
- [ ] Returns new access_token and expires_at
- [ ] Handles refresh_token expiry gracefully

**Dependencies:** S51-026

---

#### S51-028: Update Google Email Adapter
**Type:** Backend
**Priority:** P0
**Effort:** 4 hours

**Description:**
Update `google.send_email` adapter to use OAuth tokens from database.

**Acceptance Criteria:**
- [ ] Queries oauth_tokens table for workspace_id + provider="google"
- [ ] Uses access_token to send email via Gmail API
- [ ] Auto-refreshes token if expired (calls S51-027)
- [ ] Returns 200 on success (not 501)

**Dependencies:** S51-027

---

### Phase 8: Enhanced Observability

#### S51-029: Add Tempo Trace Integration
**Type:** Backend
**Priority:** P2
**Effort:** 3 hours

**Description:**
Integrate Grafana Tempo for distributed tracing.

**Acceptance Criteria:**
- [ ] TEMPO_URL environment variable configured
- [ ] X-Trace-Link header includes Tempo trace URL
- [ ] Trace context propagated to OAuth API calls
- [ ] Traces visible in Grafana Explore

**Dependencies:** None

---

#### S51-030: Create Auth Grafana Dashboard
**Type:** Observability
**Priority:** P2
**Effort:** 2 hours

**Description:**
Create Grafana dashboard for auth success/failure rates.

**Acceptance Criteria:**
- [ ] Dashboard shows auth_requests_total by role
- [ ] Dashboard shows auth_failures_total by reason
- [ ] Dashboard shows rate_limit_exceeded_total by workspace
- [ ] Dashboard includes 24h and 7d views

**Dependencies:** S51-010, S51-018

---

#### S51-031: Add Auth Failure Alerts
**Type:** Observability
**Priority:** P1
**Effort:** 2 hours

**Description:**
Create Prometheus alerts for auth failure rate > 5% over 5 minutes.

**Acceptance Criteria:**
- [ ] Alert fires when auth failure rate > 5% over 5min
- [ ] Alert includes workspace_id and failure reason
- [ ] Alert sent to PagerDuty/Slack (if configured)

**Dependencies:** S51-010

---

### Phase 9: Studio Updates

#### S51-032: Create AuthGuard Component
**Type:** Frontend
**Priority:** P0
**Effort:** 3 hours

**Description:**
Create React component to protect routes requiring authentication.

**Acceptance Criteria:**
- [ ] Checks for API key in localStorage
- [ ] Redirects to login page if no key found
- [ ] Validates key with backend on mount
- [ ] Shows loading spinner during validation

**Dependencies:** S51-009

---

#### S51-033: Add 501 Error Handling UX
**Type:** Frontend
**Priority:** P1
**Effort:** 2 hours

**Description:**
Improve UX for 501 Not Implemented errors from provider stubs.

**Acceptance Criteria:**
- [ ] Shows "Provider not configured" message
- [ ] Displays link to OAuth connection page
- [ ] Hides provider from action dropdown if not configured

**Dependencies:** None

---

#### S51-034: Add CSP Headers to Studio
**Type:** Frontend
**Priority:** P2
**Effort:** 2 hours

**Description:**
Add Content Security Policy headers with nonce support.

**Acceptance Criteria:**
- [ ] CSP meta tag in public/index.html
- [ ] Nonce added to inline scripts
- [ ] CSP blocks unsafe-inline and unsafe-eval
- [ ] Vercel deployment config updated

**Dependencies:** None

---

#### S51-035: Create API Key Management Page
**Type:** Frontend
**Priority:** P0
**Effort:** 5 hours

**Description:**
Create UI for managing API keys (create, list, revoke).

**Acceptance Criteria:**
- [ ] Page accessible at /settings/api-keys
- [ ] List all API keys with prefix, name, role, created_at
- [ ] Create new key form (name, role, expires_in_days)
- [ ] Revoke button with confirmation dialog
- [ ] Show plaintext key only once after creation

**Dependencies:** S51-005, S51-006, S51-007

---

#### S51-036: Create OAuth Integrations Page
**Type:** Frontend
**Priority:** P0
**Effort:** 4 hours

**Description:**
Create UI for connecting Microsoft and Google OAuth accounts.

**Acceptance Criteria:**
- [ ] Page accessible at /settings/integrations
- [ ] "Connect Microsoft" button redirects to /oauth/microsoft/authorize
- [ ] "Connect Google" button redirects to /oauth/google/authorize
- [ ] Shows connected accounts with email and status
- [ ] Disconnect button to revoke OAuth tokens

**Dependencies:** S51-020, S51-025

---

### Phase 10: Testing & Deployment

#### S51-037: Write Integration Tests for Auth
**Type:** Testing
**Priority:** P0
**Effort:** 6 hours

**Description:**
Write integration tests for API key creation, validation, and RBAC.

**Acceptance Criteria:**
- [ ] Test: Create API key as admin (200)
- [ ] Test: Create API key as viewer (403)
- [ ] Test: Validate valid key (200)
- [ ] Test: Validate expired key (401)
- [ ] Test: Validate revoked key (403)
- [ ] Test: Execute action as viewer (403)

**Dependencies:** S51-012

---

#### S51-038: Write Integration Tests for OAuth
**Type:** Testing
**Priority:** P0
**Effort:** 4 hours

**Description:**
Write integration tests for Microsoft and Google OAuth flows.

**Acceptance Criteria:**
- [ ] Test: Microsoft authorize redirects to MS login
- [ ] Test: Microsoft callback exchanges code for tokens
- [ ] Test: Google authorize redirects to Google consent
- [ ] Test: Google callback exchanges code for tokens

**Dependencies:** S51-023, S51-028

---

#### S51-039: Write E2E Tests for Studio Auth
**Type:** Testing
**Priority:** P1
**Effort:** 4 hours

**Description:**
Write Playwright E2E tests for Studio auth guard and API key management.

**Acceptance Criteria:**
- [ ] Test: Unauthenticated user redirected to login
- [ ] Test: Authenticated user can access protected routes
- [ ] Test: Admin can create/revoke API keys
- [ ] Test: OAuth connection buttons redirect correctly

**Dependencies:** S51-032, S51-035, S51-036

---

#### S51-040: Deploy to Staging and Run Smoke Tests
**Type:** Deployment
**Priority:** P0
**Effort:** 4 hours

**Description:**
Deploy Sprint 51 changes to Railway staging environment and run smoke tests.

**Acceptance Criteria:**
- [ ] Database migrations run successfully
- [ ] All endpoints return expected status codes
- [ ] OAuth flows work end-to-end
- [ ] No errors in logs during smoke test

**Dependencies:** S51-037, S51-038, S51-039

---

#### S51-041: Deploy to Production and Monitor
**Type:** Deployment
**Priority:** P0
**Effort:** 8 hours

**Description:**
Deploy Sprint 51 changes to Railway production and monitor for 24 hours.

**Acceptance Criteria:**
- [ ] Database migrations run successfully
- [ ] All smoke tests pass
- [ ] No errors in 24h monitoring window
- [ ] Auth failure rate < 1%
- [ ] P95 latency < 500ms

**Dependencies:** S51-040

---

#### S51-042: Generate Evidence Package
**Type:** Documentation
**Priority:** P0
**Effort:** 3 hours

**Description:**
Generate evidence package documenting Sprint 51 deployment and results.

**Acceptance Criteria:**
- [ ] Document: SPRINT-51-COMPLETE-YYYY-MM-DD.md
- [ ] Metrics: Auth success/failure rates, latencies, error logs
- [ ] Screenshots: API key management UI, OAuth integrations
- [ ] Commit references and PR links

**Dependencies:** S51-041

---

## Sprint 52: Performance & Scalability (Optional)

### S52-001: Add Redis Cache for Rate Limiting
**Type:** Backend
**Priority:** P1
**Effort:** 6 hours

**Description:**
Replace Postgres-based rate limiting with Redis for improved performance.

**Acceptance Criteria:**
- [ ] Redis connection pool configured
- [ ] Rate limit checks use Redis INCR with TTL
- [ ] Fallback to Postgres if Redis unavailable
- [ ] Latency < 5ms

---

### S52-002: Add Read Replica for Audit Logs
**Type:** Infrastructure
**Priority:** P2
**Effort:** 4 hours

**Description:**
Add Postgres read replica for audit log queries to reduce load on primary.

**Acceptance Criteria:**
- [ ] Read replica provisioned on Railway
- [ ] Audit query endpoint uses read replica
- [ ] Primary database handles writes only

---

### S52-003: Implement Token Rotation for OAuth
**Type:** Backend
**Priority:** P1
**Effort:** 4 hours

**Description:**
Automatically rotate OAuth tokens every 24 hours for improved security.

**Acceptance Criteria:**
- [ ] Daily job refreshes all tokens > 23h old
- [ ] Failed refreshes logged to audit log
- [ ] Users notified if refresh fails (re-auth required)

---

### S52-004: Add Workspace-Level Rate Limit Overrides
**Type:** Backend
**Priority:** P2
**Effort:** 5 hours

**Description:**
Allow customizing rate limits per workspace (e.g., premium workspaces get higher limits).

**Acceptance Criteria:**
- [ ] New table: rate_limit_overrides (workspace_id, endpoint, limit)
- [ ] Rate limit middleware checks overrides first
- [ ] Admin UI to set overrides

---

### S52-005: Add SAML/SSO Support
**Type:** Backend
**Priority:** P2
**Effort:** 10 hours

**Description:**
Add SAML 2.0 support for enterprise SSO integration.

**Acceptance Criteria:**
- [ ] SAML assertion validation
- [ ] Metadata endpoint for IdP configuration
- [ ] JIT (Just-In-Time) user provisioning

---

## Summary

**Sprint 51 Total:** 42 tickets, ~145 hours (25 days @ 6 hours/day)
**Sprint 52 Total:** 5 tickets, ~29 hours (5 days)

**Priority Breakdown:**
- P0 (Blocker): 28 tickets
- P1 (High): 9 tickets
- P2 (Medium): 10 tickets

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

*Backlog created: 2025-10-06 06:45 UTC*
