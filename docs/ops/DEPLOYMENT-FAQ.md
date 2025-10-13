# Railway Deployment FAQ

Common questions and solutions for deploying and managing the Relay service on Railway.

---

## General Questions

### Q: Why isn't my deployment showing up after pushing to GitHub?

**A:** Check the following:

1. **Verify GitHub Connection:**
   - Go to Railway dashboard → Relay service → Settings → Source
   - Confirm the repository and branch are correctly configured
   - Should show: `main` branch connected

2. **Check Build Status:**
   - Go to Deployments tab
   - Look for a new deployment triggered by your commit
   - If no deployment appears, the GitHub webhook may be disconnected

3. **Re-connect GitHub:**
   - Settings → Source → Disconnect
   - Reconnect and select `main` branch

4. **Verify Branch:**
   - Railway only deploys from the configured branch (main)
   - If you pushed to a different branch, merge to main first

### Q: How do I roll back to a previous deployment?

**A:** Two options:

**Option 1: Redeploy Previous Build (Fastest)**
1. Go to Railway dashboard → Relay service → Deployments
2. Find the last working deployment
3. Click the "..." menu → "Redeploy"
4. Railway will restore that exact build

**Option 2: Git Revert (Permanent Fix)**
```bash
# View recent commits
git log --oneline

# Revert the problematic commit
git revert <commit-hash>

# Push to trigger new deployment
git push origin main
```

### Q: Why is my build failing?

**A:** Common causes and solutions:

1. **Missing Python Dependencies:**
   - Error: `ModuleNotFoundError: No module named 'xxx'`
   - Fix: Add package to `requirements.in` and regenerate `requirements.txt`:
     ```bash
     pip-compile requirements.in
     git add requirements.txt
     git commit -m "Add missing dependency"
     git push origin main
     ```

2. **Docker Build Errors:**
   - Check build logs in Railway dashboard
   - Look for `ERROR` lines in the Docker output
   - Common issues: syntax errors, missing files, permission issues

3. **Python Syntax Errors:**
   - Error: `SyntaxError: invalid syntax`
   - Fix: Test locally first with `python -m py_compile src/**/*.py`
   - Use linting: `ruff check src/`

4. **Database Migration Issues:**
   - Error: `relation "xxx" does not exist`
   - Fix: Run migrations in Railway console or locally against Railway DB:
     ```bash
     alembic upgrade head
     ```

### Q: Why does my deployment succeed but API returns 500 errors?

**A:** This means the build succeeded but the application crashes at runtime.

**Diagnosis Steps:**

1. **Check Live Logs:**
   ```bash
   railway logs
   ```
   Or view in Railway dashboard → Logs tab

2. **Look for Python Exceptions:**
   - `KeyError: 'SOME_ENV_VAR'` → Missing environment variable
   - `OperationalError: ... connection refused` → Database connection issue
   - `ImportError: No module named 'xxx'` → Dependency issue

3. **Verify Environment Variables:**
   - Railway dashboard → Variables tab
   - Ensure all required variables are set (see RAILWAY-SINGLE-SERVICE.md)

4. **Test Endpoints Manually:**
   ```bash
   # Test health endpoint first
   curl https://relay-production-f2a6.up.railway.app/_stcore/health

   # If health passes, test your endpoint
   curl -X POST https://relay-production-f2a6.up.railway.app/ai/plan \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer <your-key>" \
     -d '{"prompt": "test"}'
   ```

### Q: How do I add a new environment variable?

**A:** In Railway dashboard:

1. Go to Relay service → Variables tab
2. Click "+ New Variable"
3. Enter name and value
4. Click "Add"
5. **Important:** Railway automatically redeploys after variable changes

**Note:** For sensitive values (API keys), use Railway's "Secret" option to hide values in the UI.

### Q: Can I run migrations before deployment?

**A:** Not automatically with Railway's current setup. Options:

**Option 1: Manual Migration (Recommended)**
```bash
# Connect to Railway environment
railway link

# Run migrations
railway run alembic upgrade head
```

**Option 2: Startup Migration (Not Recommended for Production)**
Add to Dockerfile or startup script:
```bash
alembic upgrade head && uvicorn src.webapi:app
```
⚠️ Risks: Can cause deployment failures if migration fails

### Q: How long does a deployment take?

**A:** Typical timeline:

- **Build:** 1-3 minutes (depending on cache hits)
- **Deploy:** 10-30 seconds
- **Total:** ~2-4 minutes from push to live

**Factors:**
- First build after dependency changes: 3-5 minutes (compiling native extensions)
- Cached builds: 1-2 minutes
- Code-only changes: 1-2 minutes

