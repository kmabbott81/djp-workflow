# Sprint 57: Security Hardening

**Status:** 🟡 READY TO START (After Sprint 56 Week 2)
**Duration:** 1 week
**Phase:** Production Readiness
**Depends on:** Sprint 56 Week 2 (Streaming Responses) ✅

---

## North Star Alignment

This sprint directly advances toward:
- ✅ **Production-ready security** - No dev mode defaults, proper secret management
- ✅ **Enterprise trust** - HMAC signing, rate limiting, audit trails
- ✅ **Compliance readiness** - All operational security gaps closed

**Strategic Goal:** Harden the platform from "secure on paper" to "locked down for real use" by eliminating dev-mode shortcuts and adding operational security controls.

---

## Sprint Goals

**Objective:** Close all identified security gaps and implement operational hardening before external exposure.

**Deliverables:**

1. ✅ **Flip DEV_AUTH_MODE default to false** - Require explicit opt-in for dev mode
2. ✅ **Remove hardcoded demo key** - Rotate and remove from codebase
3. ✅ **Move secrets to proper secret management** - Railway/cloud secrets for all keys
4. ✅ **Add HMAC signing for webhooks** - Request verification middleware
5. ✅ **Enable rate limiting** - Protect auth and AI endpoints from abuse
6. ✅ **Add security monitoring** - Automated alerts on policy violations

**Success Criteria:**
- All dev-mode defaults removed
- Zero hardcoded secrets in codebase
- All external callbacks signed with HMAC
- Rate limits enforced on sensitive endpoints
- Security violations logged and alerted

**Definition of Done:**
> Sprint 57 is done when the platform can be safely exposed to external users with no dev-mode shortcuts, all secrets properly managed, webhook signing enforced, and rate limiting active on all sensitive endpoints.

---

## Security Gaps Analysis

### Critical (Must Fix Before Production)

1. **DEV_AUTH_MODE Defaults to True** (security.py:154)
   - **Risk:** Could accidentally deploy with auth disabled
   - **Impact:** Complete bypass of authentication
   - **Fix:** Change default to `false`, require explicit `DEV_AUTH_MODE=true` in env

2. **Demo Key Hardcoded** (security.py:168)
   - **Risk:** `relay_sk_demo_preview_key` allows preview access without database
   - **Impact:** Unauthorized access to preview endpoints
   - **Fix:** Remove from code, generate proper API keys for testing

3. **Secrets in Environment Variables** (visible in process list)
   - **Risk:** API keys passed via command line (visible in `ps aux`)
   - **Impact:** Key exposure to anyone with process access
   - **Fix:** Use Railway secrets / cloud secret manager

### High (Should Fix Soon)

4. **No Request Signing for Webhooks**
   - **Risk:** Webhook spoofing attacks possible
   - **Impact:** Malicious actors could trigger workflows
   - **Fix:** Add HMAC-SHA256 signing with shared secret

5. **No Rate Limiting on Critical Endpoints**
   - **Risk:** Brute force attacks on `/ai/plan`, `/ai/execute`, auth endpoints
   - **Impact:** Resource exhaustion, credential stuffing
   - **Fix:** Enable rate limiter (infrastructure exists in `src/limits/`)

6. **OpenAI API Key Handling**
   - **Risk:** Key stored in plain environment variables
   - **Impact:** Key exposure if logs/errors leaked
   - **Fix:** Migrate to Railway secret management

### Medium (Nice to Have)

7. **No Automated Security Monitoring**
   - **Risk:** Policy violations go unnoticed
   - **Impact:** Slow incident response
   - **Fix:** Add alerts on suspicious patterns (Prometheus + Alertmanager)

8. **Audit Log Viewer Not Implemented**
   - **Risk:** Hard to investigate security incidents
   - **Impact:** Compliance and forensics challenges
   - **Fix:** Add simple UI for audit log search (stretch goal)

---

## Implementation Plan

### Task 1: Fix DEV_AUTH_MODE Default (Critical)

**File:** `src/auth/security.py:154`

