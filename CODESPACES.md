# 🚀 GitHub Codespaces - One-Click Dev UI Access

**Zero-setup browser-based testing for Gmail and Microsoft send actions**

## Quick Start (Mobile-Friendly)

### Step 1: Open Codespace
1. Go to: https://github.com/kmabbott81/djp-workflow
2. Click **Code** → **Codespaces** → **Create codespace on feat/rollout-infrastructure**
3. Wait 60-90 seconds for environment to build

### Step 2: Access Dev UI
The browser should **auto-open** the Dev UI when ready. If not, copy the URL from the terminal:

```
🚀 Dev UI ready at: https://<codespace-name>-8000.<region>.githubpreview.dev/static/dev/action-runner.html
```

**Example URL:**
```
https://upgraded-space-giggle-5jq7wrpxv7fxr6-8000.app.github.dev/static/dev/action-runner.html
```

### Step 3: Test Actions
1. **Select Action:** Choose `gmail.send` or `outlook.send` from dropdown
2. **Fill Form:** Enter recipient, subject, body (HTML supported)
3. **Preview:** Click "Preview" to see rendered email
4. **Execute (Demo):** Click "Execute (Demo Mode)" to save to outbox (no actual send)
5. **View Outbox:** Check "Demo Outbox" section to see saved emails

## Features Available in Codespaces

✅ **Gmail Send Action** (demo mode - no real sends)
✅ **Outlook Send Action** (demo mode - no real sends)
✅ **HTML Email Preview** (sanitized iframe rendering)
✅ **Attachment Support** (multi-file, base64 encoded in browser)
✅ **Demo Outbox** (localStorage persistence)
✅ **OAuth Status** (auto-detects connection, falls back to demo mode)

## No Manual Setup Required

The Codespace automatically:
- ✅ Installs Python 3.11 + dependencies
- ✅ Starts Redis on port 6379
- ✅ Starts FastAPI server on port 8000 (public)
- ✅ Forwards ports with public visibility
- ✅ Opens browser to Dev UI
- ✅ Sets environment variables (ACTIONS_ENABLED=true, DEV_MODE=true)

## URL Template

Your Codespace URL follows this pattern:

```
https://<CODESPACE_NAME>-8000.<REGION>.githubpreview.dev/static/dev/action-runner.html
```

Where:
- `<CODESPACE_NAME>` = Auto-generated (e.g., `upgraded-space-giggle-5jq7wrpxv7fxr6`)
- `<REGION>` = Auto-assigned (e.g., `app`, `preview`)
- Port `8000` = FastAPI server (always public)

## Troubleshooting

### Issue: "This site can't be reached" or 401 Unauthorized
**Fix:** Port 8000 must be **Public**. To check:
1. In VS Code, click **PORTS** tab (bottom panel)
2. Find port 8000 row
3. Right-click → **Port Visibility** → **Public**

### Issue: "Actions feature not enabled"
**Fix:** The `ACTIONS_ENABLED=true` env var should be set automatically. If not:
```bash
export ACTIONS_ENABLED=true
export TELEMETRY_ENABLED=true
```

### Issue: Server not starting automatically
**Fix:** Check startup logs:
```bash
tail -f /tmp/codespaces-logs/uvicorn.log
```

Or manually start the server:
```bash
bash .devcontainer/startup.sh
```

### Issue: OAuth status shows "Unknown"
**Expected:** Codespaces don't have OAuth secrets configured. Demo mode is automatically enabled, so you can still test the full UI flow.

## Alternative Access URLs

From your Codespace, you can also access:

- **API Root:** `https://<codespace>-8000.<region>.githubpreview.dev/`
- **API Docs:** `https://<codespace>-8000.<region>.githubpreview.dev/docs`
- **Health Check:** `https://<codespace>-8000.<region>.githubpreview.dev/_stcore/health`
- **Metrics:** `https://<codespace>-8000.<region>.githubpreview.dev/metrics`

## Mobile Usage Tips

1. **Bookmark the URL:** Once Codespace is created, bookmark the Dev UI URL for quick access
2. **Port stays public:** The port visibility persists across Codespace stops/starts
3. **Auto-saves to outbox:** Demo mode saves all test emails to localStorage (persists in same browser)
4. **No OAuth needed:** Demo mode works without any credentials - perfect for testing UI flows

## Stopping the Codespace

When done testing:
1. Go to https://github.com/codespaces
2. Click **•••** next to your Codespace → **Stop codespace**

**Note:** Codespaces auto-stop after 30 minutes of inactivity (configurable)

## Support

For issues with the Dev UI itself:
- Check: `docs/evidence/sprint-54/DEV-PREVIEW-GUIDE.md`
- Logs: `/tmp/codespaces-logs/uvicorn.log`

For Codespaces setup issues:
- GitHub Docs: https://docs.github.com/en/codespaces
- This repo: File an issue at https://github.com/kmabbott81/djp-workflow/issues

---

**Last Updated:** Sprint 55 Week 3
**Status:** ✅ Ready for mobile testing
