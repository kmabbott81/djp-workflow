# Phase 3 Setup Checklist

**Quick reference for setting up E2E testing environment**

## Prerequisites

- [ ] Phase 1 & 2 complete (90+ tests passing)
- [ ] Rollout infrastructure deployed (Sprint 53.5)
- [ ] Gmail OAuth configured (Sprint 53)

## Infrastructure Setup

### 1. Redis

**Local:**
```bash
docker run -d -p 6379:6379 --name redis redis:alpine
redis-cli ping  # Should return PONG
```

**Railway (recommended):**
```bash
# Add Redis service via Railway dashboard
# Copy connection string to REDIS_URL
```

**Initialize:**
```bash
redis-cli SET flags:google:rollout_percent 0
redis-cli SET flags:google:rollout_enabled true
```

### 2. Prometheus + Pushgateway

**Local:**
```bash
# Pushgateway
docker run -d -p 9091:9091 --name pushgateway prom/pushgateway

# Prometheus
cat > prometheus.yml <<EOF
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'pushgateway'
    static_configs:
      - targets: ['localhost:9091']
EOF

docker run -d -p 9090:9090 --name prometheus \
  -v $(pwd)/prometheus.yml:/etc/prometheus/prometheus.yml \
  prom/prometheus

# Verify
curl http://localhost:9091/metrics
curl http://localhost:9090/-/healthy
```

**Railway:**
```bash
# Deploy via Railway template (Prometheus + Pushgateway)
# Or use external provider (Grafana Cloud, Datadog, etc.)
```

### 3. Database (PostgreSQL)

Already set up from Sprint 53. Verify OAuth tokens table:

```sql
SELECT provider, workspace_id, actor_id, created_at
FROM oauth_tokens
WHERE provider = 'google'
LIMIT 1;
```

## Gmail OAuth Setup

### 1. GCP Console

1. Go to https://console.cloud.google.com/apis/credentials
2. Create OAuth 2.0 Client ID (if not exists)
3. Add authorized redirect URI: `http://localhost:8000/auth/google/callback` (or your domain)
4. Note Client ID and Client Secret

### 2. OAuth Scopes

Required scopes:
- `https://www.googleapis.com/auth/gmail.send`
- `https://www.googleapis.com/auth/userinfo.email`

### 3. Test Account Authorization

```bash
# Start server
python -m uvicorn src.webapi:app --port 8000

# Visit consent URL (replace with your values)
open "http://localhost:8000/auth/google/consent?workspace_id=test-workspace&actor_id=your-email@example.com"

# Follow OAuth flow, grant permissions
# Verify tokens stored in database
```

## Environment Variables

Create `.env` file:

```bash
# Provider
PROVIDER_GOOGLE_ENABLED=true
GOOGLE_CLIENT_ID=<from-gcp-console>
GOOGLE_CLIENT_SECRET=<from-gcp-console>

# Internal-Only Controls
GOOGLE_INTERNAL_ONLY=true
GOOGLE_INTERNAL_ALLOWED_DOMAINS=yourdomain.com
GOOGLE_INTERNAL_TEST_RECIPIENTS=your-test-email@gmail.com

# Rollout
ROLLOUT_DRY_RUN=true  # Start in dry-run mode
REDIS_URL=redis://localhost:6379

# Telemetry
TELEMETRY_ENABLED=true
PROMETHEUS_PUSHGATEWAY_URL=http://localhost:9091

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname

# Actions
ACTIONS_ENABLED=true
ACTIONS_SIGNING_SECRET=$(openssl rand -base64 32)

# E2E Test Config
E2E_WORKSPACE_ID=test-workspace-uuid
E2E_ACTOR_ID=your-email@example.com
E2E_RECIPIENT_EMAIL=your-test-email@gmail.com
```

Load environment:
```bash
export $(cat .env | xargs)
```

## Verification Steps

### 1. Redis Connection

```bash
redis-cli ping
redis-cli GET flags:google:rollout_percent  # Should return "0"
```

### 2. Prometheus Connection

```bash
curl http://localhost:9090/-/healthy  # Should return "Prometheus is Healthy"
curl http://localhost:9091/metrics | grep -i rollout  # Should show metrics
```

### 3. Database Connection

```bash
python -c "
import os
from sqlalchemy import create_engine
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute('SELECT 1')
    print('Database connected:', result.fetchone()[0] == 1)
"
```

### 4. OAuth Tokens

