# Docker Integration

## What this integrates

Multi-stage Docker build for the Relay FastAPI application. Uses Python 3.11 slim base with optimized layer caching for fast rebuilds. Deployed on Railway with automatic health checks.

## Where it's configured

- `Dockerfile` - Multi-stage build definition (builder + production)
- `scripts/start-server.sh` - Uvicorn startup script
- `requirements.txt` + `requirements.in` - Python dependencies
- `pyproject.toml` - Package metadata for observability extras

## Env vars / secrets

| Name | Scope | Where set | Notes |
|------|-------|-----------|-------|
| `PORT` | Runtime | Railway auto-sets | Defaults to 8000 if not set |
| `PYTHONUNBUFFERED` | Build + Runtime | Dockerfile | Ensures real-time log output |
| All other vars | Runtime | Railway dashboard | DATABASE_URL, REDIS_URL, OPENAI_API_KEY, etc. |

## How to verify (60 seconds)

```bash
# 1. Build locally
docker build -t relay-test .
# Should complete without errors in ~2-3 minutes

# 2. Run container locally
docker run -p 8000:8000 -e PORT=8000 relay-test
# Container starts and listens on port 8000

# 3. Test health endpoint
curl http://localhost:8000/_stcore/health
# Returns: {"status":"ok"}

# 4. Check health check passes
docker inspect relay-test --format='{{.State.Health.Status}}'
# Should show: healthy (after 10s start period)
```

## Common failure → quick fix

### Build fails with "No such file or directory"
**Cause:** COPY directive references file that doesn't exist
**Fix:** Check Dockerfile COPY lines match actual repo structure (lines 33-44)

### Build fails with "Could not find a version that satisfies requirement X"
**Cause:** Dependency missing from requirements.txt or version conflict
**Fix:**
```bash
pip-compile requirements.in  # Regenerate requirements.txt
git add requirements.txt
git commit -m "fix: update dependencies"
```

### Container starts but health check fails
**Cause:** Application crashes on startup or health endpoint not responding
**Fix:**
1. Check logs: `docker logs <container-id>`
2. Look for Python tracebacks
3. Verify all required env vars are set (DATABASE_URL, REDIS_URL, etc.)

### Port 8000 already in use (local dev)
**Cause:** Another process using port 8000
**Fix:**
```bash
# Find process
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Kill it or use different port
docker run -p 8001:8000 -e PORT=8000 relay-test
```

## References

- Dockerfile:2-14 - Builder stage with dependency compilation
- Dockerfile:16-63 - Production stage with minimal runtime image
- Dockerfile:56 - Exposed port (8000)
- Dockerfile:59-60 - HEALTHCHECK configuration (30s interval, 5s timeout)
- scripts/start-server.sh - Entry point that starts Uvicorn with `$PORT`
