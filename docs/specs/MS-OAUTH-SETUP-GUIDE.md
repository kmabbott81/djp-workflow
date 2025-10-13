# Microsoft OAuth Setup Guide - Azure AD App Registration

**Purpose:** Step-by-step guide for registering Azure AD application for Microsoft Graph API integration.

**Target Audience:** Platform engineers setting up Microsoft Outlook integration for the first time.

**Prerequisites:**
- Azure AD tenant access (organizational account)
- Admin consent permission (or self-consent for personal accounts)
- Microsoft 365 account with Exchange Online mailbox

---

## Overview

This guide covers:
1. Azure AD app registration (single tenant)
2. API permissions configuration (Mail.Send + offline_access)
3. Redirect URI setup (localhost + production)
4. Client secret generation
5. Environment variable configuration
6. Testing OAuth flow locally

**Security Note:** This implementation uses OAuth 2.0 Authorization Code Flow with PKCE (Proof Key for Code Exchange) for enhanced security.

---

## Step 1: Create Azure AD App Registration

### 1.1 Navigate to Azure Portal

1. Go to: https://portal.azure.com
2. Sign in with your organizational account
3. Navigate to: **Azure Active Directory** → **App registrations**
4. Click: **New registration**

### 1.2 Configure Basic Settings

**Application Name:** `Relay AI - Microsoft Outlook Integration`

**Supported account types:**
- ✅ **Accounts in this organizational directory only (Single tenant)**
- ❌ Accounts in any organizational directory (Multi-tenant) - Phase 2
- ❌ Personal Microsoft accounts - Phase 2

**Redirect URI:**
- Platform: **Web**
- URI: `http://localhost:8000/auth/microsoft/callback`

Click: **Register**

### 1.3 Note Application IDs

After registration, you'll see the **Overview** page. Record these values:

```bash
# Application (client) ID - looks like: 12345678-1234-1234-1234-123456789abc
MS_CLIENT_ID=<your-client-id>

# Directory (tenant) ID - looks like: 87654321-4321-4321-4321-cba987654321
MS_TENANT_ID=<your-tenant-id>
```

---

## Step 2: Configure API Permissions

### 2.1 Add Microsoft Graph Permissions

1. In your app registration, go to: **API permissions**
2. Click: **Add a permission**
3. Select: **Microsoft Graph**
4. Select: **Delegated permissions**
5. Search and add the following permissions:

**Required Permissions:**
- `Mail.Send` - Send mail as a user
- `offline_access` - Maintain access to data you have given it access to
- `openid` - Sign users in (included by default)
- `email` - View users' email address (included by default)
- `profile` - View users' basic profile (included by default)

6. Click: **Add permissions**

### 2.2 Grant Admin Consent (If Required)

If your organization requires admin consent:

1. Click: **Grant admin consent for [Your Organization]**
2. Confirm: **Yes**
3. Wait for status to show: ✅ **Granted for [Your Organization]**

**Note:** For personal Microsoft accounts or non-admin users, consent will be requested during the OAuth flow.

---

## Step 3: Generate Client Secret

### 3.1 Create New Client Secret

1. In your app registration, go to: **Certificates & secrets**
2. Click: **New client secret**
3. Description: `Relay AI - Production Secret`
4. Expires: **24 months** (recommended) or **Custom** (max security)
5. Click: **Add**

### 3.2 Record Client Secret (IMPORTANT)

⚠️ **CRITICAL:** Copy the secret **VALUE** immediately - it will only be shown once!

```bash
# Client secret value - looks like: AbC1~D2e3F4g5H6i7J8k9L0m1N2o3P4q5R6s7
MS_CLIENT_SECRET=<your-client-secret-value>
```

**Security Best Practices:**
- ✅ Store in environment variables (not in code)
- ✅ Use secrets manager in production (Railway secrets, AWS Secrets Manager, etc.)
- ✅ Rotate secrets every 6-12 months
- ❌ Never commit to Git
- ❌ Never share in Slack/email

---

## Step 4: Configure Redirect URIs

### 4.1 Add Production Redirect URI

1. In your app registration, go to: **Authentication**
2. Under **Web** platform, click: **Add URI**
3. Add production URI: `https://your-production-domain.com/auth/microsoft/callback`
4. Click: **Save**

**Example URIs:**
```
Development:  http://localhost:8000/auth/microsoft/callback
Staging:      https://staging-relay.example.com/auth/microsoft/callback
Production:   https://relay.example.com/auth/microsoft/callback
```

### 4.2 Configure Token Settings (Optional)

Under **Authentication** → **Advanced settings**:

