# Quick Start Guide

Get up and running with DJP Workflow staging deployment and observability in < 5 minutes.

## Prerequisites

- Docker (for Prometheus + Grafana)
- Railway CLI (`npm install -g @railway/cli`)
- Git

## 1. Clone and Setup

```bash
git clone https://github.com/kmabbott81/djp-workflow.git
cd djp-workflow
```

## 2. Check Staging Health

**PowerShell:**
```powershell
$env:STAGING_URL = "https://relay-production-f2a6.up.railway.app"
.\scripts\check-staging.ps1
```

**Bash:**
```bash
export STAGING_URL="https://relay-production-f2a6.up.railway.app"
./scripts/check-staging.sh
```

Expected output:
```
✅ Health: HTTP 200
✅ Metrics: Prometheus format detected
✅ All critical endpoints operational
```

## 3. Start Local Monitoring

```bash
cd observability

# Start Prometheus + Grafana
docker run -d --name prom -p 9090:9090 \
  -v ${PWD}/templates/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v ${PWD}/templates/alerts.yml:/etc/prometheus/alerts.yml \
  prom/prometheus --config.file=/etc/prometheus/prometheus.yml

docker run -d --name grafana -p 3000:3000 grafana/grafana
```

**Configure Grafana:**
1. Open http://localhost:3000 (admin/admin)
2. Add Prometheus data source: `http://host.docker.internal:9090`
3. Import dashboard: `templates/grafana-golden-signals.json`

## 4. Generate Traffic

**PowerShell:**
```powershell
.\scripts\generate-traffic.ps1 -Count 50 -Interval 2
```

**Bash:**
```bash
./scripts/traffic.sh 50 2
```

Within 30-60 seconds, Grafana panels will populate with metrics.

## 5. Verify Observability

**Check Prometheus targets:**
```
open http://localhost:9090/targets
```

Expected: `djp-workflow-staging` target is **UP**

**Check metrics:**
```bash
curl https://relay-production-f2a6.up.railway.app/metrics | head -n 20
```

Expected:
```
# HELP http_requests_total Total HTTP requests
# TYPE http_requests_total counter
http_requests_total{endpoint="/_stcore/health",method="GET",status_code="200"} 42.0
```

---

## Key Endpoints

| Endpoint | Purpose |
|----------|---------|
| `/_stcore/health` | Basic health check |
| `/ready` | Readiness with dependency checks |
| `/version` | Build metadata (git SHA, branch) |
| `/metrics` | Prometheus metrics |
| `/api/templates` | List available templates |

---

## Next Steps

### Enable Hybrid Backend (Prometheus + OTel)

Currently staging uses Prometheus-only. To add OpenTelemetry tracing:

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

### Run 24-Hour Validation

Follow `VALIDATION-CHECKLIST.md` for full staging validation procedure:
- Monitor every 4 hours
- Check P95/P99 latency thresholds
- Verify error rate < 1%
- Export baseline metrics

### Deploy to Production

1. Validate staging metrics meet SLOs
2. Create production Railway service
3. Set production environment variables
4. Deploy: `railway up --service production`

---

## Troubleshooting

### Service not responding

```bash
# Check Railway status
railway status

# View logs
railway logs --lines 100

# Restart service (Railway dashboard)
```

### No metrics in Grafana

1. Verify Prometheus data source URL
2. Check Prometheus targets: http://localhost:9090/targets
3. Wait 30-60s for first scrape
4. Verify metrics endpoint: `curl https://relay-production-f2a6.up.railway.app/metrics`

### High latency

```bash
# Check for cold starts
./scripts/traffic.sh 10 1

# Review Railway resource limits
railway status

# Check logs for errors
railway logs --lines 200 | grep -i error
```

---

## Additional Resources

- **On-Call Guide:** `docs/ops/ONCALL-10-MIN.md`
- **Validation Checklist:** `VALIDATION-CHECKLIST.md`
- **Observability Setup:** `observability/README.md`
- **Grafana Queries:** `grafana-queries.md`

---

## Environment Variables Reference

### Telemetry

| Variable | Default | Description |
|----------|---------|-------------|
| `TELEMETRY_ENABLED` | `false` | Enable telemetry |
| `TELEMETRY_BACKEND` | `noop` | Backend: `noop`, `prom`, `otel`, `hybrid` |
| `OTEL_SERVICE_NAME` | `djp-workflow` | Service name for traces |
| `OTEL_EXPORTER` | `console` | Exporter: `console`, `otlp` |
| `OTEL_ENDPOINT` | `http://localhost:4318` | OTLP endpoint URL |
| `OTEL_TRACE_SAMPLE` | `0.1` | Sampling rate (0.0-1.0) |

### Railway

| Variable | Example | Description |
|----------|---------|-------------|
| `PORT` | `8000` | HTTP port (auto-assigned by Railway) |
| `RAILWAY_ENVIRONMENT` | `staging` | Environment name |

---

## Quick Commands

```bash
# Health check
curl https://relay-production-f2a6.up.railway.app/_stcore/health

# Version info
curl https://relay-production-f2a6.up.railway.app/version

# Generate traffic
./scripts/traffic.sh 30 2

# Check staging
./scripts/check-staging.sh

# View logs
railway logs --lines 50

# Deploy
railway up

# Open Railway dashboard
railway open
```
