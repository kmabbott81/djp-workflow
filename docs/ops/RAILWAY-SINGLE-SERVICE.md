# Railway Single-Service Deployment Guide

**Last Updated:** October 12, 2025
**Service Name:** Relay
**Production URL:** https://relay-production-f2a6.up.railway.app

## Overview

This project uses a **single-service Railway deployment** architecture that automatically builds and deploys from the `main` branch on GitHub.

### Architecture Flow

```
GitHub Repository (main branch)
         ↓ (push trigger)
Railway Relay Service
         ↓ (docker build)
Production Container
         ↓ (running on Railway)
Public API Endpoint
```

### Key Components

- **Service:** Relay (single service)
- **Source:** GitHub repository (main branch)
- **Builder:** Docker (multi-stage Dockerfile)
- **Runtime:** Python 3.13 + FastAPI + Uvicorn
- **Dependencies:** PostgreSQL, Redis (separate Railway services)

## Required Environment Variables

The following environment variables must be configured in the Railway Relay service:

### Core Configuration

| Variable | Purpose | Example | Required |
|----------|---------|---------|----------|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql://user:pass@host:port/db` | Yes |
| `REDIS_URL` | Redis connection string | `redis://default:pass@host:port` | Yes |
| `OPENAI_API_KEY` | OpenAI API for GPT-4 planning | `sk-proj-...` | Yes |
| `OAUTH_ENCRYPTION_KEY` | OAuth token encryption | `base64-encoded-32-bytes` | Yes |

### Feature Flags

| Variable | Purpose | Default | Required |
|----------|---------|---------|----------|
| `ACTIONS_ENABLED` | Enable actions execution | `false` | No |
| `TELEMETRY_ENABLED` | Enable metrics collection | `false` | No |
| `PROVIDER_GOOGLE_ENABLED` | Enable Google OAuth | `false` | No |

### Google OAuth (if enabled)

| Variable | Purpose | Required |
|----------|---------|----------|
| `GOOGLE_CLIENT_ID` | Google OAuth client ID | If Google enabled |
| `GOOGLE_CLIENT_SECRET` | Google OAuth client secret | If Google enabled |

### Optional Configuration

| Variable | Purpose | Default |
|----------|---------|---------|
| `PORT` | HTTP server port | `8000` |
| `WEBHOOK_URL` | External webhook endpoint | None |
| `ACTIONS_SIGNING_SECRET` | Webhook signature verification | None |

## How Auto-Deploy Works

### 1. Trigger

Every push to the `main` branch on GitHub automatically triggers a new deployment:

```bash
git push origin main
# → Railway detects push
# → Starts build process
```

### 2. Build Process

Railway executes the multi-stage Dockerfile:

1. **Builder Stage:**
   - Uses `python:3.13-slim` base image
   - Installs system dependencies (gcc, postgresql-dev, etc.)
   - Installs Python packages from `requirements.txt`
   - Compiles native extensions (argon2, asyncpg)

2. **Production Stage:**
   - Uses clean `python:3.13-slim` image
   - Copies only compiled packages from builder
   - Copies application code
   - Exposes port 8000

### 3. Deployment

- Railway replaces the running container with the new build
- Zero-downtime deployment (brief connection pause)
- Health checks verify the new container is responding
- Old container is terminated after health checks pass

### 4. Verification

Monitor deployment in Railway dashboard:
- **Build Logs:** Shows Docker build output
- **Deploy Logs:** Shows application startup (Uvicorn)
- **Status:** Should show "Active" with green indicator

## Health Check Endpoint

The service exposes a health check endpoint for monitoring:

```bash
GET https://relay-production-f2a6.up.railway.app/_stcore/health
```

**Response:**
```json
{
  "status": "ok"
}
```

### Health Check Configuration

Configured in `Dockerfile`:
```dockerfile
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:${PORT:-8000}/_stcore/health')" || exit 1
```

- **Interval:** Checks every 30 seconds
- **Timeout:** 5 seconds max response time
- **Start Period:** 10 seconds grace period on startup
- **Retries:** 3 failed checks before marking unhealthy

## Manual Deployment

If you need to trigger a deployment without pushing to GitHub:

### Prerequisites

Install Railway CLI:
```bash
npm install -g @railway/cli
```

Login to Railway:
```bash
railway login
```

Link to your project:
```bash
cd /path/to/openai-agents-workflows-2025.09.28-v1
railway link
# Select: Relay service
```

### Deploy Command

```bash
railway up
```

This will:
1. Package your local code
2. Upload to Railway
3. Trigger a new build and deployment

**Note:** Manual deployments use your local code state, not GitHub. Use this for testing or emergency hotfixes.

## Monitoring Deployment Status

### Via Railway Dashboard

1. Go to https://railway.app
2. Select your project
3. Click "Relay" service
4. View tabs:
   - **Deployments:** Build and deploy history
   - **Logs:** Real-time application logs
   - **Metrics:** CPU, memory, network usage