- **Allow public client flows:** No (we use PKCE for public clients)
- **Supported account types:** Single tenant (already set)

---

## Step 5: Environment Configuration

### 5.1 Local Development (.env file)

Create or update `.env` file in project root:

```bash
# Microsoft OAuth Configuration
MS_CLIENT_ID=12345678-1234-1234-1234-123456789abc
MS_CLIENT_SECRET=AbC1~D2e3F4g5H6i7J8k9L0m1N2o3P4q5R6s7
MS_TENANT_ID=87654321-4321-4321-4321-cba987654321
MS_REDIRECT_URI=http://localhost:8000/auth/microsoft/callback

# Provider feature flag
PROVIDER_MICROSOFT_ENABLED=true

# Internal-only mode (restrict to internal domains)
MICROSOFT_INTERNAL_ONLY=true
MICROSOFT_INTERNAL_ALLOWED_DOMAINS=yourcompany.com,example.com

# Required infrastructure (already configured for Google)
DATABASE_URL=postgresql://...
REDIS_URL=redis://...
OAUTH_ENCRYPTION_KEY=<32-byte-base64-key>
```

### 5.2 Railway/Production Configuration

In Railway (or your deployment platform):

1. Go to project settings → **Variables**
2. Add the following secrets:
   - `MS_CLIENT_ID` = `<your-client-id>`
   - `MS_CLIENT_SECRET` = `<your-client-secret>` (encrypted)
   - `MS_TENANT_ID` = `<your-tenant-id>`
   - `MS_REDIRECT_URI` = `https://your-domain.com/auth/microsoft/callback`
   - `PROVIDER_MICROSOFT_ENABLED` = `true`
   - `MICROSOFT_INTERNAL_ONLY` = `true`
   - `MICROSOFT_INTERNAL_ALLOWED_DOMAINS` = `yourcompany.com`

---

## Step 6: Test OAuth Flow Locally

### 6.1 Start Local Server

```bash
# Set environment variables
export MS_CLIENT_ID=<your-client-id>
export MS_CLIENT_SECRET=<your-client-secret>
export MS_TENANT_ID=<your-tenant-id>
export MS_REDIRECT_URI=http://localhost:8000/auth/microsoft/callback
export PROVIDER_MICROSOFT_ENABLED=true
export DATABASE_URL=<your-database-url>
export REDIS_URL=<your-redis-url>
export OAUTH_ENCRYPTION_KEY=<your-encryption-key>

# Start server
python -m uvicorn src.webapi:app --port 8000 --reload
```

### 6.2 Run Manual Token Setup Script

```bash
python scripts/manual_token_setup_ms.py \
  --workspace-id ws_test_123 \
  --actor-id user_test_456
```

**Expected Output:**
```
🔐 Microsoft OAuth Token Setup - Manual Flow
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

✅ Configuration loaded:
   Client ID: 12345678-****-****-****-********9abc
   Tenant ID: 87654321-****-****-****-********4321
   Redirect URI: http://localhost:8000/auth/microsoft/callback

📋 Step 1: Open this URL in your browser:
https://login.microsoftonline.com/87654321-.../oauth2/v2.0/authorize?client_id=...&code_challenge=...

📋 Step 2: After authorization, paste the full callback URL here:
Callback URL: http://localhost:8000/auth/microsoft/callback?code=...&state=...

🔄 Exchanging authorization code for tokens...
✅ Tokens stored successfully!
   - Access token expires in: 3600 seconds
   - Refresh token: available
   - Token cache: database + Redis

🎉 OAuth setup complete! You can now send emails via Microsoft Graph API.
```

### 6.3 Verify Token Storage

```bash
# Check database for stored tokens
python -c "
from src.auth.oauth.ms_tokens import get_tokens
import asyncio

async def check():
    tokens = await get_tokens('ws_test_123', 'user_test_456')
    print(f'Tokens found: {bool(tokens)}')
    if tokens:
        print(f'Expires at: {tokens.get(\"expires_at\")}')
        print(f'Has refresh token: {bool(tokens.get(\"refresh_token\"))}')

asyncio.run(check())
"
```

**Expected Output:**
```
Tokens found: True
Expires at: 2025-10-12 18:30:45
Has refresh token: True
```

---

## Step 7: Test Email Send

### 7.1 Send Test Email via Integration Test

```bash
# Set test environment variables
export TEST_MICROSOFT_INTEGRATION=true
export MS_TEST_RECIPIENT=test@yourcompany.com  # Internal domain only

# Run integration test
pytest tests/integration/test_microsoft_send.py -v
```

