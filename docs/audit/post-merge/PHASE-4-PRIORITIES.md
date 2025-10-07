# Phase 4 Priorities & Roadmap Alignment

**Sprint 53+ Planning**
**Date:** October 7, 2025
**Vision Reference:** RELAY_VISION_2025.md

---

## Executive Summary

With Sprint 51-52 completing platform hardening and operational excellence, **Phase 4 (Sprint 53+)** shifts focus to **product-market love** and **developer platform** foundations. The goal is to complete the vertical slice from "intent → action" while preparing for business viability in Sprints 53-56.

**Key Principle:** **Stability is now a competitive advantage.** With CI/CD, backups, observability, and security hardening in place, we can now iterate quickly on product features without operational firefighting.

---

## Roadmap Context

### Where We Are (Post-Sprint 52)

**Completed:**
✅ Core API (FastAPI with health, metrics, tracing)
✅ Actions framework (preview/confirm workflow, idempotency, audit logging)
✅ Auth & RBAC (API keys with Argon2, roles: admin/developer/viewer)
✅ Rate limiting (Redis + in-process fallback, per-workspace isolation)
✅ Security headers (HSTS, CSP, referrer policy, MIME protection)
✅ Webhook signing (HMAC-SHA256 with comprehensive docs)
✅ CI/CD pipeline (deployments, migrations, smoke tests, rollback)
✅ Database backups (daily backups, monthly restore drills)
✅ Observability (SLOs, Prometheus alerts, Grafana dashboards)
✅ Provider adapters: Independent (webhook)

**Platform Health:** 🟢 **89%** (Security 95%, Reliability 90%, Observability 90%, Docs 95%, Product 75%)

### Where We're Going (Phase 4 - Sprints 53-56)

**Phase I Goal:** Ship vertical slice, prove retention, remove obvious scale blockers

**KPI Targets (Sprints 49B-52):**
- 30-day retention ≥ 40% for beta devs
- Time-to-first-action < 3 minutes
- P95 action latency < 1.2s

**KPI Targets (Sprints 53-56):**
- $50-100k ARR
- ≥10 design-partner orgs
- <1% weekly incident rate

---

## Phase 4 Priorities (Sprint 53-56)

### 🎯 Priority 1: Complete Vertical Slice (Sprint 53-54)

**Goal:** Finish the "intent → action" user journey for beta developers

#### 1A. Chat MVP (Studio `/chat` Endpoint)

**Why:** Core UX for intent → action conversion
**Effort:** M (6-8 hours)
**Risk:** Low

**Deliverables:**
- `/api/chat` endpoint with streaming support
- Message history per session/workspace
- Intent extraction → action suggestion flow
- Integration with actions preview/confirm workflow
- Test coverage for chat session management

**Acceptance Criteria:**
- User sends text intent → receives action suggestion
- User confirms action → executes via existing `/actions/execute`
- Session history persisted (last 50 messages per workspace)
- Streaming response with Server-Sent Events (SSE)

**Dependencies:** None (actions framework already exists)

#### 1B. OAuth Scaffolds (Google & GitHub)

**Why:** Enable provider-specific actions (Gmail, Calendar, GitHub repos, etc.)
**Effort:** L (12-16 hours for both)
**Risk:** Medium (OAuth flows can be tricky)

**Deliverables:**
- OAuth 2.0 authorization code flow for Google
- OAuth 2.0 authorization code flow for GitHub
- Token storage with encryption (per workspace)
- Token refresh automation
- Scopes configuration per provider
- Admin UI for OAuth consent screens

**Acceptance Criteria:**
- User initiates OAuth flow → redirected to provider
- User grants consent → tokens stored encrypted in database
- Actions use stored tokens for API calls
- Token refresh happens automatically before expiry
- Revocation support (user can disconnect)

**Dependencies:**
- Database schema for OAuth tokens
- Encryption key management (env variable or KMS)

#### 1C. Provider Adapters: Microsoft & Google

**Why:** Expand from webhook-only to real integrations
**Effort:** XL (20-24 hours)
**Risk:** Medium (API complexity, error handling)

