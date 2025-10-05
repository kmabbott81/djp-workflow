# On-Call 10-Minute Checklist

Quick diagnostic guide for DJP Workflow staging incidents.

## 🚨 Incident Response (First 10 Minutes)

### 1. Check Service Health (30 seconds)

```bash
# Health check
curl https://relay-production-f2a6.up.railway.app/_stcore/health

# Expected: {"ok":true}
# If non-200 or timeout → Service is DOWN
```

### 2. Review Grafana Golden Signals (2 minutes)

**Access:** http://localhost:3000 (if local) or Grafana Cloud

**Check these panels in order:**

1. **Error Rate** - Is it > 1%?
   - Yes → Check logs for exceptions (Step 4)
   - No → Continue

2. **P95 Latency** - Is it > 500ms?
   - Yes → Check resource limits (Step 5)
   - No → Continue

3. **P99 Latency** - Is it > 1s?
   - Yes → Potential cold starts or resource contention
   - No → Continue

4. **Request Rate** - Unexpected spike or drop?
   - Spike → Possible traffic surge
   - Drop → Possible upstream issue

### 3. Check Recent Deployments (1 minute)

```bash
# List recent Railway deployments
railway status

# Check last deployment time
railway logs --lines 10 | head -n 5
```

**Questions:**
- Was there a deployment in the last 30 minutes?
- Did deployment complete successfully?
- Any configuration changes?

### 4. Review Logs for Errors (3 minutes)

```bash
# Recent errors
railway logs --lines 200 | grep -i "error\|exception\|traceback"

# Check uvicorn health
railway logs --lines 100 | grep -i "uvicorn"

# Memory warnings
railway logs --lines 200 | grep -i "memory\|oom"
```

**Common Issues:**
- `ModuleNotFoundError` → Missing dependency
- `MemoryError` → Resource limits exceeded
- `Connection refused` → Database/external service down
- `Traceback` → Application exception

### 5. Check Railway Resource Limits (1 minute)

```bash
# Railway dashboard
railway open

# Or check via CLI
railway status
```

**Verify:**
- Memory usage < 80%
- CPU usage < 80%
- No deployment failures
- Environment variables set correctly

### 6. Verify Prometheus Metrics (1 minute)

```bash
# Check metrics endpoint
curl https://relay-production-f2a6.up.railway.app/metrics | head -n 20

# Expected: Prometheus text format with HELP/TYPE comments
# If empty → Telemetry initialization failed
```

### 7. Check Upstream Dependencies (1 minute)

**External Services:**
- OpenAI API (if using real mode)
- Anthropic API (if using real mode)
- GitHub (for webhooks/integrations)

```bash
# Quick external service check
curl -I https://api.openai.com
curl -I https://api.anthropic.com
```

### 8. Quick Fix Attempts (30 seconds)

**If service is degraded but not down:**

```bash
# Option 1: Redeploy current version
railway up

# Option 2: Rollback to previous deployment (Railway dashboard)
# Go to Deployments → Click previous successful deployment → Redeploy
```

**If service is DOWN:**

```bash
# Check Railway service status
railway status

# Restart service (if needed)
# Go to Railway dashboard → Service → Settings → Restart
```

---

## 📊 Quick Health Check Commands

**One-liner health check:**
```bash
curl -s https://relay-production-f2a6.up.railway.app/_stcore/health && echo "✅ Health OK" || echo "❌ Health FAIL"
```

**Full endpoint check:**
```bash
for endpoint in "/_stcore/health" "/metrics" "/version" "/ready"; do
  echo "Testing $endpoint..."
  curl -s -o /dev/null -w "  HTTP %{http_code} - %{time_total}s\n" \
    "https://relay-production-f2a6.up.railway.app$endpoint"
done
```

**Quick metrics check:**
```bash
curl -s https://relay-production-f2a6.up.railway.app/metrics | grep -E "^http_requests_total|^http_request_duration_seconds"
```

---

## 🔍 Common Issues and Solutions

### Issue: High Error Rate (> 5%)

**Symptoms:**
- Error rate panel in Grafana shows > 5%
- Logs show 5xx status codes

**Check:**
1. Recent code deployment?
2. External API failures?
3. Resource limits hit?

**Fix:**
- Rollback deployment if recent
- Check external service status
- Increase resource limits in Railway

---

### Issue: High Latency (P95 > 500ms)

**Symptoms:**
- P95 latency panel shows > 500ms
- Slow response times

**Check:**
1. Cold starts (Railway service idle?)
2. Resource contention (CPU/memory)
3. Database/external API slow

**Fix:**
- Enable keep-alive requests
- Scale Railway resources
- Optimize slow endpoints

---

### Issue: Service Unreachable

**Symptoms:**
- Health endpoint returns timeout
- Railway dashboard shows "Crashed"

**Check:**
1. Deployment logs for startup errors
2. Environment variables missing
3. Port binding issues

**Fix:**
```bash
# Check startup logs
railway logs --lines 50

# Verify PORT variable set
railway variables

# Redeploy
railway up
```

---

### Issue: Metrics Endpoint Empty

**Symptoms:**
- `/metrics` returns 200 but empty body
- Grafana panels show "No Data"

**Check:**
1. Telemetry enabled? (`TELEMETRY_ENABLED=true`)
2. Observability extras installed?
3. `init_telemetry()` called?

**Fix:**
```bash
# Check environment variables
railway variables | grep TELEMETRY

# Verify observability dependencies in logs
railway logs --lines 100 | grep -i prometheus

# Redeploy with correct config
railway variables set TELEMETRY_ENABLED=true
railway variables set TELEMETRY_BACKEND=prom
railway up
```

---

## 📞 Escalation

**Escalate if:**
- Service down for > 15 minutes
- Data loss suspected
- Security incident
- Persistent high error rate (> 10%)

**Escalation Checklist:**
1. Gather diagnostics (logs, metrics, screenshots)
2. Document timeline of incident
3. Note all attempted fixes
4. Open incident issue with label `incident`

---

## 📚 Additional Resources

- **Grafana Queries:** `grafana-queries.md`
- **24-Hour Validation:** `VALIDATION-CHECKLIST.md`
- **Deployment Guide:** `docs/DEPLOYMENT.md`
- **Telemetry Config:** `src/telemetry/README.md`

---

## ✅ Post-Incident

After resolving:
1. Close incident issue
2. Document root cause
3. Add monitoring/alerting if missing
4. Update runbook with lessons learned
5. Review deployment process for improvements
