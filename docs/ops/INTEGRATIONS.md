# Integrations Overview

> **📊 Automated Monitoring:** This documentation is monitored by [Integration Docs Drift Detection](.github/workflows/integration-docs-check.yml) (on push) and [Monthly Audit](.github/workflows/integration-docs-audit.yml) (issues-based review).

This document provides a quick reference to all external systems integrated with this repository. Each integration has a one-pager with configuration details, verification steps, and troubleshooting guidance.

## At-a-Glance Matrix

| Integration | Where Config Lives | Key Env Vars/Secrets | Primary Files | Health/Verify | Common Failure → Fix |
|-------------|-------------------|---------------------|---------------|---------------|---------------------|
| **Docker** | `Dockerfile` | `PORT` (runtime) | `Dockerfile`, `scripts/start-server.sh` | `curl localhost:8000/_stcore/health` | Build fails → check `requirements.txt` completeness |
| **GitHub** | `.github/` | `GITHUB_TOKEN` (auto) | `.github/workflows/*.yml` | Check Actions tab | Webhook disconnected → reconnect in Railway settings |
| **GitHub Actions** | `.github/workflows/` | `DATABASE_PUBLIC_URL`, `RAILWAY_TOKEN` | `ci.yml`, `backup.yml`, `uptime.yml` | View workflow runs | Workflow skipped → check var gates (BACKUP_ENABLED) |
| **Railway** | Railway dashboard | `OPENAI_API_KEY`, `DATABASE_URL`, `REDIS_URL`, `OAUTH_ENCRYPTION_KEY` | `Dockerfile`, `src/webapi.py` | `curl https://relay-production-f2a6.up.railway.app/_stcore/health` | Deploy fails → check build logs; missing env var |
| **Redis** | Railway service | `REDIS_URL` (runtime) | `src/rollout/controller.py`, `src/auth/oauth_state_context.py` | `redis-cli -u $REDIS_URL PING` | Connection refused → verify REDIS_URL format |
| **Postgres** | Railway service | `DATABASE_URL` (runtime) | `src/db/connection.py`, `migrations/` | `psql $DATABASE_URL -c "SELECT 1"` | Auth failed → check DATABASE_URL credentials |
| **OpenAI** | Railway vars | `OPENAI_API_KEY` (runtime) | `src/ai/planner.py`, `requirements.txt` | `curl -X POST .../ai/plan` | "No module 'openai'" → add to requirements.txt |
| **Observability** | `prometheus.yml`, `src/telemetry/prom.py` | `TELEMETRY_ENABLED` (runtime) | `src/telemetry/prom.py`, `observability/templates/*.yml` | `curl localhost:9090/metrics` | Metrics missing → set TELEMETRY_ENABLED=true |
| **Codespaces** | `.devcontainer/` (if present), `CODESPACES.md` | None (local dev) | `static/dev/action-runner.*` | Open `localhost:8000/dev/action-runner.html` | Port conflict → kill process on 8000 |

## System Diagram

```mermaid
graph TB
    subgraph "Development"
        CS[Codespaces Dev UI<br/>localhost:8000/dev]
    end

    subgraph "Source Control"
        GH[GitHub Repository<br/>main branch]
    end

    subgraph "CI/CD"
        GA[GitHub Actions<br/>ci.yml, backup.yml, etc.]
    end

    subgraph "Production Platform"
        RLY[Railway Relay Service<br/>Auto-deploy on push]
        DOCKER[Docker Build<br/>Multi-stage: builder + prod]
    end

    subgraph "Runtime Services"
        API[FastAPI Application<br/>Port 8000<br/>src/webapi.py]
        REDIS[(Redis<br/>Rate limiting<br/>OAuth state)]
        PG[(PostgreSQL<br/>Token storage<br/>Audit logs)]
    end

    subgraph "External Services"
        OAI[OpenAI API<br/>GPT-4 Planning]
        PROM[Prometheus/Grafana<br/>Observability Stack]
    end

    GH -->|Push to main| RLY
    GH -->|Trigger| GA
    RLY -->|Build| DOCKER
    DOCKER -->|Deploy| API
    API -->|Connect| REDIS
    API -->|Connect| PG
    API -->|Call| OAI
    API -->|Export metrics| PROM
    CS -.->|Local testing| API

    style API fill:#e1f5ff
    style DOCKER fill:#fff4e1
    style RLY fill:#ffe1f5
    style OAI fill:#e1ffe1
    style PROM fill:#f5e1ff
```