**Deliverables:**
- **Microsoft adapter:** Outlook (send email, get inbox), Teams (send message), Calendar (create event)
- **Google adapter:** Gmail (send email, get inbox), Chat (send message), Calendar (create event)
- Adapter interface standardization
- Error handling and retry logic
- Rate limit respect (provider-side)
- Test coverage for each action type

**Acceptance Criteria:**
- User executes "Send email via Outlook" → email sent successfully
- User executes "Create calendar event" → event created in Google Calendar
- API errors handled gracefully with user-friendly messages
- Provider rate limits respected (exponential backoff)

**Dependencies:**
- OAuth tokens (1B)
- Provider API credentials (dev accounts)

---

### 🎯 Priority 2: Developer Platform Foundations (Sprint 53-54)

**Goal:** Enable beta developers to build on Relay

#### 2A. OpenAPI SDK Generation (JS/Python)

**Why:** Enable third-party integrations
**Effort:** S (4-6 hours)
**Risk:** Low

**Deliverables:**
- Automated SDK generation from OpenAPI spec
- Published NPM package (`@relay/sdk-js`)
- Published PyPI package (`relay-sdk`)
- Example apps (React + FastAPI)
- SDK documentation with code samples

**Acceptance Criteria:**
- Developers can `npm install @relay/sdk-js` or `pip install relay-sdk`
- All API endpoints accessible via SDK
- TypeScript types included (JS SDK)
- Authentication helper (API key injection)

**Dependencies:** None (OpenAPI spec already exists)

#### 2B. Postman Collection & Examples

**Why:** Lower barrier to API exploration
**Effort:** S (2-4 hours)
**Risk:** Low

**Deliverables:**
- Postman collection with all endpoints
- Environment variables template
- Example requests for each action type
- Published to Postman Public Workspace

**Acceptance Criteria:**
- Developers can import collection → test API immediately
- All endpoints documented with examples
- Environment variables clearly labeled

**Dependencies:** None

---

### 🎯 Priority 3: Business Viability Prep (Sprint 55-56)

**Goal:** Prepare for monetization and design-partner onboarding

#### 3A. Billing Scaffolds (Stripe Integration)

**Why:** Enable paid tiers (Pro, Team, Enterprise)
**Effort:** L (12-16 hours)
**Risk:** Medium (payment flows require careful testing)

**Deliverables:**
- Stripe customer creation per org
- Subscription management (create, update, cancel)
- Usage tracking (action executions per workspace)
- Invoice generation (seat + usage)
- Webhook handling for subscription events
- Admin UI for billing management

**Acceptance Criteria:**
- User creates org → Stripe customer created
- User upgrades to Pro → subscription started
- Monthly invoice generated with seat + usage charges
- User cancels → subscription ends gracefully

**Dependencies:**
- Stripe account and API keys
- Org/workspace database schema extensions

#### 3B. SSO (OIDC) - Basic Implementation

**Why:** Enterprise requirement for design partners
**Effort:** M (8-10 hours)
**Risk:** Medium (integration complexity)

**Deliverables:**
- OIDC authorization code flow
- Support for generic OIDC providers (Okta, Auth0, Azure AD)
- User provisioning on first login
- Admin UI for SSO configuration

**Acceptance Criteria:**
- Admin configures SSO with OIDC metadata
- User initiates login → redirected to IdP
- User authenticates → auto-provisioned in Relay
- User role mapping from IdP claims

**Dependencies:**
- OIDC library (Python: `authlib` or `python-jose`)

#### 3C. Audit Export API

**Why:** Enterprise compliance requirement
**Effort:** S (4-6 hours)
**Risk:** Low

**Deliverables:**
- `/api/audit/export` endpoint (CSV/JSON)
- Date range filtering
- Workspace/user filtering
- Pagination for large exports
- Admin-only access (RBAC enforcement)

**Acceptance Criteria:**
- Admin requests audit export → receives CSV/JSON
- Export includes all audit events for specified date range
- Large exports paginated (stream response)

**Dependencies:** None (audit logging already exists)

---

### 🎯 Priority 4: Scale Posture (Sprint 56)