**Current Code:**
```python
if os.getenv("DEV_AUTH_MODE", "true").lower() == "true":
```

**Updated Code:**
```python
if os.getenv("DEV_AUTH_MODE", "false").lower() == "true":
```

**Impact:**
- Auth now required by default
- Developers must explicitly set `DEV_AUTH_MODE=true` in local `.env`
- Production deployments safe by default

**Testing:**
- Start server without `DEV_AUTH_MODE` → Auth should be required
- Set `DEV_AUTH_MODE=true` → Dev mode should work
- Verify Railway prod deployment doesn't have this env var set

---

### Task 2: Remove Hardcoded Demo Key (Critical)

**File:** `src/auth/security.py:168-183`

**Current Code:**
```python
if token == "relay_sk_demo_preview_key":
    # Grant preview-only scopes for demo mode
    ...
```

**Updated Code:**
```python
# Remove entire demo key block
# Use proper API keys for testing instead
```

**Migration Path:**
1. Generate proper test API keys in dev database
2. Update all references to demo key in tests/docs
3. Remove demo key code block
4. Document how to create test keys in `docs/DEVELOPMENT.md`

**Testing:**
- Demo key should no longer work
- Tests should use real API keys from fixture data
- Dev setup guide should document key creation process

---

### Task 3: Migrate Secrets to Railway (Critical)

**Current State:**
- `OPENAI_API_KEY` passed via command line
- `GOOGLE_CLIENT_SECRET` in env vars
- `OAUTH_ENCRYPTION_KEY` in env vars
- `DATABASE_URL` in env vars (acceptable)
- `REDIS_URL` in env vars (acceptable)

**Migration Plan:**

1. **Add Railway Secrets:**
   ```bash
   railway secrets set OPENAI_API_KEY="sk-proj-..."
   railway secrets set GOOGLE_CLIENT_SECRET="GOCSPX-..."
   railway secrets set OAUTH_ENCRYPTION_KEY="Mvwr_5P4VoevQaR7..."
   ```

2. **Update start_server.bat for Local Dev:**
   ```batch
   @echo off
   REM Load secrets from .env file (git-ignored)
   for /f "delims=" %%x in (.env) do (set "%%x")

   python -m uvicorn src.webapi:app --port 8000 --reload
   ```

3. **Create .env.example Template:**
   ```bash
   # .env.example - Copy to .env and fill in your secrets
   ACTIONS_ENABLED=true
   TELEMETRY_ENABLED=true
   DEV_AUTH_MODE=true
   RELAY_ENV=local

   # OpenAI (required for AI planning)
   OPENAI_API_KEY=sk-proj-YOUR_KEY_HERE

   # Google OAuth (optional - only if using Gmail actions)
   GOOGLE_CLIENT_ID=YOUR_CLIENT_ID
   GOOGLE_CLIENT_SECRET=YOUR_SECRET

   # Database (local or Railway)
   DATABASE_URL=postgresql://user:pass@host:port/db
   REDIS_URL=redis://default:pass@host:port

   # OAuth encryption (generate with: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())")
   OAUTH_ENCRYPTION_KEY=YOUR_KEY_HERE
   ```

4. **Update .gitignore:**
   ```
   .env
   .env.local
   *.key
   secrets/
   ```

**Testing:**
- Local dev should load from `.env` file (not committed)
- Railway deployment should use Railway secrets
- No secrets in git history or process list

---

### Task 4: Add HMAC Webhook Signing (High Priority)

**File:** `src/security/hmac.py` (new file)