```bash
python -c "
import asyncio
import os
from src.auth.oauth.tokens import OAuthTokenCache

async def check():
    cache = OAuthTokenCache()
    tokens = await cache.get_tokens_with_auto_refresh(
        'google',
        os.getenv('E2E_WORKSPACE_ID'),
        os.getenv('E2E_ACTOR_ID')
    )
    print('Tokens found:', tokens is not None)
    if tokens:
        print('Access token length:', len(tokens.get('access_token', '')))

asyncio.run(check())
"
```

### 5. Adapter Initialization

```bash
python -c "
from src.actions.adapters.google import GoogleAdapter
adapter = GoogleAdapter()
print('Adapter enabled:', adapter.enabled)
print('Internal only:', adapter.internal_only)
print('Allowed domains:', adapter.internal_allowed_domains)
"
```

## Run E2E Tests

### Dry-Run First (Preview Only)

```bash
python scripts/e2e_gmail_test.py \
  --scenarios 1,2,3 \
  --dry-run \
  --verbose
```

### Full Test (With Gmail Sends)

```bash
python scripts/e2e_gmail_test.py \
  --scenarios all \
  --verbose
```

### Check Results

```bash
# View logs
tail -f logs/e2e_test.log

# View results JSON
cat logs/e2e_results_*.json | jq '.results[] | {scenario, status, duration_seconds}'

# Check Gmail inbox
# You should receive test emails
```

## Monitor Telemetry

### Prometheus Queries

```bash
# Check action metrics
curl 'http://localhost:9090/api/v1/query?query=action_execution_total' | jq .

# Check MIME builder metrics
curl 'http://localhost:9090/api/v1/query?query=gmail_mime_build_seconds_count' | jq .

# Check error rate
curl 'http://localhost:9090/api/v1/query?query=action_error_total' | jq .
```

### Pushgateway

```bash
curl http://localhost:9091/metrics | grep -E "(rollout|gmail|action)"
```

### Logs

```bash
# Application logs
tail -f logs/*.jsonl

# Audit logs
tail -f audit/audit-$(date +%Y-%m-%d).jsonl | jq 'select(.event=="rollout_decision")'

# Controller logs (if running)
tail -f logs/rollout_controller.log | grep -E "(DRY_RUN|promotion|rollback)"
```

## Troubleshooting

### OAuth Tokens Expired

```bash
# Tokens auto-refresh, but if issues:
# 1. Delete expired tokens
DELETE FROM oauth_tokens WHERE provider = 'google' AND workspace_id = 'test-workspace';

# 2. Re-authorize via consent flow
open "http://localhost:8000/auth/google/consent?workspace_id=test-workspace&actor_id=your-email@example.com"
```

### Redis Connection Failed

```bash
# Check Redis is running
docker ps | grep redis

# Check connection
redis-cli -u $REDIS_URL ping

# Restart if needed
docker restart redis
```

### Prometheus Not Scraping

```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets | jq '.data.activeTargets[] | {job, health}'

# Check Pushgateway metrics
curl http://localhost:9091/metrics
```

### Gmail API Errors

```bash
# Check quota
# Visit: https://console.cloud.google.com/apis/api/gmail.googleapis.com/quotas

# Common issues:
# - Daily send limit (100-500 for new accounts)
# - OAuth consent screen not published (test mode limits to 100 users)
# - Missing scopes in OAuth token
```

## Success Criteria

Before proceeding to Phase 4:

- [ ] All 8 E2E scenarios pass (or expected errors for validation tests)
- [ ] Test emails received in Gmail inbox
- [ ] Prometheus metrics flowing (check `/metrics` endpoint)
- [ ] Controller observes in dry-run mode (check logs)
- [ ] No unexpected errors in logs
- [ ] P95 latency < 2 seconds (check metrics)
- [ ] Rollout percent stays at 0% (dry-run confirmation)

## Next Steps

Once checklist complete:
1. Run E2E tests for 24-48 hours (monitor stability)
2. Review metrics and logs
3. If stable, proceed to Phase 4 (Observability)
4. If issues, debug and iterate

---

**Quick Start (TL;DR):**

```bash
# 1. Infrastructure
docker run -d -p 6379:6379 redis:alpine
docker run -d -p 9091:9091 prom/pushgateway
redis-cli SET flags:google:rollout_percent 0

# 2. Environment
export $(cat .env | xargs)

# 3. OAuth
python -m uvicorn src.webapi:app --port 8000 &
open "http://localhost:8000/auth/google/consent?workspace_id=test&actor_id=you@example.com"

# 4. Test
python scripts/e2e_gmail_test.py --scenarios all --verbose

# 5. Monitor
tail -f logs/e2e_test.log
curl http://localhost:9090/api/v1/query?query=action_execution_total
```

Done! 🚀