**Goal:** Remove obvious scale blockers before ramping beta traffic

#### 4A. Production Postgres Migration

**Why:** Managed database with better reliability than Railway default
**Effort:** M (6-8 hours)
**Risk:** Medium (migration downtime)

**Deliverables:**
- Railway Postgres Pro plan or external managed Postgres (Neon, Supabase)
- Connection pooling (PgBouncer)
- Read replicas for reporting queries
- Migration plan with rollback

**Acceptance Criteria:**
- Database migrated with zero data loss
- Downtime < 5 minutes
- Connection pooling active (verify via metrics)
- Read replicas serving /audit queries

**Dependencies:**
- Backup/restore validation (already done in Sprint 51)

#### 4B. Regional Replicas (US-East + US-West)

**Why:** Reduce latency for West Coast users
**Effort:** L (12-16 hours)
**Risk:** High (multi-region complexity)

**Deliverables:**
- Railway deployments in us-east-1 and us-west-2
- GeoDNS routing (Cloudflare or Route53)
- Database replication (primary in us-east, replica in us-west)
- Region-aware session affinity

**Acceptance Criteria:**
- West Coast users see P95 latency < 200ms (down from ~500ms)
- Database writes replicate to us-west within 1s
- No stale reads for critical operations (use primary for writes)

**Dependencies:**
- Production Postgres with replication support (4A)

#### 4C. Blue/Green Deployment Support

**Why:** Zero-downtime deployments
**Effort:** M (6-8 hours)
**Risk:** Medium (requires traffic switching logic)

**Deliverables:**
- CI/CD workflow update for blue/green
- Health check validation before traffic switch
- Smoke tests run against new deployment
- Automatic rollback on smoke test failure

**Acceptance Criteria:**
- Deploy to "green" environment → runs smoke tests
- Smoke tests pass → switch traffic to green
- Smoke tests fail → rollback to blue, alert team

**Dependencies:**
- CI/CD pipeline (already exists from Sprint 51)

---

## Priority Matrix

| Priority | Sprint | Effort | Risk | Impact | Dependencies |
|----------|--------|--------|------|--------|--------------|
| **1A. Chat MVP** | 53 | M | Low | High | None |
| **1B. OAuth Scaffolds** | 53 | L | Med | High | DB schema |
| **1C. Provider Adapters** | 54 | XL | Med | High | OAuth |
| **2A. SDK Generation** | 53 | S | Low | Med | None |
| **2B. Postman Collection** | 53 | S | Low | Low | None |
| **3A. Billing Scaffolds** | 55 | L | Med | High | Stripe account |
| **3B. SSO (OIDC)** | 55 | M | Med | High | OIDC library |
| **3C. Audit Export** | 55 | S | Low | Med | None |
| **4A. Production Postgres** | 56 | M | Med | High | Backup/restore |
| **4B. Regional Replicas** | 56 | L | High | Med | 4A |
| **4C. Blue/Green Deploys** | 56 | M | Med | Med | CI/CD pipeline |

**Effort Legend:** S (2-6h), M (6-10h), L (10-16h), XL (16-24h)
**Risk Legend:** Low (straightforward), Med (some unknowns), High (complex integration)

---

## Recommended Sprint Breakdown

### Sprint 53: Developer Platform Core

**Goal:** Complete vertical slice + enable external developers

**Deliverables:**
- ✅ Chat MVP (1A)
- ✅ OAuth Scaffolds - Google & GitHub (1B)
- ✅ SDK Generation - JS/Python (2A)
- ✅ Postman Collection (2B)

**Total Effort:** ~30-40 hours
**KPI Target:** Time-to-first-action < 3 minutes

### Sprint 54: Provider Expansion

**Goal:** Real integrations beyond webhooks

**Deliverables:**
- ✅ Microsoft Adapter - Outlook, Teams, Calendar (1C)
- ✅ Google Adapter - Gmail, Chat, Calendar (1C)
- ✅ Runbook Documentation (complete for all alerts)
- ✅ Load Testing (100 RPS baseline validation)

**Total Effort:** ~30-36 hours
**KPI Target:** P95 action latency < 1.2s