---

## Troubleshooting Specific Errors

### "No module named 'openai'"

**Cause:** The `openai` package is missing from `requirements.txt`

**Fix:**
```bash
# Add to requirements.in
echo "openai>=1.0.0" >> requirements.in

# Regenerate requirements.txt
pip-compile requirements.in

# Commit and push
git add requirements.in requirements.txt
git commit -m "Add openai dependency"
git push origin main
```

### "Address already in use: 0.0.0.0:8000"

**Cause:** Port 8000 is occupied by another process

**Context:** This only happens in local development, not on Railway

**Fix (Local Development):**
```bash
# Find the process using port 8000
lsof -i :8000  # Mac/Linux
netstat -ano | findstr :8000  # Windows

# Kill the process
kill -9 <PID>  # Mac/Linux
taskkill /PID <PID> /F  # Windows

# Or use a different port
uvicorn src.webapi:app --port 8001
```

### "HEALTHCHECK failed"

**Cause:** The health endpoint is not responding within the timeout

**Common Reasons:**
1. Application crashes on startup
2. Port binding issues
3. Slow startup (database connections, etc.)

**Fix:**

1. **Check Deploy Logs:**
   - Look for Python exceptions during startup
   - Verify Uvicorn starts successfully: `Uvicorn running on http://0.0.0.0:8000`

2. **Increase Health Check Grace Period:**
   Edit `Dockerfile`:
   ```dockerfile
   HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
       CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8000}/_stcore/health')" || exit 1
   ```
   (Increased from 10s to 30s)

3. **Test Health Endpoint Locally:**
   ```bash
   python -m uvicorn src.webapi:app --port 8000
   curl http://localhost:8000/_stcore/health
   ```

### "Authentication failed for user 'postgres'"

**Cause:** Database connection string is incorrect or database is unreachable

**Fix:**

1. **Verify DATABASE_URL:**
   - Railway dashboard → Variables → DATABASE_URL
   - Format: `postgresql://user:password@host:port/database`
   - Should match the connection string from Railway's PostgreSQL service

2. **Check PostgreSQL Service:**
   - Go to PostgreSQL service tile
   - Verify it's running (green status)
   - Click "Connect" to see the correct connection string

3. **Test Connection:**
   ```bash
   railway run python -c "import asyncpg; import asyncio; asyncio.run(asyncpg.connect('$DATABASE_URL'))"
   ```

### "Redis connection refused"

**Cause:** Redis service is not reachable or REDIS_URL is incorrect

**Fix:**

1. **Verify REDIS_URL:**
   - Railway dashboard → Variables → REDIS_URL
   - Format: `redis://user:password@host:port`
   - Should match Redis service connection string

2. **Check Redis Service:**
   - Go to Redis service tile
   - Verify it's running (green status)

3. **Test Connection:**
   ```bash
   railway run python -c "import redis; r = redis.from_url('$REDIS_URL'); print(r.ping())"
   ```

### "JSONDecodeError: Expecting value"

**Cause:** Malformed JSON in request body

**Context:** Common when testing with curl/PowerShell

**Fix:**

**PowerShell (Correct):**
```powershell
$body = '{"prompt": "test"}'
Invoke-RestMethod -Uri "..." -Method Post -Body $body -ContentType "application/json"
```

**Bash/curl (Correct):**
```bash
curl -X POST "..." \
  -H "Content-Type: application/json" \
  -d '{"prompt": "test"}'
```

**Common Mistakes:**
- Missing quotes around JSON
- Using single quotes in PowerShell without escaping
- Newlines breaking the JSON string

---

## Performance Issues

### Q: Why is my API slow?

**A:** Diagnosis steps:

1. **Check Railway Metrics:**
   - Dashboard → Metrics tab
   - Look for: CPU spike, Memory spike, High network latency

2. **Review Application Logs:**
   ```bash
   railway logs | grep "took"
   ```
   Look for slow operations

3. **Database Query Performance:**
   - Enable SQL logging in local testing
   - Check for N+1 queries or missing indexes

4. **OpenAI API Latency:**
   - GPT-4 calls typically take 2-5 seconds
   - Consider caching common prompts
   - Use `gpt-4o-mini` for faster responses (at cost of quality)

### Q: Why is my deployment using so much memory?

**A:** Common causes:

1. **Python Packages:**
   - Large ML libraries (numpy, pandas) consume memory
   - Check: `railway run pip list | grep -E "pandas|numpy"`

