# Railway Configuration

Manual configuration steps for Railway service settings.

## Start Command Pinning

**Why:** Prevents Dockerfile CMD changes from accidentally switching the entrypoint (e.g., back to Streamlit).

**How:**
1. Open Railway dashboard: https://railway.app/project/relay
2. Navigate to: **Service → Settings → Start Command**
3. Set to:
   ```
   sh -c scripts/start-server.sh
   ```
4. Click **Save**

This ensures the service always boots with uvicorn via the start script, regardless of Dockerfile changes.

## Environment Variables

**Current Staging Configuration:**

### Telemetry (Prometheus-only)
```
TELEMETRY_ENABLED=true
TELEMETRY_BACKEND=prom
OTEL_EXPORTER=console
OTEL_SERVICE_NAME=djp-workflow-staging
OTEL_TRACE_SAMPLE=0.05
```

### Hybrid Backend (Prometheus + OTel)
To enable OpenTelemetry tracing alongside Prometheus:

```bash
railway variables set TELEMETRY_BACKEND=hybrid
railway up
```

Traces will log to console. To send to Tempo/Jaeger:

```bash
railway variables set OTEL_EXPORTER=otlp
railway variables set OTEL_ENDPOINT=http://<tempo-collector>:4318
railway up
```

## Build Configuration

**Build Command:** (Auto-detected from Dockerfile)
```dockerfile
RUN pip install --no-cache-dir --user -e ".[observability]"
```

**Dockerfile:** Default (automatically detected)

**Root Directory:** `/` (repository root)

## Service Settings

**Region:** us-west1 (or your preferred region)

**Health Check:**
- Path: `/_stcore/health`
- Expected: HTTP 200 with `{"ok": true}`

**Deployment:**
- Auto-deploy: Enabled for `sprint/48-staging-and-dashboards` branch
- Or manual: `railway up`

## Resource Limits

**Memory:** Default (512 MB - 8 GB based on usage)

**CPU:** Shared vCPU (default)

**Scaling:** Single instance (vertical scaling)

---

## Monitoring Setup

### Enable Railway Metrics
Railway provides basic metrics in the dashboard:
- CPU usage
- Memory usage
- Network I/O

### External Monitoring (Prometheus)
1. Ensure `/metrics` endpoint is accessible
2. Configure Prometheus to scrape: `relay-production-f2a6.up.railway.app/metrics`
3. Use `observability/templates/prometheus.yml`

### Alerting
- **GitHub Actions:** Uptime monitoring (5-min interval)
- **Prometheus:** Alert rules in `alerts.yml`
- **Grafana:** Dashboard alerts for P95/P99 latency

---

## Deployment Checklist

Before deploying changes:

- [ ] Test locally: `uvicorn src.webapi:app --port 8000`
- [ ] Run linters: `pre-commit run --all-files`
- [ ] Verify health endpoint: `curl http://localhost:8000/_stcore/health`
- [ ] Check metrics: `curl http://localhost:8000/metrics | head -n 20`
- [ ] Deploy: `railway up`
- [ ] Verify deployment: `./scripts/check-staging.sh`
- [ ] Monitor logs: `railway logs --lines 100`

---

## Rollback Procedure

If deployment fails:

1. **Via Dashboard:**
   - Go to Deployments tab
   - Find last successful deployment
   - Click **Redeploy**

2. **Via CLI:**
   ```bash
   # View recent deployments
   railway logs --lines 200

   # Rollback to previous commit
   git revert HEAD
   git push
   railway up
   ```

3. **Emergency:**
   - Railway auto-scales down failed deployments
   - Previous deployment remains active until new one is healthy
   - No manual intervention needed for failed health checks

---

## Troubleshooting

### Service won't start
```bash
# Check logs
railway logs --lines 200

# Common issues:
# - Missing dependencies (check pip install output)
# - Port binding error (ensure PORT env var is used)
# - Import errors (verify all modules installed)
```

### Environment variables not set
```bash
# List all variables
railway variables

# Set variable
railway variables set KEY=VALUE

# Redeploy
railway up
```

### Start command not persisting
- Ensure start command is set in Railway dashboard (not just Dockerfile)
- Verify `scripts/start-server.sh` is executable in git
- Check file is included in deployment (not in .dockerignore)

---

## Additional Resources

- **Railway Docs:** https://docs.railway.app/
- **Railway Status:** https://status.railway.app/
- **Project Dashboard:** https://railway.app/project/relay
- **Deployment Guide:** `docs/DEPLOYMENT.md` (if exists)
