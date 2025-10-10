# Sprint 53: Provider Vertical Slice & Infrastructure Completion

**Branch:** `sprint/53-provider-vertical-slice`
**Start Date:** October 8, 2025
**Target Duration:** 10-12 days
**Status:** 🟢 Ready to Start

---

## Executive Summary

Sprint 53 focuses on **completing the Layer 1 infrastructure** and implementing **one complete provider adapter (Google or Microsoft)** as a vertical slice pattern for future providers. This sprint transforms the Actions API from a foundation with stubs into a **fully functional integration platform**.

**Key Deliverables:**
1. ✅ Deploy Redis to Railway (distributed state management)
2. ✅ Verify & fix Studio → Backend integration
3. ✅ Complete ONE provider adapter end-to-end (OAuth + API + Tests)
4. ✅ Generate SDK (JS/Python from OpenAPI)

---

## Sprint 52 Completion Status

### ✅ What Sprint 52 Delivered

From validation audit (`docs/status/SPRINT-52-VALIDATION-AUDIT.md`):

**Complete & Deployed:**
- Actions API foundation (`/actions`, `/actions/preview`, `/actions/execute`)
- Webhook action (independent provider) - fully functional
- Prometheus metrics + Grafana dashboard (local)
- Audit logging + Request tracing
- Railway production deployment (stable)
- Branch protection + CI stabilization (1313 tests passing, 54 quarantined)

**Infrastructure:**
- ✅ Railway backend (Python 3.11, Uvicorn, PostgreSQL)
- ✅ Docker Compose (local dev with Redis, workers)
- ⚠️ Redis: Local only (not in Railway production)
- ⚠️ Studio UI: Deployed to Vercel (integration unclear)

**Provider Adapters:**
- ✅ Independent (webhook) - Complete
- ❌ Microsoft - Stub only (no code)
- ❌ Google - Stub only (no code)
- ❌ Apple Bridge - Not started

### 📊 Audit Key Findings

**Production Performance:**
- `/actions` p50 latency: <5ms ✅
- `/actions/execute` p50: ~285ms ✅ (under 1.2s SLO)
- Webhook execution: 1 success, 1 error (needs investigation)

**Gaps Identified:**
1. Redis not deployed to Railway → rate limiting may not work correctly
2. Microsoft/Google adapters are placeholders → no OAuth, no API calls
3. Studio → Backend integration not verified
4. SDK generation not started

---

## Sprint 53 Objectives

### Priority 1: Infrastructure Completion (Days 1-2)

#### 1.1 Deploy Redis to Railway
**Why:** Distributed rate limiting, session storage, queue management

**Tasks:**
- [ ] Add Redis service to Railway project
- [ ] Configure environment variables (`REDIS_URL`)
- [ ] Update backend to use Railway Redis
- [ ] Test rate limiting in production
- [ ] Monitor Redis metrics in Grafana

**Acceptance Criteria:**
- Production backend connects to Railway Redis
- Rate limiting works across multiple instances
- Prometheus metrics show Redis connection health

#### 1.2 Verify Studio Integration
**Why:** Ensure UI → Backend API connection works

**Tasks:**
- [ ] Find Vercel deployment URL
- [ ] Check `.env.production` configuration
- [ ] Test Studio → Railway API calls
- [ ] Fix CORS if needed
- [ ] Test actions flow end-to-end from UI

**Acceptance Criteria:**
- Studio can list actions from production backend
- Preview flow works from UI
- Execute flow works from UI

#### 1.3 Fix Webhook Error
**Why:** 50% error rate on webhook executions

**Tasks:**
- [ ] Investigate `HTTPStatusError` in webhook execution
- [ ] Check webhook.site endpoint configuration
- [ ] Verify HMAC signature if required
- [ ] Add better error handling
- [ ] Test successful execution

**Acceptance Criteria:**
- Webhook executions succeed consistently
- Error rate < 5%

---

### Priority 2: Provider Vertical Slice (Days 3-9)

**Decision Point:** Choose Google OR Microsoft for first full implementation

#### Option A: Google (Recommended)
**Pros:**
- Simpler OAuth 2.0 flow
- Better API documentation
- Gmail API well-established
- Broader user base

**Cons:**
- Need Google Cloud project setup

#### Option B: Microsoft
**Pros:**
- Enterprise-focused
- Graph API covers more services

**Cons:**
- More complex OAuth (Azure AD)
- Steeper learning curve

**Recommendation:** **Start with Google** for faster iteration, then template to Microsoft in Sprint 54.

---

### 2.1 Google Provider Adapter (If Chosen)

#### Phase A: OAuth 2.0 Flow (Days 3-4)

**Tasks:**
- [ ] Create Google Cloud project
- [ ] Configure OAuth consent screen
- [ ] Generate client ID + secret
- [ ] Implement `/oauth/google/authorize` endpoint
- [ ] Implement `/oauth/google/callback` endpoint
- [ ] Store tokens securely (encrypted in database)
- [ ] Implement token refresh logic
- [ ] Add OAuth tests

