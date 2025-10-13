# Railway Integration

## What this integrates

Single-service cloud deployment platform ("Relay" service) that automatically builds from Dockerfile and deploys on every push to GitHub `main` branch. Provides PostgreSQL and Redis as connected services.

## Where it's configured

- Railway Dashboard → Relay service → Settings → Source (GitHub connection)
- Railway Dashboard → Relay service → Variables (environment configuration)
- Dockerfile - Build configuration used by Railway
- `src/webapi.py:274-275` - Health endpoint (`/_stcore/health`)

## Env vars / secrets

| Name | Scope | Where set | Notes |
|------|-------|-----------|-------|
| `OPENAI_API_KEY` | Runtime | Railway Variables | GPT-4 API access |
| `DATABASE_URL` | Runtime | Railway Variables (auto) | PostgreSQL connection from Railway service |
| `REDIS_URL` | Runtime | Railway Variables (auto) | Redis connection from Railway service |
| `OAUTH_ENCRYPTION_KEY` | Runtime | Railway Variables | Base64-encoded 32-byte key for token encryption |
| `ACTIONS_ENABLED` | Runtime | Railway Variables | Feature flag (default: false) |
| `TELEMETRY_ENABLED` | Runtime | Railway Variables | Metrics collection (default: false) |
| `PROVIDER_GOOGLE_ENABLED` | Runtime | Railway Variables | Google OAuth (default: false) |
| `PORT` | Runtime | Railway auto-sets | App listens on this port (typically 8000) |

## How to verify (60 seconds)

```bash
# 1. Check service health
curl https://relay-production-f2a6.up.railway.app/_stcore/health
# Returns: {"status":"ok"}

# 2. View recent deployments
# Go to Railway → Relay service → Deployments tab
# Should show recent builds with "GitHub push" trigger

# 3. Check environment variables
railway variables
# Should list all configured vars (values hidden for secrets)

# 4. Test API endpoint
curl -X POST https://relay-production-f2a6.up.railway.app/ai/plan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer relay_sk_demo_preview_key" \
  -d '{"prompt":"test email"}'
# Should return action plan JSON

# 5. View live logs
railway logs
# Shows real-time application logs
```

## Common failure → quick fix

### Deploy succeeds but API returns 500
**Cause:** Missing environment variable or runtime error
**Fix:**
1. Check Railway → Service → Logs for Python exceptions
2. Verify all required vars are set in Variables tab
3. Common missing vars: DATABASE_URL, REDIS_URL, OPENAI_API_KEY

### Build fails with dependency error
**Cause:** Missing package in requirements.txt
**Fix:**
```bash
# Add package to requirements.in
echo "missing-package>=1.0.0" >> requirements.in
# Regenerate requirements.txt
pip-compile requirements.in
# Commit and push
git add requirements.in requirements.txt
git commit -m "fix: add missing-package"
git push origin main
```

### Health check failing
**Cause:** App not binding to `$PORT` or crashes on startup
**Fix:**
1. Check start-server.sh uses `${PORT:-8000}`
2. View deployment logs for startup errors
3. Verify Dockerfile CMD calls start-server.sh correctly

### Rollback needed
**Fix:**
1. Go to Railway → Deployments tab
2. Find last working deployment
3. Click "..." menu → "Redeploy"
**Note:** Railway redeploys the exact same build (instant)

## References

- Railway Relay Service → Settings → Source - GitHub main branch connection
- Railway Relay Service → Variables - All runtime environment configuration
- Dockerfile:56 - Exposed port 8000 (Railway overrides with $PORT)
- Dockerfile:59-60 - Health check calls `/_stcore/health`
- src/webapi.py:274-275 - Health endpoint implementation
- docs/ops/RAILWAY-SINGLE-SERVICE.md - Detailed Railway setup guide
