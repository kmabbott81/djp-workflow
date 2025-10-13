# Codespaces Integration

## What this integrates

GitHub Codespaces and local development UI for testing actions without external APIs. Includes an interactive Dev UI at `/dev/action-runner.html` for executing actions with form inputs.

## Where it's configured

- `CODESPACES.md` - Full Codespaces setup and usage guide
- `static/dev/action-runner.html` - Interactive action testing UI
- `static/dev/action-runner.js` - Client-side action execution logic
- `.devcontainer/` - Devcontainer configuration (if present)
- `scripts/start-server.sh` - Startup script that binds to 0.0.0.0

## Env vars / secrets

| Name | Scope | Where set | Notes |
|------|-------|-----------|-------|
| None required | Dev | N/A | Dev UI works in demo mode without OAuth |

## How to verify (60 seconds)

```bash
# 1. Start local server
python -m uvicorn src.webapi:app --port 8000 --reload
# Should show: Uvicorn running on http://127.0.0.1:8000

# 2. Open Dev UI in browser
open http://localhost:8000/dev/action-runner.html
# Or manually navigate to the URL

# 3. Test action execution via UI
# - Select "webhook.save" action
# - Fill in URL and method fields
# - Click "Execute Action"
# - Should see success response or validation errors

# 4. Verify port forwarding in Codespaces
# Go to Codespaces → Ports tab
# Port 8000 should show "Public" or "Private" with green status

# 5. Access from external (if Codespaces)
# Click port 8000 → "Open in Browser"
# Should load Dev UI at forwarded URL
```

## Common failure → quick fix

### Port 8000 already in use
**Cause:** Another process (old server, Docker, etc.) using port
**Fix:**
```bash
# Find process
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Kill process
kill -9 <PID>  # Mac/Linux
taskkill /PID <PID> /F  # Windows

# Or use different port
python -m uvicorn src.webapi:app --port 8001
```

### Dev UI loads but actions fail with 401
**Cause:** No API key or demo key not working
**Fix:**
- Dev UI should work in "demo mode" (mocked responses)
- If hitting real API, add Authorization header via browser DevTools
- Or use demo mode by setting `ACTIONS_ENABLED=false`

### Codespaces port not forwarding
**Cause:** Port visibility set to "Private" or not auto-forwarded
**Fix:**
1. Go to Codespaces → Ports tab
2. Right-click port 8000 → "Port Visibility" → "Public"
3. Or set in `.devcontainer/devcontainer.json`:
```json
{
  "forwardPorts": [8000],
  "portsAttributes": {
    "8000": {
      "label": "Dev UI",
      "onAutoForward": "openBrowser"
    }
  }
}
```

### Action Runner UI not found (404)
**Cause:** Static files not served or wrong path
**Fix:**
- Verify `static/dev/` directory exists with HTML/JS files
- Check FastAPI static file mounting in `src/webapi.py`:
```python
from fastapi.staticfiles import StaticFiles
app.mount("/dev", StaticFiles(directory="static/dev"), name="dev")
```

## Dev UI vs OAuth mode

| Feature | Demo Mode (Dev UI) | OAuth Mode (Production) |
|---------|-------------------|-------------------------|
| Setup | None - works immediately | Requires Google OAuth setup |
| Authentication | Mocked | Real OAuth2 flow |
| Gmail API | Simulated responses | Real Gmail API calls |
| Use case | Local testing, UI dev | End-to-end integration |

**To enable OAuth in dev:**
1. Set `PROVIDER_GOOGLE_ENABLED=true`
2. Set `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET`
3. Follow CODESPACES.md OAuth setup section

## References

- CODESPACES.md - Complete Codespaces setup guide (startup, port forwarding, OAuth)
- static/dev/action-runner.html - Interactive action testing UI
- static/dev/action-runner.js:50-120 - Action execution and form handling
- scripts/start-server.sh - Uvicorn startup with 0.0.0.0 binding for Codespaces