**Files to Create:**
- `src/auth/oauth/google.py` - OAuth flow implementation
- `src/auth/oauth/token_storage.py` - Encrypted token management
- `tests/auth/test_google_oauth.py` - OAuth tests

**Acceptance Criteria:**
- User can authorize Relay to access Gmail
- Tokens stored encrypted in database
- Tokens refresh automatically when expired
- OAuth flow tested with mock responses

#### Phase B: Gmail API Integration (Days 5-6)

**Tasks:**
- [ ] Install Google API client library
- [ ] Implement Gmail service wrapper
- [ ] Create `src/actions/adapters/google.py`
- [ ] Implement `gmail.send_email` action
- [ ] Handle API rate limits
- [ ] Add comprehensive error handling
- [ ] Write adapter tests

**Files to Create:**
- `src/actions/adapters/google.py` - Gmail adapter
- `src/actions/adapters/google_api_client.py` - Gmail API wrapper
- `tests/actions/adapters/test_google.py` - Adapter tests

**Action Schema:**
```python
{
    "id": "gmail.send_email",
    "name": "Send Gmail",
    "provider": "google",
    "schema": {
        "type": "object",
        "properties": {
            "to": {"type": "string", "format": "email"},
            "subject": {"type": "string", "maxLength": 255},
            "body": {"type": "string"},
            "cc": {"type": "array", "items": {"type": "string", "format": "email"}},
            "bcc": {"type": "array", "items": {"type": "string", "format": "email"}},
        },
        "required": ["to", "subject", "body"]
    }
}
```

**Acceptance Criteria:**
- Gmail send works end-to-end
- Error handling for API failures
- Rate limiting respected
- Tests cover success + error cases

#### Phase C: Integration & Documentation (Day 7)

**Tasks:**
- [ ] Update `/actions` endpoint to return Google actions
- [ ] Enable `gmail.send_email` in action registry
- [ ] Add Prometheus metrics for Google actions
- [ ] Update observability dashboard
- [ ] Write integration guide (`docs/integrations/GOOGLE.md`)
- [ ] Write OAuth setup guide for users

**Acceptance Criteria:**
- End-to-end flow works: authorize → preview → execute
- Metrics tracked in Grafana
- Documentation complete

---

### Priority 3: SDK Generation (Days 8-9)

**Why:** Enable external developers to use Actions API

#### 3.1 OpenAPI Spec Generation

**Tasks:**
- [ ] Generate OpenAPI 3.0 spec from FastAPI
- [ ] Validate spec with Swagger UI
- [ ] Add examples for each endpoint
- [ ] Document authentication

**Output:** `docs/api/openapi.yaml`

#### 3.2 Generate Client SDKs

**Tools:**
- `openapi-generator` (community)
- `fastapi` built-in OpenAPI

**Tasks:**
- [ ] Generate JavaScript/TypeScript SDK
- [ ] Generate Python SDK
- [ ] Add SDK usage examples
- [ ] Publish to npm (private registry or public)
- [ ] Publish to PyPI (private or public)

**Files to Create:**
- `sdks/javascript/` - JS/TS SDK package
- `sdks/python/` - Python SDK package
- `docs/sdks/JAVASCRIPT.md` - JS SDK guide
- `docs/sdks/PYTHON.md` - Python SDK guide

**Acceptance Criteria:**
- SDKs generated and functional
- Example code works
- Published packages (private or public)

---

## Sprint 53 Non-Goals (Deferred)

**Not in Sprint 53:**
- ❌ Second provider (Microsoft or Apple)
- ❌ SMTP independent action
- ❌ Grafana Cloud deployment
- ❌ Billing/monetization
- ❌ Multi-workspace support
- ❌ Admin SSO/SCIM
- ❌ Template marketplace

**Reason:** Focus on **quality over breadth**. One complete vertical slice is better than multiple incomplete features.

---

## Success Criteria

### Must Have (Sprint 53 Complete)

1. ✅ Redis deployed to Railway and operational
2. ✅ Studio UI verified working with backend
3. ✅ ONE provider adapter fully functional (Google or Microsoft)
4. ✅ OAuth flow working end-to-end
5. ✅ SDKs generated (JS + Python)
6. ✅ Documentation complete
7. ✅ Tests passing (provider adapter + OAuth)
8. ✅ Metrics tracked in Grafana

### Nice to Have (Stretch Goals)

9. 🎯 Second provider adapter started (scaffold only)
10. 🎯 CLI tool for API interaction
11. 🎯 Postman collection published

---

## Technical Architecture

### OAuth Token Storage (New)