```python
"""HMAC request signing for webhook verification.

Implements SHA-256 HMAC signing to prevent webhook spoofing.
"""
import hashlib
import hmac
import os
from typing import Optional

from fastapi import HTTPException, Request


def compute_signature(payload: bytes, secret: str) -> str:
    """Compute HMAC-SHA256 signature for payload.

    Args:
        payload: Request body bytes
        secret: Shared secret key

    Returns:
        Hex-encoded signature
    """
    return hmac.new(
        secret.encode('utf-8'),
        payload,
        hashlib.sha256
    ).hexdigest()


def verify_webhook_signature(request: Request, body: bytes, secret_key: Optional[str] = None) -> bool:
    """Verify HMAC signature on incoming webhook request.

    Args:
        request: FastAPI request object
        body: Raw request body bytes
        secret_key: Shared secret (defaults to WEBHOOK_SIGNING_SECRET env var)

    Returns:
        True if signature valid

    Raises:
        HTTPException: 401 if signature invalid or missing
    """
    secret = secret_key or os.getenv("WEBHOOK_SIGNING_SECRET")
    if not secret:
        # No secret configured - skip verification in dev mode only
        if os.getenv("RELAY_ENV") == "local":
            return True
        raise HTTPException(
            status_code=500,
            detail="WEBHOOK_SIGNING_SECRET not configured"
        )

    # Get signature from header
    signature_header = request.headers.get("X-Webhook-Signature")
    if not signature_header:
        raise HTTPException(
            status_code=401,
            detail="Missing X-Webhook-Signature header"
        )

    # Compute expected signature
    expected_sig = compute_signature(body, secret)

    # Constant-time comparison to prevent timing attacks
    if not hmac.compare_digest(signature_header, expected_sig):
        raise HTTPException(
            status_code=401,
            detail="Invalid webhook signature"
        )

    return True
```

**Integration in webapi.py:**

```python
from src.security.hmac import verify_webhook_signature

@app.post("/webhooks/relay")
async def relay_webhook(request: Request):
    """Handle incoming webhook from Relay.

    Verifies HMAC signature before processing.
    """
    # Read raw body for signature verification
    body = await request.body()

    # Verify signature
    verify_webhook_signature(request, body)

    # Parse JSON after verification
    data = await request.json()

    # Process webhook...
```

**Client-Side Signing (for outgoing webhooks):**

```python
def sign_webhook_request(payload: dict, secret: str) -> dict:
    """Add HMAC signature to outgoing webhook request.

    Args:
        payload: Webhook payload dict
        secret: Shared secret

    Returns:
        Headers dict with X-Webhook-Signature
    """
    import json
    body_bytes = json.dumps(payload).encode('utf-8')
    signature = compute_signature(body_bytes, secret)

    return {
        "X-Webhook-Signature": signature,
        "Content-Type": "application/json"
    }
```

**Testing:**
- Valid signature → webhook processed
- Invalid signature → 401 error
- Missing signature → 401 error
- Dev mode with no secret → allowed (local only)

---

### Task 5: Enable Rate Limiting (High Priority)

**Existing Infrastructure:** `src/limits/limiter.py` already implements rate limiting

**Implementation:**

1. **Add Rate Limits to Critical Endpoints:**

```python
from src.limits.limiter import get_rate_limiter

# In webapi.py

@app.post("/ai/plan")
@require_scopes(["actions:preview"])
async def plan_with_ai(request: Request, body: dict):
    """Generate action plan - rate limited to 10 req/min per workspace."""
    limiter = get_rate_limiter()

    # Get workspace_id from auth context
    workspace_id = request.state.workspace_id

    # Check rate limit (10 requests per 60 seconds)
    if not limiter.check_limit(
        key=f"ai:plan:{workspace_id}",
        limit=10,
        window_seconds=60
    ):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Max 10 requests per minute."
        )

    # Existing logic...


@app.post("/ai/execute")
@require_scopes(["actions:execute"])
async def execute_ai_plan(request: Request, body: dict):
    """Execute plan - rate limited to 20 req/min per workspace."""
    limiter = get_rate_limiter()
    workspace_id = request.state.workspace_id

    if not limiter.check_limit(
        key=f"ai:execute:{workspace_id}",
        limit=20,
        window_seconds=60
    ):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Max 20 executions per minute."
        )

    # Existing logic...


@app.post("/actions/execute")
@require_scopes(["actions:execute"])
async def execute_action(request: Request, body: dict):
    """Execute single action - rate limited to 30 req/min per workspace."""
    limiter = get_rate_limiter()
    workspace_id = request.state.workspace_id

    if not limiter.check_limit(
        key=f"actions:execute:{workspace_id}",
        limit=30,
        window_seconds=60
    ):
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded. Max 30 actions per minute."
        )

    # Existing logic...
```