**Expected Output:**
```
tests/integration/test_microsoft_send.py::test_microsoft_send_happy_path PASSED
tests/integration/test_microsoft_send.py::test_microsoft_send_with_attachments PASSED
tests/integration/test_microsoft_send.py::test_microsoft_send_internal_only_blocks_external PASSED
```

### 7.2 Verify Email Delivery

1. Check recipient inbox for test email
2. Verify subject: "Test Email from Relay AI"
3. Verify body contains HTML content
4. Verify attachments (if sent)

---

## Troubleshooting

### Issue: "Invalid client secret"

**Symptoms:** `401 Unauthorized` during token exchange

**Solution:**
1. Verify `MS_CLIENT_SECRET` matches Azure portal value exactly
2. Check for trailing spaces or newlines in environment variable
3. If expired, generate new secret in Azure portal

### Issue: "Redirect URI mismatch"

**Symptoms:** Error during authorization: `AADSTS50011: The redirect URI ... does not match the redirect URIs configured for the application`

**Solution:**
1. Verify `MS_REDIRECT_URI` exactly matches Azure portal configuration
2. Check for trailing slashes (must match exactly)
3. Add missing URI in Azure portal → Authentication → Redirect URIs

### Issue: "Insufficient privileges to complete the operation"

**Symptoms:** `403 Forbidden` when sending email

**Solution:**
1. Verify `Mail.Send` permission is added in Azure portal
2. If admin consent required, grant it in API permissions
3. Verify user has Exchange Online mailbox (not all M365 licenses include email)

### Issue: "Token refresh fails"

**Symptoms:** `invalid_grant` error during token refresh

**Solution:**
1. Verify `offline_access` scope is included in API permissions
2. Check token expiration in database (tokens expire after 90 days of inactivity)
3. If tokens expired, run `manual_token_setup_ms.py` again to re-authorize

### Issue: "Rate limiting (429 Too Many Requests)"

**Symptoms:** `429` response with `Retry-After` header

**Solution:**
- This is expected behavior during high traffic
- Our implementation automatically retries with exponential backoff
- Check `throttled_429` metric in Prometheus
- If sustained, consider implementing request queuing

---

## Security Checklist

Before going to production:

- [ ] Client secret stored in secrets manager (not environment variables in code)
- [ ] Redirect URIs limited to production domains only (remove localhost)
- [ ] Internal-only mode enabled (`MICROSOFT_INTERNAL_ONLY=true`)
- [ ] Domain allowlist configured with only trusted domains
- [ ] Token encryption key rotated from dev key
- [ ] OAuth state CSRF tokens enabled (automatic in our implementation)
- [ ] PKCE enabled (automatic in our implementation)
- [ ] Tokens stored encrypted in database (automatic)
- [ ] Redis TLS enabled for token cache
- [ ] Database TLS enabled for token storage
- [ ] Rollout gate configured (start at 0%, gradual rollout)

---

## API Rate Limits

**Microsoft Graph API Limits:**
- **Resource-based throttling:** 10,000 requests per 10 minutes per user
- **Service-based throttling:** Varies by workload (Mail.Send typically ~30 req/sec)
- **Tenant-wide limits:** 300,000 requests per 5 minutes

**Our Mitigations:**
- Exponential backoff with jitter on 429 responses
- Retry-After header parsing (seconds or HTTP date)
- Max 3 retries per request
- Circuit breaker pattern (future enhancement)

**Monitoring:**
- `throttled_429` structured error count
- `job:outlook_send_latency_p95:5m` (latency increases under throttling)
- `OutlookSendHighLatency` alert (warns if P95 > 2s)

---

## References

**Microsoft Documentation:**
- [Register an application with Microsoft identity platform](https://learn.microsoft.com/en-us/azure/active-directory/develop/quickstart-register-app)
- [Microsoft Graph API - Send mail](https://learn.microsoft.com/en-us/graph/api/user-sendmail)
- [OAuth 2.0 authorization code flow with PKCE](https://learn.microsoft.com/en-us/azure/active-directory/develop/v2-oauth2-auth-code-flow)
- [Microsoft Graph throttling guidance](https://learn.microsoft.com/en-us/graph/throttling)

**Internal Documentation:**
- OAuth token manager: `src/auth/oauth/ms_tokens.py`
- Microsoft adapter: `src/actions/adapters/microsoft.py`
- Recording rules: `config/prometheus/prometheus-recording-microsoft.yml`
- Alert rules: `config/prometheus/prometheus-alerts-microsoft.yml`

---

**Created:** 2025-10-12
**Owner:** Platform Engineering / Microsoft Integration Team
**Status:** Ready for Azure AD app registration (Week 2)