## Integration One-Pagers

- [Docker](./integrations/DOCKER.md) - Multi-stage build, health checks, port configuration
- [GitHub](./integrations/GITHUB.md) - Repository settings, branch protection, PR workflows
- [GitHub Actions](./integrations/GITHUB_ACTIONS.md) - CI/CD workflows, var-gated automation, secrets
- [Railway](./integrations/RAILWAY.md) - Single-service deployment, environment variables, rollback
- [Redis](./integrations/REDIS.md) - Rate limiting, OAuth state management, connection pooling
- [Postgres](./integrations/POSTGRES.md) - Token storage, migrations, backup/restore
- [OpenAI](./integrations/OPENAI.md) - GPT-4 planning, API key management, cost control
- [Observability](./integrations/OBSERVABILITY.md) - Prometheus metrics, Grafana dashboards, alerts
- [Codespaces](./integrations/CODESPACES.md) - Dev UI, local environment setup

## Quick Verification Checklist

Run these commands to verify all integrations in 60 seconds:

```bash
# 1. Docker build succeeds
docker build -t test . && echo "✓ Docker build OK"

# 2. Production API health
curl https://relay-production-f2a6.up.railway.app/_stcore/health | grep "ok" && echo "✓ Railway deployment OK"

# 3. Redis connectivity (requires REDIS_URL env var)
redis-cli -u "$REDIS_URL" PING | grep PONG && echo "✓ Redis OK"

# 4. Postgres connectivity (requires DATABASE_URL env var)
psql "$DATABASE_URL" -c "SELECT 1" | grep "1 row" && echo "✓ Postgres OK"

# 5. OpenAI integration (requires API key + auth)
curl -X POST https://relay-production-f2a6.up.railway.app/ai/plan \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer relay_sk_demo_preview_key" \
  -d '{"prompt":"test"}' | grep "intent" && echo "✓ OpenAI OK"

# 6. Metrics endpoint (if TELEMETRY_ENABLED=true)
curl http://localhost:9090/metrics | grep "http_requests_total" && echo "✓ Observability OK"
```

## Common Cross-Integration Issues

### Issue: "Everything builds locally but fails on Railway"

**Causes:**
- Missing environment variable in Railway dashboard
- Dependency not in `requirements.txt`
- Port mismatch (Railway uses `$PORT`, not hardcoded 8000)

**Fix:**
1. Check Railway → Variables tab for missing vars
2. Verify `requirements.txt` includes all runtime deps
3. Ensure `start-server.sh` uses `${PORT:-8000}`

### Issue: "Tests pass but Docker build fails"

**Causes:**
- Dev dependencies in `requirements.txt` causing conflict
- Missing system packages in Dockerfile (gcc, postgresql-dev, etc.)
- Multi-stage build copying wrong files

**Fix:**
1. Split dev deps into `requirements-dev.txt`
2. Add missing `apt-get install` lines to Dockerfile builder stage
3. Verify `COPY` directives match actual repo structure

### Issue: "Metrics not showing up in Prometheus"

**Causes:**
- `TELEMETRY_ENABLED` not set to `true`
- `prometheus-client` not installed
- Metrics endpoint not exposed

**Fix:**
1. Set `TELEMETRY_ENABLED=true` in Railway vars
2. Add `pip install -e ".[observability]"` to Dockerfile
3. Verify `/metrics` endpoint returns data: `curl localhost:9090/metrics`

### Issue: "GitHub Actions workflow not running"

**Causes:**
- Workflow has var gate disabled (e.g., `BACKUP_ENABLED: false`)
- Workflow only runs on `main` branch, but you're on a feature branch
- Workflow scheduled but not time yet

**Fix:**
1. Check workflow file for `if:` conditions with env vars
2. Merge to main or update workflow to trigger on your branch
3. For scheduled workflows, trigger manually via Actions tab

## Related Documentation

- [Railway Single-Service Setup](./RAILWAY-SINGLE-SERVICE.md) - Detailed Railway deployment guide
- [Deployment FAQ](./DEPLOYMENT-FAQ.md) - Common deployment questions
- [Operations Guide](../OPERATIONS.md) - Day-to-day operational procedures
- [Codespaces Setup](../../CODESPACES.md) - Full Codespaces development guide

---

**Last Updated:** 2025-10-12