2. **Add Global Rate Limit Middleware:**

```python
@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    """Global rate limiting by IP address."""
    # Get client IP
    client_ip = request.client.host

    # Skip rate limiting for health checks
    if request.url.path in ["/health", "/metrics"]:
        return await call_next(request)

    # Global limit: 100 requests per minute per IP
    limiter = get_rate_limiter()
    if not limiter.check_limit(
        key=f"global:{client_ip}",
        limit=100,
        window_seconds=60
    ):
        return JSONResponse(
            status_code=429,
            content={"detail": "Global rate limit exceeded. Max 100 req/min per IP."}
        )

    return await call_next(request)
```

**Rate Limit Configuration:**

| Endpoint | Limit | Window | Scope |
|----------|-------|--------|-------|
| `/ai/plan` | 10 | 60s | Per workspace |
| `/ai/execute` | 20 | 60s | Per workspace |
| `/actions/execute` | 30 | 60s | Per workspace |
| `/oauth/*` | 5 | 300s | Per IP (OAuth flows) |
| Global | 100 | 60s | Per IP |

**Testing:**
- Make 11 requests to `/ai/plan` within 60s → 429 on 11th
- Wait 60s → Counter resets
- Different workspaces → Separate limits
- Verify Redis counters increment correctly

---

### Task 6: Add Security Monitoring (Medium Priority)

**File:** `src/telemetry.py` (extend existing)

```python
# Add new security metrics

security_violations = Counter(
    'security_violations_total',
    'Security policy violations',
    ['type', 'severity', 'workspace_id']
)

auth_failures = Counter(
    'auth_failures_total',
    'Authentication failures',
    ['reason', 'endpoint']
)

rate_limit_hits = Counter(
    'rate_limit_hits_total',
    'Rate limit violations',
    ['endpoint', 'workspace_id']
)
```

**Add Alerting in Prometheus/Alertmanager:**

```yaml
# alerting-rules.yml
groups:
  - name: security
    interval: 30s
    rules:
      # Alert on repeated auth failures
      - alert: HighAuthFailureRate
        expr: rate(auth_failures_total[5m]) > 10
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "High authentication failure rate detected"
          description: "{{ $value }} auth failures per second in last 5 minutes"

      # Alert on rate limit abuse
      - alert: RateLimitAbuse
        expr: rate(rate_limit_hits_total[5m]) > 5
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Rate limit repeatedly hit"
          description: "Workspace {{ $labels.workspace_id }} hitting rate limits"

      # Alert on security violations
      - alert: SecurityViolation
        expr: security_violations_total > 0
        labels:
          severity: critical
        annotations:
          summary: "Security policy violation detected"
          description: "{{ $labels.type }} violation in workspace {{ $labels.workspace_id }}"
```

**Integration:**

```python
# In require_scopes decorator (security.py)
except HTTPException as e:
    if e.status_code == 401:
        auth_failures.labels(
            reason="invalid_token",
            endpoint=request.url.path
        ).inc()
    elif e.status_code == 403:
        auth_failures.labels(
            reason="insufficient_scopes",
            endpoint=request.url.path
        ).inc()
    raise

# In rate limiter
if not check_limit(...):
    rate_limit_hits.labels(
        endpoint=request.url.path,
        workspace_id=workspace_id
    ).inc()
    raise RateLimitExceeded()
```

---

## Testing Strategy

### Security Test Suite

**File:** `tests/security/test_hardening.py`

