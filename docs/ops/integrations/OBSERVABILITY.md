# Observability Integration

## What this integrates

Prometheus metrics collection with Grafana dashboards and Alertmanager for SLO monitoring. Behind `TELEMETRY_ENABLED` flag - all operations are no-ops if disabled.

## Where it's configured

- `src/telemetry/prom.py` - Prometheus metrics instrumentation
- `prometheus.yml` - Prometheus server configuration (local dev)
- `observability/templates/prometheus.yml` - Production config template
- `observability/templates/prometheus-alerts.yml` - Alert rules
- `pyproject.toml` - `[observability]` extra with prometheus-client

## Env vars / secrets

| Name | Scope | Where set | Notes |
|------|-------|-----------|-------|
| `TELEMETRY_ENABLED` | Runtime | Railway Variables or local | Set to `true` to enable metrics collection |
| `PROM_EXPORT_PORT` | Runtime | Optional | Metrics export port (default: 9090) |

## How to verify (60 seconds)

```bash
# 1. Check TELEMETRY_ENABLED status
railway variables | grep TELEMETRY_ENABLED
# Should show: TELEMETRY_ENABLED=true

# 2. Query metrics endpoint
curl http://localhost:9090/metrics
# Should return Prometheus text format metrics

# 3. Check specific metrics exist
curl http://localhost:9090/metrics | grep "http_requests_total"
# Should show: http_requests_total{method="GET",endpoint="/health",status_code="200"} N

# 4. Query Prometheus for action metrics
curl 'http://localhost:9090/api/v1/query?query=action_latency_seconds' | jq .
# Should return time series data

# 5. Verify recording rules/alerts loaded (if Prometheus running)
curl http://localhost:9090/api/v1/rules | jq '.data.groups[].name'
# Should list: gmail_slo, outlook_slo, rollout_health, etc.
```

## Sample PromQL queries

Copy-paste these into Prometheus or Grafana:

```promql
# Gmail send p95 latency (last 5 minutes)
histogram_quantile(0.95,
  rate(action_latency_seconds_bucket{provider="google",action="gmail.send"}[5m])
)

# Outlook send p95 latency (last 5 minutes)
histogram_quantile(0.95,
  rate(action_latency_seconds_bucket{provider="microsoft",action="outlook.send"}[5m])
)

# Rollout controller runs (last 1 hour)
increase(rollout_controller_runs_total[1h])

# Error rate by provider (last 5 minutes)
rate(action_error_total[5m])

# HTTP request rate by endpoint
rate(http_requests_total[5m])
```

## Common failure → quick fix

### Metrics missing (returns empty)
**Cause:** TELEMETRY_ENABLED not set to `true`
**Fix:**
```bash
# Set in Railway
railway variables set TELEMETRY_ENABLED=true
# Or locally
export TELEMETRY_ENABLED=true
python -m uvicorn src.webapi:app --port 8000
```

### "prometheus-client not installed" warning
**Cause:** Observability extras not installed
**Fix:**
```bash
# Install with observability extras
pip install -e ".[observability]"
# Or add to Dockerfile (already present on line 14)
```

### Metrics endpoint returns 404
**Cause:** `/metrics` route not registered (check src/webapi.py)
**Fix:**
```python
# Add to src/webapi.py (if missing)
from src.telemetry.prom import generate_metrics_text

@app.get("/metrics")
def metrics():
    return generate_metrics_text()
```

### Alert not firing despite breach
**Cause:** Recording rules not loaded or alert expression wrong
**Fix:**
1. Check Prometheus logs: `docker logs prometheus`
2. Verify `prometheus-alerts.yml` syntax: `promtool check rules prometheus-alerts.yml`
3. Reload Prometheus config: `curl -X POST http://localhost:9090/-/reload`

## Metrics sentinel alert

This alert fires if no metrics received for 5 minutes (indicates TELEMETRY_ENABLED=false or crash):

```yaml
- alert: MetricsMissing
  expr: absent(up{job="relay"}) == 1
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Metrics collection stopped"
    description: "No metrics from Relay service for 5+ minutes. Check TELEMETRY_ENABLED flag."
```

## References

- src/telemetry/prom.py:1-318 - Full metrics instrumentation implementation
- src/telemetry/prom.py:46-48 - `_is_enabled()` checks TELEMETRY_ENABLED env var
- src/telemetry/prom.py:78-145 - Metric definitions (histograms, counters, gauges)
- observability/templates/prometheus.yml - Server config with scrape targets
- observability/templates/prometheus-alerts.yml - SLO alert rules
