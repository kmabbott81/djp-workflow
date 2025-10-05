# Observability Setup

Local Prometheus + Grafana monitoring for DJP Workflow staging deployment.

## Quick Start

### 1. Start Prometheus + Grafana

```bash
cd observability

# Start Prometheus
docker run -d --name prom -p 9090:9090 \
  -v ${PWD}/templates/prometheus.yml:/etc/prometheus/prometheus.yml \
  -v ${PWD}/templates/alerts.yml:/etc/prometheus/alerts.yml \
  prom/prometheus --config.file=/etc/prometheus/prometheus.yml

# Start Grafana
docker run -d --name grafana -p 3000:3000 grafana/grafana
```

**Windows PowerShell:**
```powershell
cd observability

# Start Prometheus
docker run -d --name prom -p 9090:9090 `
  -v ${PWD}\templates\prometheus.yml:/etc/prometheus/prometheus.yml `
  -v ${PWD}\templates\alerts.yml:/etc/prometheus/alerts.yml `
  prom/prometheus --config.file=/etc/prometheus/prometheus.yml

# Start Grafana
docker run -d --name grafana -p 3000:3000 grafana/grafana
```

### 2. Configure Grafana

1. Open http://localhost:3000
2. Login: `admin` / `admin` (change password when prompted)
3. Add Data Source:
   - Type: Prometheus
   - URL: `http://host.docker.internal:9090` (Mac/Windows) or `http://172.17.0.1:9090` (Linux)
   - Save & Test

### 3. Import Dashboard

1. In Grafana: **Dashboards → Import**
2. Upload `templates/grafana-golden-signals.json`
3. Select Prometheus data source
4. Click **Import**

### 4. Generate Traffic

```bash
# From repo root
./scripts/generate-traffic.ps1 -Count 50 -Interval 2
```

Within 30-60 seconds, you should see metrics populating in Grafana.

---

## Files

### `templates/prometheus.yml`
Prometheus scraping configuration targeting Railway staging endpoint:
- Job: `djp-workflow-staging`
- Target: `relay-production-f2a6.up.railway.app`
- Scrape interval: 15s

### `templates/alerts.yml`
Prometheus alert rules:
- **HighP99Latency**: P99 > 1s for 5m
- **HighErrorRate**: Error rate > 5% for 5m

### `templates/grafana-golden-signals.json`
Grafana dashboard with Golden Signals panels:
- Request Rate (Traffic)
- Error Rate (Errors)
- P50/P95/P99 Latency (Latency)
- In-Flight Requests (Saturation)
- Memory/CPU Usage

---

## Endpoints

Staging service exposes these observability endpoints:

- `/_stcore/health` - Basic health check (`{"ok": true}`)
- `/ready` - Readiness check with dependency validation
- `/version` - Build metadata (git SHA, branch, environment)
- `/metrics` - Prometheus metrics (text exposition format)

---

## Metrics Available

### HTTP Metrics
- `http_requests_total` - Total HTTP requests (labels: `method`, `endpoint`, `status_code`)
- `http_request_duration_seconds` - Request latency histogram (labels: `method`, `endpoint`)
- `http_requests_in_flight` - Currently active requests

### Python Metrics
- `process_resident_memory_bytes` - RSS memory usage
- `process_cpu_seconds_total` - CPU time consumed
- `python_gc_*` - Garbage collector stats

---

## Validation

Follow the 24-hour validation procedure in `../VALIDATION-CHECKLIST.md`:

1. Start Prometheus + Grafana (above)
2. Generate initial traffic
3. Monitor every 4 hours
4. Export baseline metrics after 24 hours

---

## Troubleshooting

### Prometheus not scraping

```bash
# Check target status
open http://localhost:9090/targets

# Verify staging metrics accessible
curl https://relay-production-f2a6.up.railway.app/metrics

# Check Prometheus logs
docker logs prom
```

### No data in Grafana

1. Verify Prometheus data source connected
2. Check query syntax in panel editor
3. Wait 30-60s for first scrape
4. Ensure time range covers recent data

### High latency

```bash
# Check Railway logs
railway logs --lines 100

# Verify no cold starts
curl https://relay-production-f2a6.up.railway.app/_stcore/health

# Check resource limits
railway status
```

---

## Cleanup

```bash
# Stop and remove containers
docker stop prom grafana
docker rm prom grafana

# Remove volumes (optional)
docker volume prune
```

---

## Next Steps

1. **Enable Hybrid Backend** - Add OpenTelemetry tracing:
   ```bash
   railway variables set TELEMETRY_BACKEND=hybrid
   railway variables set OTEL_EXPORTER=otlp
   railway variables set OTEL_ENDPOINT=http://<tempo>:4318
   railway up
   ```

2. **Deploy Tempo** - Distributed tracing backend for OTel spans

3. **Alert Notifications** - Configure Grafana alerting with Slack/email

4. **Production Deployment** - Replicate setup for production environment

---

## References

- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Docs**: https://grafana.com/docs/
- **PromQL Cheat Sheet**: https://promlabs.com/promql-cheat-sheet/
- **Golden Signals**: https://sre.google/sre-book/monitoring-distributed-systems/