2. **Memory Leaks:**
   - Monitor memory over time in Railway metrics
   - If steadily increasing → likely a leak
   - Check for unclosed connections (database, Redis, HTTP clients)

3. **Too Many Workers:**
   - Default Uvicorn config may spawn multiple workers
   - Check: `ps aux | grep uvicorn` in Railway console
   - Limit workers with `--workers 1` in production

**Fix:** Optimize startup command in Dockerfile or Railway settings:
```bash
uvicorn src.webapi:app --host 0.0.0.0 --port $PORT --workers 1
```

---

## Security Questions

### Q: Are my environment variables secure in Railway?

**A:** Yes, Railway encrypts environment variables:

- Encrypted at rest
- Encrypted in transit
- Not visible in build logs
- Not accessible to GitHub webhooks
- Only visible to service at runtime

### Q: Should I commit secrets to GitHub?

**A:** NO, never commit secrets to Git:

**What NOT to commit:**
- API keys (OPENAI_API_KEY)
- Database passwords (DATABASE_URL)
- OAuth secrets (OAUTH_ENCRYPTION_KEY)
- Any credentials or tokens

**What CAN be committed:**
- Public configuration
- Non-sensitive defaults
- Feature flags (ACTIONS_ENABLED)
- Service hostnames (without credentials)

**Best Practice:**
```bash
# Use .env for local development (gitignored)
echo "OPENAI_API_KEY=sk-..." > .env
echo ".env" >> .gitignore

# Use Railway environment variables for production
# (Set in Railway dashboard)
```

### Q: How do I rotate an API key?

**A:** Steps to safely rotate:

1. **Generate New Key:**
   - Create new API key from provider (OpenAI, etc.)

2. **Update Railway:**
   - Dashboard → Variables → Edit OPENAI_API_KEY
   - Paste new key
   - Railway auto-redeploys

3. **Verify Deployment:**
   - Test API endpoint to confirm new key works

4. **Revoke Old Key:**
   - Go to provider dashboard (OpenAI, etc.)
   - Revoke the old key

**Downtime:** ~2-4 minutes during redeployment

---

## Architecture Questions

### Q: What happened to the djp-workflow service?

**A:** It was removed during architecture consolidation on October 12, 2025.

**Previous Setup:**
- djp-workflow: GitHub-connected builder (no public URL)
- Relay: Runtime service (had public URL but no GitHub connection)
- Both services were redundant and confusing

**Current Setup:**
- Single "Relay" service
- Connected directly to GitHub main branch
- Builds and runs in one service
- Simpler, cleaner architecture

### Q: Can I deploy to a staging environment?

**A:** Yes, create a second Railway service:

1. **Create New Service:**
   - Railway dashboard → "+ New" → Service
   - Name: "Relay-Staging"

2. **Connect to Branch:**
   - Settings → Source → Connect GitHub
   - Select `develop` or `staging` branch

3. **Copy Environment Variables:**
   - Use separate database/Redis for isolation
   - Copy other variables from production

4. **Deploy:**
   - Push to staging branch triggers deployment

### Q: How do I run the app locally with Railway's database?

**A:** Use Railway CLI:

```bash
# Install Railway CLI
npm install -g @railway/cli

# Link to project
railway link

# Run locally with Railway environment
railway run python -m uvicorn src.webapi:app --port 8000 --reload
```

This loads all Railway environment variables locally.

---

## Getting Help

### Railway Support

- **Status Page:** https://status.railway.app
- **Documentation:** https://docs.railway.app
- **Discord:** https://discord.gg/railway

### Project Issues

- Report bugs in GitHub Issues
- Tag deployment issues with `deployment` label

### Checking Service Health

```bash
# Quick health check
curl https://relay-production-f2a6.up.railway.app/_stcore/health

# Expected: {"status": "ok"}
```

---

## Quick Reference

### Common Commands

```bash
# Deploy manually
railway up

# View logs
railway logs

# Check service status
railway status

# Run command in Railway environment
railway run <command>

# Connect to database
railway run psql $DATABASE_URL

# Connect to Redis
railway run redis-cli -u $REDIS_URL
```

### Important URLs

- **Production API:** https://relay-production-f2a6.up.railway.app
- **Health Endpoint:** https://relay-production-f2a6.up.railway.app/_stcore/health
- **Railway Dashboard:** https://railway.app

### Related Documentation

- [RAILWAY-SINGLE-SERVICE.md](./RAILWAY-SINGLE-SERVICE.md) - Complete setup guide
- [README.md](../../README.md) - Project overview
- [OPERATIONS.md](../OPERATIONS.md) - Operational procedures

---

**Last Updated:** October 12, 2025