### Via Railway CLI

View recent deployments:
```bash
railway status
```

Stream live logs:
```bash
railway logs
```

Check service variables:
```bash
railway variables
```

## Testing the Deployment

### Test Health Endpoint

```bash
curl https://relay-production-f2a6.up.railway.app/_stcore/health
```

Expected: `{"status":"ok"}`

### Test AI Planning Endpoint

Using PowerShell:
```powershell
$body = '{"prompt": "Send an email to test@example.com"}'
Invoke-RestMethod `
  -Uri "https://relay-production-f2a6.up.railway.app/ai/plan" `
  -Method Post `
  -Headers @{
    "Content-Type" = "application/json"
    "Authorization" = "Bearer relay_sk_demo_preview_key"
  } `
  -Body $body
```

Using curl (Linux/Mac):
```bash
curl -X POST https://relay-production-f2a6.up.railway.app/ai/plan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer relay_sk_demo_preview_key" \
  -d '{"prompt": "Send an email to test@example.com"}'
```

Expected: JSON response with action plan from GPT-4

## Troubleshooting

### Build Failures

**Symptom:** Deployment shows "Build Failed"

**Common Causes:**
- Missing dependencies in `requirements.txt`
- Syntax errors in Python code
- Docker build errors

**Solution:**
1. Check build logs in Railway dashboard
2. Fix the error locally
3. Test build locally: `docker build -t test .`
4. Push fix to GitHub

### Deployment Fails Health Checks

**Symptom:** Build succeeds but deployment fails with "Unhealthy"

**Common Causes:**
- Application crashes on startup
- Port binding issues
- Missing environment variables

**Solution:**
1. Check deploy logs in Railway dashboard
2. Look for Python tracebacks or errors
3. Verify all required environment variables are set
4. Test locally with same environment variables

### No Automatic Deployment

**Symptom:** Push to main but no deployment triggered

**Common Causes:**
- Railway GitHub connection broken
- Wrong branch selected in Railway settings

**Solution:**
1. Go to Railway dashboard → Relay service → Settings
2. Check "Source" section
3. Verify GitHub repo and branch are correct
4. Re-connect GitHub if needed

### Application Errors After Deployment

**Symptom:** Deployment succeeds but API returns 500 errors

**Common Causes:**
- Database connection issues
- Missing environment variables
- Code bugs not caught in testing

**Solution:**
1. Check live logs: `railway logs`
2. Look for Python exceptions
3. Verify DATABASE_URL and REDIS_URL are correct
4. Test endpoints manually to isolate issue

## Rollback Procedure

If a deployment introduces bugs:

### Option 1: Quick Rollback (Railway Dashboard)

1. Go to Railway dashboard → Relay service → Deployments
2. Find the last working deployment
3. Click "..." menu → "Redeploy"

### Option 2: Git Revert

```bash
# Find the problematic commit
git log --oneline

# Revert the commit
git revert <commit-hash>

# Push to trigger new deployment
git push origin main
```

### Option 3: Emergency Hotfix

```bash
# Make the fix locally
# ...

# Deploy immediately without waiting for GitHub
railway up
```

## Security Best Practices

### Environment Variables

- **Never commit secrets to GitHub** (API keys, passwords, etc.)
- Store all secrets in Railway environment variables
- Railway encrypts environment variables at rest
- GitHub cannot read Railway environment variables

### API Keys

- Use Railway's built-in secret management
- Rotate API keys periodically
- Set usage limits on OpenAI API keys
- Monitor API usage for unexpected spikes

### Database Access

- Use Railway's internal PostgreSQL service (not exposed publicly)
- Database credentials are auto-generated and managed by Railway
- Access only via internal Railway network

## Performance Optimization

### Docker Build Cache

Railway caches Docker layers between builds for faster deployments:
- Unchanged layers are reused
- Only modified layers are rebuilt
- Typical rebuild time: 1-2 minutes

### Python Package Installation

Packages are compiled once during build:
- Native extensions (argon2, asyncpg) compiled in builder stage
- Compiled packages copied to production image
- No compilation overhead at runtime

### Resource Allocation

Monitor resource usage in Railway dashboard:
- **CPU:** Should stay under 80% average
- **Memory:** Should stay under 80% of allocated
- **Network:** Monitor for unexpected traffic spikes

## Related Documentation

- [Deployment FAQ](./DEPLOYMENT-FAQ.md) - Common questions and solutions
- [README.md](../../README.md) - Project overview and quickstart
- [OPERATIONS.md](../OPERATIONS.md) - Operational procedures

## Support

- **Railway Status:** https://status.railway.app
- **Railway Docs:** https://docs.railway.app
- **Project Issues:** Track in GitHub issues

---

**Migration Note:** This service was consolidated from a previous two-service architecture (djp-workflow + Relay) on October 12, 2025. The djp-workflow service was removed after connecting Relay directly to GitHub, simplifying to a single-service deployment model.
