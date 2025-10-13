# Google OAuth Setup Guide - Phase 3 E2E

**Purpose:** Set up Google OAuth for Gmail API E2E testing
**Time Required:** ~15-20 minutes
**Status:** 📋 READY TO EXECUTE

## Prerequisites

- [ ] Google account for testing
- [ ] Gmail account to receive test emails
- [ ] Access to Google Cloud Console

## Step 1: Create GCP Project

1. **Go to Google Cloud Console**
   - Visit: https://console.cloud.google.com/

2. **Create New Project**
   - Click "Select a project" dropdown (top bar)
   - Click "New Project"
   - Project name: `Relay E2E Testing`
   - Organization: (leave as is)
   - Location: (leave default)
   - Click "Create"
   - Wait for project creation (~30 seconds)

3. **Verify Project Selected**
   - Ensure "Relay E2E Testing" appears in top bar

## Step 2: Enable Gmail API

1. **Navigate to APIs & Services**
   - Left menu → "APIs & Services" → "Library"
   - Or visit: https://console.cloud.google.com/apis/library

2. **Search for Gmail API**
   - Search box: "Gmail API"
   - Click "Gmail API" card

3. **Enable the API**
   - Click "Enable" button
   - Wait for activation (~10 seconds)

## Step 3: Configure OAuth Consent Screen

1. **Navigate to OAuth Consent**
   - Left menu → "APIs & Services" → "OAuth consent screen"
   - Or visit: https://console.cloud.google.com/apis/credentials/consent

2. **User Type Selection**
   - Select: **External** (allows any Gmail account)
   - Click "Create"

3. **App Information**
   - App name: `Relay E2E Testing`
   - User support email: (your email)
   - Developer contact: (your email)
   - Leave other fields empty
   - Click "Save and Continue"