**Table:** `oauth_tokens`
```sql
CREATE TABLE oauth_tokens (
    id UUID PRIMARY KEY,
    user_id UUID REFERENCES users(id),
    provider VARCHAR(50) NOT NULL,  -- 'google', 'microsoft', etc.
    access_token_encrypted TEXT NOT NULL,
    refresh_token_encrypted TEXT NOT NULL,
    token_type VARCHAR(50) DEFAULT 'Bearer',
    expires_at TIMESTAMP NOT NULL,
    scope TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(user_id, provider)
);
```

**Encryption:** Use `cryptography.fernet` with key from `OAUTH_ENCRYPTION_KEY` env var

### Provider Adapter Pattern

```python
# src/actions/adapters/base.py
class ProviderAdapter(ABC):
    @abstractmethod
    def list_actions(self) -> list[ActionDefinition]:
        pass

    @abstractmethod
    def preview(self, action: str, params: dict) -> dict:
        pass

    @abstractmethod
    async def execute(self, action: str, params: dict, user_id: str) -> dict:
        pass

# src/actions/adapters/google.py
class GoogleAdapter(ProviderAdapter):
    def __init__(self, oauth_service: OAuthService):
        self.oauth = oauth_service

    async def execute(self, action: str, params: dict, user_id: str) -> dict:
        # Get user's OAuth tokens
        tokens = await self.oauth.get_tokens(user_id, "google")

        # Use Gmail API
        gmail = build('gmail', 'v1', credentials=tokens)
        ...
```

---

## Risks & Mitigation

### Risk 1: OAuth Complexity
**Impact:** High - Blocks provider functionality
**Probability:** Medium
**Mitigation:**
- Use well-tested libraries (`google-auth`, `msal`)
- Follow official OAuth guides closely
- Test with real Google accounts early
- Have fallback: manual token entry for dev/testing

### Risk 2: API Rate Limits
**Impact:** Medium - Affects production usage
**Probability:** High
**Mitigation:**
- Implement exponential backoff
- Track rate limit metrics
- Cache API responses where appropriate
- Document rate limit expectations

### Risk 3: Scope Creep
**Impact:** High - Sprint extends beyond 12 days
**Probability:** Medium
**Mitigation:**
- **Strict scope:** ONE provider only
- Defer second provider to Sprint 54
- Focus on quality over quantity
- Use time-boxing for each phase

---

## Dependencies

**External Services:**
- Google Cloud Platform (if Google chosen)
- Azure AD (if Microsoft chosen)
- Railway Redis service (new)

**Code Dependencies:**
```python
# New packages needed
google-auth>=2.0.0
google-auth-oauthlib>=1.0.0
google-auth-httplib2>=0.1.0
google-api-python-client>=2.0.0
cryptography>=41.0.0  # For token encryption
```

---

## Timeline

**Total Duration:** 10-12 days

| Days | Phase | Deliverables |
|------|-------|--------------|
| 1-2 | Infrastructure | Redis deployed, Studio verified, webhook fixed |
| 3-4 | OAuth Flow | Google OAuth working, tokens stored |
| 5-6 | Gmail API | Gmail send action functional |
| 7 | Integration | End-to-end flow + docs |
| 8-9 | SDK Generation | JS + Python SDKs published |
| 10 | Testing & Polish | Bug fixes, performance tuning |
| 11-12 | Buffer | Documentation, cleanup |

---

## Alignment with Vision

From `RELAY_VISION_2025.md`:

**Sprint 49B-52 Goals (Current):**
- ✅ Actions API (provider-agnostic): `/actions` list/preview/execute
- ⚠️ **Provider adapters: Independent, Microsoft, Google** ← Sprint 53 focus
- ⚠️ Keys & rate limits ← Enabled with Redis
- ⚠️ SDKs: JS/Python clients ← Sprint 53 focus

**KPI Targets (Sprint 49-52):**
- Time-to-first-action < 3 minutes ← Measured after OAuth flow complete
- P95 action latency < 1.2s ← Currently meeting this
- 30-day retention ≥ 40% ← Not yet tracked (no beta users)

**Sprint 53 moves us from "foundation" to "functional integration platform."**

---

## Next Steps After Sprint 53

**Sprint 54 Priorities:**
1. Second provider adapter (whichever wasn't chosen in Sprint 53)
2. SMTP independent action
3. Multi-workspace support
4. API key management UI
5. Grafana Cloud deployment
6. First beta user onboarding

---

## References

- Validation Audit: `docs/status/SPRINT-52-VALIDATION-AUDIT.md`
- Sprint 52 Spec: `docs/SPRINT-52-PLATFORM-ALIGNMENT.md`
- Vision Doc: `RELAY_VISION_2025.md`
- Actions Contracts: `src/actions/contracts.py`
- Independent Adapter: `src/actions/adapters/independent.py`

---

## Sign-Off

**Planning Complete:** October 8, 2025
**Ready to Start:** ✅ Yes
**Blockers:** None
**Team:** Kyle (owner) + Claude Code (execution)

**Let's build! 🚀**
