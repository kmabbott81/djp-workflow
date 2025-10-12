# Phase 3 E2E Testing - Status

**Date:** 2025-10-10
**Status:** ✅ OAuth Complete - Ready for E2E Testing

---

## ✅ Completed

1. **OAuth Setup in GCP** ✓
   - OAuth client created: `70455570373-o3l12k6gdokvpr87l66hh6jh7bvqpnbo.apps.googleusercontent.com`
   - Test user added: kbmabb@gmail.com
   - Redirect URI configured: `http://localhost:8003/oauth/google/callback`

2. **Environment Configuration** ✓
   - `.env.e2e` configured with all credentials
   - DATABASE_URL: Railway PostgreSQL
   - REDIS_URL: Railway Redis (crossover.proxy.rlwy.net:22070)
   - OAUTH_ENCRYPTION_KEY: Set

3. **OAuth Tokens Stored** ✓
   - Workspace ID: `00000000-0000-0000-0000-000000000e2e`
   - Actor ID: `kbmabb@gmail.com`
   - Access token: Valid for ~1 hour
   - Scopes: gmail.send, openid, email, profile
   - **Note:** No refresh token yet (will need to revoke + re-auth if expired)

4. **OAuth Callback Fixed** ✓
   - Fixed to use proper UUID for workspace_id
   - Uses Redis for state management (persistent across reloads)

---

## 🚀 Next Steps

### 1. Run E2E Test Suite

```bash
cd C:\Users\kylem\openai-agents-workflows-2025.09.28-v1
python scripts/e2e_gmail_test.py --scenarios all --verbose
```

**This will test:**
- ✅ Scenario 1: Text-only email (baseline)
- ✅ Scenario 2: HTML + text fallback (sanitization)
- ✅ Scenario 3: HTML + inline image (CID references)
- ✅ Scenario 4: Regular attachments
- ✅ Scenario 5: Full complexity (nested multipart)
- ✅ Scenario 6: Validation errors (oversized, blocked MIME, orphan CID)
- ✅ Scenario 7: Internal-only controls
- ✅ Scenario 8: Rollout controller observation

### 2. If Access Token Expired

If you see authentication errors:

1. **Revoke app access:**
   - Visit: https://myaccount.google.com/connections
   - Find "Relay E2E Local"
   - Click "Remove access"

2. **Re-run OAuth setup to get refresh token:**
   ```bash
   python scripts/manual_token_setup.py
   ```
   - This will give you a refresh token on first authorization
   - Follow the prompts to paste the callback URL

### 3. Collect Evidence

After tests pass, collect evidence with this prompt to Claude:

```
OAuth is configured and .env.e2e is set.

Run the full E2E test suite (scripts/e2e_gmail_test.py --scenarios all --verbose).

Return a table of the 8 scenarios with PASS/FAIL and durations.

Include MIME trees for the 3 golden cases (redacted).

Include Prometheus results for:
• gmail_mime_build_seconds_bucket (P95)
• gmail_attachment_bytes_total by result
• gmail_inline_refs_total by result
• gmail_html_sanitization_changes_total by change_type

Run the rollout controller once with ROLLOUT_DRY_RUN=true and paste the last 5 audit log lines and rollout_controller_runs_total by status.

Provide a self-critique of flakiness or perf hotspots, with one suggested fix.
```

### 4. Monitor Controller in Dry-Run

Run controller locally for 24-48 hours:

```bash
# Set environment
set ROLLOUT_DRY_RUN=true
set ROLLOUT_ENABLED=true
set ROLLOUT_EVAL_INTERVAL_SECONDS=300

# Run controller
python -m src.rollout.controller
```

Watch for:
- SLO metrics (error rate, P95 latency)
- Dry-run decisions (should NOT change rollout_percent)
- Audit logs in `audit/audit-*.jsonl`

---

## 📁 Key Files

### Scripts
- `scripts/e2e_gmail_test.py` - Main E2E test runner
- `scripts/manual_token_setup.py` - OAuth flow helper (interactive)
- `scripts/complete_oauth.py` - OAuth flow helper (non-interactive)
- `scripts/store_tokens.py` - Manual token storage

### Configuration
- `.env.e2e` - Environment variables for E2E testing
- `start_oauth_server.bat` - Start OAuth server (if needed)

### Documentation
- `docs/specs/PHASE-3-E2E-TESTING-PLAN.md` - Complete test plan (450 lines)
- `docs/specs/PHASE-3-SETUP-CHECKLIST.md` - Setup checklist
- `docs/specs/OAUTH-SETUP-GUIDE.md` - OAuth setup guide

---

## 🔧 Troubleshooting

### Token Verification

Check if tokens are valid:

```bash
python -c "import asyncio; from src.auth.oauth.tokens import OAuthTokenCache; asyncio.run(OAuthTokenCache().get_tokens('google', '00000000-0000-0000-0000-000000000e2e', 'kbmabb@gmail.com'))"
```

### Redis Connection

Verify Redis is accessible:

```bash
python -c "import redis; r = redis.from_url('redis://default:zhtagqDujRcWQzETQOgHYLYYtiVduGTe@crossover.proxy.rlwy.net:22070', decode_responses=True); r.ping(); print('Redis OK')"
```

### Database Connection

Verify PostgreSQL is accessible:

```bash
python -c "import asyncio; from src.db.connection import get_connection; asyncio.run((lambda: None)())"
```

---

## 📊 Success Criteria

**Phase 3 is complete when:**

1. ✅ All 8 E2E scenarios pass
2. ✅ MIME structures are correct (validated against RFC 2822)
3. ✅ Structured error payloads match spec
4. ✅ Internal-only controls work (domain allowlist)
5. ✅ Rollout controller runs in dry-run mode without errors
6. ✅ Prometheus metrics are collected
7. ✅ Audit logs show all actions
8. ✅ Controller runs stably for 24-48 hours

**Then proceed to Phase 4:** Observability enhancements (Prometheus rules + Grafana dashboards)

---

## 🎯 Current Blockers

**None!** Ready to run E2E tests.

**Note:** Access token expires in ~1 hour. If expired, follow "If Access Token Expired" steps above.
