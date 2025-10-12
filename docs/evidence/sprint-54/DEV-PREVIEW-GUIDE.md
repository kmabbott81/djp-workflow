# Dev Preview UI - Usage Guide

**Sprint 55 Week 3 Deliverable**
**PR:** #36 (feat/rollout-infrastructure → main)

## Overview

The Dev Preview UI provides a browser-based interface for testing email actions without needing to configure OAuth or send actual emails. Perfect for:
- Development testing
- QA validation
- Demo presentations
- Integration testing

## Quick Start

### Option 1: GitHub Codespaces (Zero Setup)

1. **Open in Codespaces**
   ```
   Click "Code" → "Codespaces" → "Create codespace on feat/rollout-infrastructure"
   ```

2. **Wait for auto-boot** (30-60 seconds)
   - Python 3.11 environment
   - Redis server
   - FastAPI server on port 8000

3. **Access Dev UI**
   ```
   https://<your-codespace>-8000.app.github.dev/static/dev/action-runner.html
   ```

### Option 2: Railway Preview Deploy (Auto-deployed on PRs)

1. **Check PR comments** for preview URL
2. **Access Dev UI**
   ```
   https://<preview-url>.up.railway.app/static/dev/action-runner.html
   ```

### Option 3: Local Development

1. **Start server with required env vars**
   ```bash
   export ACTIONS_ENABLED=true
   export TELEMETRY_ENABLED=true
   export REDIS_URL=redis://localhost:6379
   uvicorn src.webapi:app --reload --port 8000
   ```

2. **Access Dev UI**
   ```
   http://localhost:8000/static/dev/action-runner.html
   ```

## Features

### 1. Action Selection
- Dropdown lists all available actions (gmail.send, outlook.send, etc.)
- Auto-discovers actions from `/actions` endpoint
- Shows OAuth status per provider

### 2. Email Composition
- **To/Cc/Bcc:** Standard email fields (comma-separated for multiple)
- **Subject:** Email subject line
- **Body:** HTML or plain text (supports full HTML formatting)
- **Attachments:** Multi-file upload with base64 encoding in browser

### 3. Preview Mode
- **Click "Preview"** to render email without sending
- Shows sanitized HTML in sandboxed iframe
- Displays recipient fields, subject, and body
- Generates `preview_id` for execute step

### 4. Demo Mode
- **Click "Execute (Demo Mode)"** to save email to local outbox
- No actual sends - safe for testing
- Emails saved to demo outbox (localStorage or `/dev/outbox`)
- View saved emails in "Demo Outbox" section

### 5. Demo Outbox
- Lists all emails saved in demo mode
- Shows timestamp, action, recipient, subject, status
- **Click "Refresh"** to reload outbox
- Persists across sessions (localStorage)

## OAuth Status

The UI shows OAuth connection status per provider:

- **✅ Connected:** OAuth tokens exist, real sends possible
- **⚠️ Not Connected:** Demo mode automatically enabled
- **ℹ️ Unknown:** Status check unavailable, demo mode fallback

**Note:** Codespaces and Railway preview environments default to demo mode (no OAuth secrets configured).

## Testing Scenarios

### Scenario A: Preview HTML Email with Attachment

1. Select `gmail.send` action
2. Fill in recipient: `test@example.com`
3. Subject: `Test Email with Attachment`
4. Body:
   ```html
   <h1>Hello!</h1>
   <p>This is a test email with <strong>bold</strong> text.</p>
   <ul>
     <li>Item 1</li>
     <li>Item 2</li>
   </ul>
   ```
5. Attach a file (PDF, image, etc.)
6. **Click "Preview"**
7. **Verify:** Email renders correctly in preview box

### Scenario B: Demo Mode Execution

1. Select `outlook.send` action
2. Fill in recipient: `demo@example.com`
3. Subject: `Demo Mode Test`
4. Body: `This email will be saved, not sent.`
5. **Click "Execute (Demo Mode)"**
6. **Verify:** Success message shows, outbox updates

### Scenario C: Multiple Recipients (Cc/Bcc)

1. Select `gmail.send` action
2. To: `primary@example.com`
3. Cc: `cc1@example.com, cc2@example.com`
4. Bcc: `bcc@example.com`
5. **Click "Preview"**
6. **Verify:** All recipients shown in preview

## File Structure

```
static/dev/
  action-runner.html      # Main UI (HTML/CSS)
  action-runner.js        # Client-side logic (vanilla JS)

.devcontainer/
  devcontainer.json       # Codespaces config (Python 3.11, Redis)

.github/workflows/
  preview-deploy.yml      # Railway preview deploy on PRs

src/
  webapi.py               # FastAPI server (static mount + /dev/outbox endpoint)
```

## API Endpoints Used

- **GET /actions** - List available actions
- **POST /actions/preview** - Preview action (no execution)
- **POST /actions/execute** - Execute action (real or demo)
- **GET /oauth/{provider}/status** - Check OAuth connection
- **GET /dev/outbox** - List demo outbox items

## Security Notes

- **Sandboxed preview:** HTML rendered in iframe with `sandbox="allow-same-origin"`
- **CSP headers:** Content Security Policy prevents XSS
- **Base64 in browser:** Attachments encoded client-side, never touch server
- **No secrets in UI:** OAuth tokens never exposed to client
- **Demo mode default:** No accidental sends without OAuth

## Troubleshooting

### Issue: "Actions feature not enabled"
**Fix:** Set `ACTIONS_ENABLED=true` environment variable

### Issue: Preview button stuck "Previewing..."
**Fix:** Check browser console for errors, verify `/actions/preview` endpoint accessible

### Issue: Demo outbox empty after execute
**Fix:** Check localStorage in browser DevTools (Application → Local Storage)

### Issue: OAuth status always "Unknown"
**Fix:** Ensure REDIS_URL set and reachable (OAuth state cache)

### Issue: Attachments not encoding
**Fix:** Check file size (<10 MB recommended), verify browser File API support

## Next Steps

After testing the Dev UI:

1. **Configure OAuth** for real sends (see `docs/specs/OAUTH-SETUP-GUIDE.md`)
2. **Run E2E tests** (see `scripts/e2e_gmail_test.py`)
3. **Enable rollout controller** (set `ROLLOUT_CONTROLLER_ENABLED=true`)
4. **Monitor metrics** (Prometheus at `/metrics`)

## Support

For issues or questions:
- **Sprint 55 context:** See `docs/planning/SPRINT-54-PLAN.md`
- **API docs:** https://relay-production-f2a6.up.railway.app/docs
- **GitHub Issues:** https://github.com/kmabbott81/djp-workflow/issues

---

**Last Updated:** Sprint 55 Week 3
**Status:** ✅ Complete - Ready for QA