### Sprint 55: Business Viability

**Goal:** Monetization and enterprise readiness

**Deliverables:**
- ✅ Billing Scaffolds - Stripe Integration (3A)
- ✅ SSO (OIDC) - Basic Implementation (3B)
- ✅ Audit Export API (3C)
- ✅ Template Marketplace v0.1 (curated templates)

**Total Effort:** ~30-38 hours
**KPI Target:** ≥10 design-partner orgs signed

### Sprint 56: Scale Posture

**Goal:** Remove scale blockers

**Deliverables:**
- ✅ Production Postgres Migration (4A)
- ✅ Regional Replicas - US-East + US-West (4B)
- ✅ Blue/Green Deployment Support (4C)
- ✅ Error Budget Automation

**Total Effort:** ~30-40 hours
**KPI Target:** <1% weekly incident rate

---

## What We're NOT Doing (and Why)

### ❌ Autonomous Actions (Autopilot)

**Why Deferred:** Requires policy engine and trust UX (Sprints 89-94)
**Risk:** Premature automation without proper guardrails
**Alternative:** Focus on preview→confirm workflow for now

### ❌ Multi-Cloud Portability

**Why Deferred:** Layer 1 (Railway/Vercel) sufficient through Sprint 55
**Risk:** Premature optimization before product-market fit
**Alternative:** Stay on managed platforms for speed

### ❌ Vertical Packs (Sales, Support, Finance)

**Why Deferred:** Requires design-partner feedback first (Sprints 61-68)
**Risk:** Building without customer validation
**Alternative:** Start with generic actions, learn from beta users

### ❌ Async Orchestration (Durable Jobs, Sagas)

**Why Deferred:** Current synchronous actions sufficient for MVP (Sprints 69-74)
**Risk:** Complexity before demand
**Alternative:** Add job queue only when latency requires it

---

## Success Metrics

### Sprint 53-54: Product-Market Love

**Retention:**
- 30-day retention ≥ 40% for beta devs

**Engagement:**
- Time-to-first-action < 3 minutes
- Median actions per developer ≥ 5/week

**Performance:**
- P95 action latency < 1.2s
- Error rate < 1%

### Sprint 55-56: Business Viability

**Revenue:**
- $50-100k ARR (assumes ~10-20 paying orgs at $5k/year each)

**Customers:**
- ≥10 design-partner orgs
- ≥50 beta developers

**Reliability:**
- <1% weekly incident rate
- Uptime ≥ 99.9%

---

## Risk Mitigation

### Risk 1: OAuth Integration Complexity

**Mitigation:**
- Start with Google OAuth (most common)
- Use proven libraries (`authlib` for Python)
- Test with personal accounts before design partners

### Risk 2: Provider API Rate Limits

**Mitigation:**
- Implement exponential backoff in all adapters
- Add rate limit monitoring (Prometheus metrics)
- Document provider-specific limits in docs

### Risk 3: Multi-Region Latency

**Mitigation:**
- Start with single region (us-east-1)
- Add us-west-2 only after baseline validated
- Use geoDNS to route traffic intelligently

### Risk 4: Billing Complexity

**Mitigation:**
- Start with seat-based pricing (simpler than usage)
- Add usage metering incrementally
- Test with Stripe test mode extensively

---

## Conclusion

**Phase 4 (Sprint 53-56) Strategic Focus:**

1. **Complete the vertical slice:** Chat MVP + OAuth + Provider adapters
2. **Enable developer platform:** SDKs, Postman, documentation
3. **Prepare for monetization:** Billing, SSO, audit export
4. **Remove scale blockers:** Production DB, regional replicas, blue/green deploys

**Key Decision Point:** After Sprint 54, evaluate beta developer retention. If ≥ 40%, proceed with billing (Sprint 55). If < 40%, pivot to product improvements before monetization.

**Next Milestone:** $100k ARR with ≥10 design-partner orgs by end of Sprint 56

---

**Status:** 📋 Ready for Sprint 53 Planning
**Owner:** Product + Platform Team
**Next Review:** End of Sprint 54 (post-vertical slice completion)