4. **Scopes (Skip for Now)**
   - Click "Save and Continue" (we'll add scopes in client config)

5. **Test Users**
   - Click "Add Users"
   - Add your Gmail test account(s):
     - Example: `your.name@gmail.com`
   - Click "Add"
   - Click "Save and Continue"

6. **Summary**
   - Review settings
   - Click "Back to Dashboard"

**Note:** App will stay in "Testing" mode - this is fine for E2E testing. Max 100 test users allowed.

## Step 4: Create OAuth 2.0 Client ID

1. **Navigate to Credentials**
   - Left menu → "APIs & Services" → "Credentials"
   - Or visit: https://console.cloud.google.com/apis/credentials

2. **Create Credentials**
   - Click "+ Create Credentials" (top)
   - Select "OAuth 2.0 Client ID"

3. **Application Type**
   - Application type: **Web application**
   - Name: `Relay E2E Local`

4. **Authorized Redirect URIs**
   - Click "Add URI" under "Authorized redirect URIs"
   - Add: `http://localhost:8000/auth/google/callback`
   - (Optional) Add your dev domain if needed

5. **Create**
   - Click "Create"
   - **IMPORTANT:** Modal appears with Client ID and Client Secret
   - Copy both values immediately (you'll need them next)

**Save These Values:**
```
Client ID: xxx.apps.googleusercontent.com
Client Secret: GOCSPX-xxxxx
```

## Step 5: Configure Environment

1. **Edit .env.e2e file**

Open `C:\Users\kylem\openai-agents-workflows-2025.09.28-v1\.env.e2e` and update:

```bash
# Google OAuth (FROM GCP CONSOLE)
GOOGLE_CLIENT_ID=<YOUR_CLIENT_ID>.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-<YOUR_CLIENT_SECRET>

# OAuth Scopes (required)
GOOGLE_OAUTH_SCOPES="https://www.googleapis.com/auth/gmail.send openid email profile"

# Redirect URI (must match GCP)
GOOGLE_REDIRECT_URI=http://localhost:8000/auth/google/callback

# Provider Config
PROVIDER_GOOGLE_ENABLED=true

# Internal-Only Controls (CUSTOMIZE THESE)
GOOGLE_INTERNAL_ONLY=true
GOOGLE_INTERNAL_ALLOWED_DOMAINS=<your-domain.com>
GOOGLE_INTERNAL_TEST_RECIPIENTS=<your-test-email@gmail.com>

# E2E Test Config (CUSTOMIZE THESE)
E2E_WORKSPACE_ID=test-workspace-$(uuidgen)
E2E_ACTOR_ID=<your-email@example.com>
E2E_RECIPIENT_EMAIL=<your-test-email@gmail.com>

# Rollout (keep dry-run)
ROLLOUT_DRY_RUN=true
ROLLOUT_ENABLED=true
```

2. **Load Environment**

```bash
# Windows (Command Prompt)
for /f "delims=" %i in (.env.e2e) do set %i

# Windows (PowerShell)
Get-Content .env.e2e | ForEach-Object { if ($_ -match '^\s*([^#][^=]+)=(.*)$') { [System.Environment]::SetEnvironmentVariable($matches[1], $matches[2]) } }

# Or use Railway CLI
railway run --environment production bash
# Then: export $(cat .env.e2e | xargs)
```

## Step 6: Run OAuth Consent Flow

1. **Start API Server**

```bash
cd C:\Users\kylem\openai-agents-workflows-2025.09.28-v1

# Start server
python -m uvicorn src.webapi:app --port 8000 --reload
```

2. **Visit Consent URL**

Open browser:
```
http://localhost:8000/auth/google/consent?workspace_id=test-workspace&actor_id=your-email@example.com
```

Or use the authorize endpoint:
```
http://localhost:8000/auth/google/authorize?workspace_id=test-workspace&actor_id=your-email@example.com
```

3. **Complete OAuth Flow**
   - Click "Sign in with Google"
   - Choose your test Gmail account
   - Review permissions:
     - Send email on your behalf
     - See your email address
     - See your personal info
   - Click "Continue" (or "Allow")
   - Should redirect back to localhost
   - Look for success message

4. **Verify Tokens Stored**

```bash
python -c "
import asyncio
import os
from src.auth.oauth.tokens import OAuthTokenCache

async def check():
    cache = OAuthTokenCache()
    tokens = await cache.get_tokens_with_auto_refresh(
        'google',
        os.getenv('E2E_WORKSPACE_ID', 'test-workspace'),
        os.getenv('E2E_ACTOR_ID', 'your-email@example.com')
    )

    if tokens:
        print('[OK] OAuth tokens found!')
        print(f'  Access token length: {len(tokens.get(\"access_token\", \"\"))}')
        print(f'  Refresh token exists: {\"refresh_token\" in tokens}')
        print(f'  Expires at: {tokens.get(\"expires_at\")}')
    else:
        print('[FAIL] No tokens found - consent flow may have failed')

asyncio.run(check())
"
```

**Expected Output:**
```
[OK] OAuth tokens found!
  Access token length: 183
  Refresh token exists: True
  Expires at: 2025-10-09T20:00:00
```

## Troubleshooting

### Error: "redirect_uri_mismatch"

**Cause:** Redirect URI in GCP doesn't match code

**Fix:**
1. Check GCP Console → Credentials → OAuth Client
2. Ensure exact match: `http://localhost:8000/auth/google/callback`
3. No trailing slash, no extra paths

### Error: "access_denied"

**Cause:** User clicked "Cancel" or app not in test mode

**Fix:**
1. Complete flow again
2. Verify test user added in OAuth consent screen
3. Check app is in "Testing" status (not "Production")

### Error: "Token not found in database"

**Cause:** Database connection issue or token storage failed

**Fix:**
1. Check DATABASE_URL is set correctly
2. Verify database is accessible
3. Check logs for database errors
4. Try consent flow again

### Error: "Invalid scope"

**Cause:** Requested scope not enabled for app

**Fix:**
1. Check GOOGLE_OAUTH_SCOPES includes required scopes
2. Verify Gmail API is enabled
3. Restart server after changing scopes

## Security Notes

- ✅ Client Secret is sensitive - never commit to Git
- ✅ Test mode limits to 100 users - fine for E2E
- ✅ Tokens stored encrypted in database (OAUTH_ENCRYPTION_KEY)
- ✅ Access tokens expire after 1 hour (auto-refresh)
- ✅ Refresh tokens valid until revoked

## Next Steps

After OAuth setup complete:

1. ✅ Run E2E test script
   ```bash
   python scripts/e2e_gmail_test.py --scenarios all --verbose
   ```

2. ✅ Check Gmail inbox for test emails

3. ✅ Run controller in dry-run mode
   ```bash
   export ROLLOUT_DRY_RUN=true
   python scripts/rollout_controller.py
   ```

4. ✅ Monitor for 24-48 hours

5. ✅ Proceed to Phase 4 (Observability)

## Checklist

Before starting E2E tests, verify:

- [ ] GCP project created: "Relay E2E Testing"
- [ ] Gmail API enabled
- [ ] OAuth consent screen configured (External, Testing mode)
- [ ] Test user(s) added to OAuth consent
- [ ] OAuth 2.0 Client ID created (Web application)
- [ ] Redirect URI configured: `http://localhost:8000/auth/google/callback`
- [ ] Client ID and Secret saved
- [ ] .env.e2e configured with OAuth credentials
- [ ] Environment variables loaded
- [ ] Consent flow completed successfully
- [ ] Tokens verified in database

## Quick Reference

**GCP Console URLs:**
- Project Dashboard: https://console.cloud.google.com/home/dashboard
- APIs Library: https://console.cloud.google.com/apis/library
- OAuth Consent: https://console.cloud.google.com/apis/credentials/consent
- Credentials: https://console.cloud.google.com/apis/credentials

**Required Scopes:**
- `https://www.googleapis.com/auth/gmail.send` - Send email
- `openid` - OpenID Connect
- `email` - User email address
- `profile` - User profile info

**Environment Variables:**
```bash
GOOGLE_CLIENT_ID       # From GCP
GOOGLE_CLIENT_SECRET   # From GCP
GOOGLE_OAUTH_SCOPES    # Space-separated scopes
GOOGLE_REDIRECT_URI    # Must match GCP
PROVIDER_GOOGLE_ENABLED=true
E2E_WORKSPACE_ID       # Test workspace UUID
E2E_ACTOR_ID          # Your email
E2E_RECIPIENT_EMAIL   # Where to send test emails
```

---

**Ready to proceed!** Once OAuth is configured and tokens verified, you can run the E2E test script immediately.