```python
"""Security hardening tests for Sprint 57."""
import pytest
from fastapi.testclient import TestClient


def test_dev_auth_mode_defaults_to_false(monkeypatch):
    """Verify DEV_AUTH_MODE requires explicit opt-in."""
    # Clear environment
    monkeypatch.delenv("DEV_AUTH_MODE", raising=False)

    from src.webapi import app
    client = TestClient(app)

    # Auth should be required by default
    response = client.post("/ai/plan", json={"prompt": "test"})
    assert response.status_code == 401


def test_demo_key_removed():
    """Verify hardcoded demo key no longer works."""
    from src.webapi import app
    client = TestClient(app)

    response = client.post(
        "/ai/plan",
        json={"prompt": "test"},
        headers={"Authorization": "Bearer relay_sk_demo_preview_key"}
    )
    assert response.status_code == 401


def test_webhook_signature_required():
    """Verify webhooks require valid HMAC signature."""
    from src.webapi import app
    client = TestClient(app)

    # Missing signature
    response = client.post("/webhooks/relay", json={"event": "test"})
    assert response.status_code == 401
    assert "signature" in response.json()["detail"].lower()


def test_webhook_signature_validation():
    """Verify invalid signatures are rejected."""
    from src.security.hmac import compute_signature
    from src.webapi import app
    import json

    client = TestClient(app)
    payload = {"event": "test"}
    body = json.dumps(payload).encode()

    # Compute correct signature
    secret = "test_secret"
    valid_sig = compute_signature(body, secret)

    # Valid signature
    response = client.post(
        "/webhooks/relay",
        json=payload,
        headers={"X-Webhook-Signature": valid_sig}
    )
    assert response.status_code == 200

    # Invalid signature
    response = client.post(
        "/webhooks/relay",
        json=payload,
        headers={"X-Webhook-Signature": "invalid_sig"}
    )
    assert response.status_code == 401


def test_rate_limiting_enforced():
    """Verify rate limits prevent abuse."""
    from src.webapi import app
    client = TestClient(app)

    # Make 11 requests (limit is 10/min)
    for i in range(11):
        response = client.post(
            "/ai/plan",
            json={"prompt": f"test {i}"},
            headers={"Authorization": "Bearer test_key"}
        )

        if i < 10:
            assert response.status_code == 200
        else:
            assert response.status_code == 429
            assert "rate limit" in response.json()["detail"].lower()


def test_no_secrets_in_codebase():
    """Verify no hardcoded secrets in source files."""
    import re
    import glob

    secret_patterns = [
        r'sk-[a-zA-Z0-9]{20,}',  # OpenAI keys
        r'GOCSPX-[a-zA-Z0-9_-]+',  # Google OAuth secrets
        r'relay_sk_[a-zA-Z0-9]+',  # API keys
    ]

    # Scan Python files
    for filepath in glob.glob("src/**/*.py", recursive=True):
        with open(filepath) as f:
            content = f.read()
            for pattern in secret_patterns:
                matches = re.findall(pattern, content)
                # Allow in test fixtures only
                if matches and "test" not in filepath:
                    pytest.fail(f"Found secret in {filepath}: {matches[0][:10]}...")
```

### Manual Security Checklist

Before deploying to production:

- [ ] `DEV_AUTH_MODE` defaults to `false`
- [ ] Demo key removed from `security.py`
- [ ] All secrets in Railway secrets (not env vars)
- [ ] `.env` file in `.gitignore`
- [ ] No secrets in git history (`git log --all -- '*.env'`)
- [ ] Webhook signing works with test webhooks
- [ ] Rate limiting kicks in at correct thresholds
- [ ] Prometheus metrics expose security events
- [ ] Alerting rules configured in Alertmanager
- [ ] Security test suite passes

---

## Success Metrics

### Quantitative
- ✅ Zero hardcoded secrets in codebase
- ✅ 100% of sensitive endpoints rate-limited
- ✅ 100% of webhook endpoints signed with HMAC
- ✅ Auth required by default (no opt-out)

### Qualitative
- ✅ Railway deployment uses secret management
- ✅ Security violations trigger alerts
- ✅ Dev setup documented with secret generation
- ✅ Audit trail covers all security events

---

## Deployment Checklist

### Pre-Deployment

1. **Review Code Changes:**
   - [ ] All dev-mode defaults flipped
   - [ ] Demo key removed
   - [ ] Rate limiting integrated
   - [ ] HMAC signing implemented

2. **Configure Secrets:**
   ```bash
   railway secrets set OPENAI_API_KEY="sk-proj-..."
   railway secrets set GOOGLE_CLIENT_SECRET="GOCSPX-..."
   railway secrets set OAUTH_ENCRYPTION_KEY="..."
   railway secrets set WEBHOOK_SIGNING_SECRET="$(openssl rand -hex 32)"
   ```

3. **Update Environment:**
   ```bash
   railway variables set RELAY_ENV=production
   railway variables set ACTIONS_ENABLED=true
   railway variables set TELEMETRY_ENABLED=true
   # Do NOT set DEV_AUTH_MODE (defaults to false)
   ```

4. **Run Security Tests:**
   ```bash
   pytest tests/security/test_hardening.py -v
   ```

### Post-Deployment

1. **Verify Security:**
   - [ ] Auth works without `DEV_AUTH_MODE`
   - [ ] Rate limiting enforced on production
   - [ ] Webhook signatures validated
   - [ ] Prometheus metrics flowing

2. **Monitor Alerts:**
   - [ ] Check Alertmanager for security alerts
   - [ ] Verify alert routing to Slack/PagerDuty
   - [ ] Test alert by triggering rate limit

3. **Document Changes:**
   - [ ] Update `docs/DEVELOPMENT.md` with secret setup
   - [ ] Update `docs/DEPLOYMENT.md` with Railway secrets
   - [ ] Add security section to `README.md`

---

## Risk Mitigation

### Risk 1: Breaking Dev Workflow
**Mitigation:**
- Provide clear `.env.example` template
- Document secret generation in `DEVELOPMENT.md`
- Test local dev setup on fresh clone
- Keep `DEV_AUTH_MODE` flag for explicit opt-in

### Risk 2: Secrets Leakage During Migration
**Mitigation:**
- Use Railway CLI for secret upload (not web UI)
- Rotate all secrets after migration
- Audit git history for accidentally committed secrets
- Add pre-commit hook to catch secrets

### Risk 3: Rate Limiting Too Aggressive
**Mitigation:**
- Start with generous limits (monitor usage)
- Make limits configurable via env vars
- Add rate limit headers to responses
- Provide clear error messages with reset times

### Risk 4: HMAC Signing Breaks Existing Webhooks
**Mitigation:**
- Add `X-Webhook-Version` header for gradual rollout
- Support unsigned webhooks in dev mode only
- Document signing process for partners
- Provide test tool for signature generation

---

## Future Enhancements (Post-Sprint 57)

### Sprint 58: Advanced Security Features
- **Secrets Rotation:** Automated key rotation every 90 days
- **Audit Log Viewer:** UI for searching/filtering security events
- **IP Allowlisting:** Restrict API access to trusted IPs
- **2FA for Admin Accounts:** TOTP-based two-factor auth

### Sprint 59: Compliance & Governance
- **SOC 2 Preparation:** Audit trail completeness, access reviews
- **GDPR Compliance:** Data retention policies, right to erasure
- **Penetration Testing:** Third-party security audit
- **Bug Bounty Program:** Responsible disclosure policy

---

## Conclusion

Sprint 57 transforms the platform from "secure on paper" to "production-ready" by eliminating all dev-mode shortcuts and implementing operational security controls. This sprint is the final security gate before external exposure.

**Key Wins:**
- ✅ No accidental auth bypass in production
- ✅ All secrets properly managed
- ✅ Webhook spoofing prevented
- ✅ Rate limiting protects against abuse
- ✅ Security violations monitored and alerted

This is the bridge from internal MVP to enterprise-grade platform.

---

**Sprint 57 Status:** 🟡 READY TO START
**Estimated Duration:** 1 week
**Key Milestone:** Production Security Hardening Complete
