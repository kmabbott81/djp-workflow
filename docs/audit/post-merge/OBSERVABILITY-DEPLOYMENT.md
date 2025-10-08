# Observability Stack Deployment Guide

**Sprint 52 - Platform Alignment**
**Date:** October 7, 2025
**Status:** ✅ Configurations Ready for Deployment

---

## Overview

This guide documents how to deploy the complete observability stack for the Relay Platform, including Prometheus alert rules, Grafana dashboards, and SLO monitoring.

**What's Included:**
- Service Level Objectives (SLOs) with PromQL queries
- Prometheus alert rules (8 alerts across 4 severity levels)
- Grafana golden signals dashboard (8 panels)
- Integration instructions for Railway/production deployment

---

## 1. Alert Rules Deployment

**File:** `observability/dashboards/alerts.json`

### Alert Summary

| Alert Name | Severity | Threshold | Description |
|------------|----------|-----------|-------------|
| `HighLatencyLight` | warning | p99 > 50ms for 5min | Light endpoint latency breach |
| `HighLatencyWebhook` | warning | p95 > 1.2s for 5min | Webhook execution latency breach |
| `HighErrorRate` | critical | >1% errors for 5min | Error rate exceeds SLO |
| `ErrorStreak` | page | >10 errors in 1min | Rapid error burst |
| `HighRateLimitUsage` | info | >80% rate limit for 5min | Rate limiting pressure |
| `ServiceDown` | page | No successful requests for 2min | Service unavailable |
| `DatabasePoolExhaustion` | critical | >90% DB pool for 5min | Database connection pressure |
| `RedisDown` | warning | Redis unavailable for 2min | Rate limiting degraded |

### Deployment Steps

#### Option 1: Prometheus Alerts (YAML)

1. **Convert JSON to Prometheus format** (if using raw Prometheus):
   ```bash
   # observability/dashboards/alerts.yml already contains YAML format
   cp observability/dashboards/alerts.json /path/to/prometheus/alerts/relay.json
   ```

2. **Reload Prometheus configuration**:
   ```bash
   curl -X POST http://localhost:9090/-/reload
   ```

3. **Verify alerts loaded**:
   ```bash
   curl http://localhost:9090/api/v1/rules | jq '.data.groups[].rules[].name'
   ```

#### Option 2: Railway Prometheus Integration

1. **Add Prometheus service** to Railway project
2. **Mount alert rules**:
   - Upload `observability/dashboards/alerts.json` via Railway Dashboard
   - Set environment variable: `PROMETHEUS_RULES_PATH=/app/alerts.json`
3. **Configure targets** in `prometheus.yml`:
   ```yaml
   scrape_configs:
     - job_name: 'relay-backend'
       static_configs:
         - targets: ['relay-production-f2a6.up.railway.app:443']
       metrics_path: '/metrics'
       scheme: 'https'
   ```

---

## 2. Grafana Dashboard Deployment

**File:** `observability/dashboards/golden-signals.json`

### Dashboard Panels

1. **Request Rate** - Total req/sec over time
2. **Error Rate** - 5xx errors as percentage
3. **Latency (Light Endpoints)** - p50, p95, p99 histograms
4. **Latency (Webhook Execution)** - p50, p95, p99 histograms
5. **Rate Limit Hits** - Rate limit 429 responses
6. **SLO Compliance** - Green/yellow/red indicator
7. **Uptime** - Service availability percentage
8. **Total Requests** - Cumulative request counter

### Deployment Steps

#### Option 1: Grafana UI Import

1. **Open Grafana** → **Dashboards** → **Import**
2. **Upload** `observability/dashboards/golden-signals.json`
3. **Configure data source**:
   - Select Prometheus instance
   - Set default time range: Last 24 hours
4. **Set auto-refresh**: 30 seconds

#### Option 2: Grafana API

```bash
GRAFANA_URL="https://grafana.example.com"
GRAFANA_API_KEY="your-api-key"

curl -X POST "$GRAFANA_URL/api/dashboards/db" \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d @observability/dashboards/golden-signals.json
```

#### Option 3: Grafana Provisioning

1. **Add dashboard file** to Grafana provisioning:
   ```bash
   cp observability/dashboards/golden-signals.json \
      /etc/grafana/provisioning/dashboards/relay-golden-signals.json
   ```

2. **Configure provisioning** (`dashboards.yaml`):
   ```yaml
   apiVersion: 1
   providers:
     - name: 'relay-dashboards'
       orgId: 1
       folder: 'Relay Platform'
       type: file
       disableDeletion: false
       updateIntervalSeconds: 10
       options:
         path: /etc/grafana/provisioning/dashboards
   ```

3. **Restart Grafana** or wait for auto-reload

---

## 3. SLO Monitoring

**File:** `docs/observability/SLOs.md`

### Defined SLOs

| Metric | Target | Measurement Period |
|--------|--------|-------------------|
| Light endpoint latency | p99 ≤ 50ms | 7 days |
| Webhook execution latency | p95 ≤ 1.2s | 7 days |
| Error rate | ≤ 1% | 7 days |
| Availability | ≥ 99.9% | 30 days |

### PromQL Queries

**Light Endpoint p99 Latency:**
```promql
histogram_quantile(0.99,
  rate(http_request_duration_seconds_bucket{
    path=~"/actions|/audit"
  }[5m])
)
```

**Webhook p95 Latency:**
```promql
histogram_quantile(0.95,
  rate(http_request_duration_seconds_bucket{
    path="/actions/execute"
  }[5m])
)
```

**Error Rate:**
```promql
sum(rate(http_requests_total{status=~"5.."}[5m]))
/
sum(rate(http_requests_total[5m]))
```

**Availability (30-day):**
```promql
avg_over_time(up{job="relay-backend"}[30d])
```

### Error Budget Tracking

**Error Budget:** `(1 - SLO) * Total Requests`

For 99.9% availability SLO:
- **Budget:** 0.1% of requests can fail
- **Example:** 1M requests/month → 1,000 allowed errors
- **Alert Threshold:** 50% budget consumed → warning

**Query:**
```promql
sum(http_requests_total{status=~"5.."})
/
sum(http_requests_total)
> 0.0005  # 50% of 0.1% error budget
```

---

## 4. Production Deployment Checklist

### Pre-Deployment

- [ ] Prometheus instance running with `/metrics` endpoint configured
- [ ] Grafana instance running with Prometheus data source configured
- [ ] Alert notification channels configured (Slack, PagerDuty, email)
- [ ] SLO baselines established from Phase B monitoring data

### Deployment

- [ ] Import alert rules to Prometheus
- [ ] Verify alert rules loaded: `curl http://localhost:9090/api/v1/rules`
- [ ] Import Grafana dashboard via UI or API
- [ ] Configure dashboard refresh interval (30s recommended)
- [ ] Test alert firing with synthetic traffic:
  ```bash
  # Trigger high latency alert (add artificial delay to endpoint)
  # Trigger error rate alert (force 500 errors)
  ```

### Post-Deployment

- [ ] Validate all panels displaying data in Grafana dashboard
- [ ] Confirm alert rules appear in Prometheus UI
- [ ] Test alert notifications fire correctly
- [ ] Set up oncall rotation for `page` severity alerts
- [ ] Document runbook URLs in alert annotations

---

## 5. Validation Commands

### Check Prometheus Metrics

```bash
# Verify metrics endpoint accessible
curl https://relay-production-f2a6.up.railway.app/metrics

# Check specific metrics exist
curl https://relay-production-f2a6.up.railway.app/metrics | grep http_request_duration_seconds
curl https://relay-production-f2a6.up.railway.app/metrics | grep http_requests_total
curl https://relay-production-f2a6.up.railway.app/metrics | grep actions_exec_total
```

### Test PromQL Queries

```bash
# Test latency query
curl 'http://localhost:9090/api/v1/query?query=histogram_quantile(0.99,rate(http_request_duration_seconds_bucket[5m]))'

# Test error rate query
curl 'http://localhost:9090/api/v1/query?query=sum(rate(http_requests_total{status=~"5.."}[5m]))/sum(rate(http_requests_total[5m]))'
```

### Verify Grafana Dashboard

1. Open dashboard in Grafana
2. Verify all 8 panels display data
3. Check time range selector works
4. Test variable filters (if any)
5. Confirm refresh interval set to 30s

---

## 6. Troubleshooting

### Issue: No Data in Grafana Panels

**Cause:** Prometheus not scraping metrics endpoint

**Fix:**
1. Check Prometheus targets: `http://localhost:9090/targets`
2. Verify endpoint accessible: `curl https://relay-production-f2a6.up.railway.app/metrics`
3. Check Prometheus logs for scrape errors

### Issue: Alerts Not Firing

**Cause:** Alert thresholds not met or notification channel misconfigured

**Fix:**
1. Check alert state in Prometheus UI
2. Test alert manually: `curl -X POST http://localhost:9090/api/v1/admin/tsdb/snapshot`
3. Verify notification channel configuration in Alertmanager

### Issue: High Latency False Positives

**Cause:** Baseline data doesn't account for cold starts or deployment spikes

**Fix:**
1. Adjust `for` duration in alert rule (increase from 5m to 10m)
2. Add `rate()` function to smooth spikes
3. Use `quantile_over_time()` for percentile-based alerting

---

## 7. Next Steps

1. **Deploy to Production:**
   - Schedule deployment window
   - Import configurations
   - Validate monitoring live

2. **Establish Baselines:**
   - Run for 7 days to collect baseline data
   - Adjust alert thresholds based on actual traffic patterns
   - Document P50/P95/P99 latencies for each endpoint

3. **Oncall Setup:**
   - Configure PagerDuty integration for `page` severity
   - Set up Slack integration for `critical` and `warning`
   - Create oncall rotation schedule

4. **Runbook Documentation:**
   - Document response procedures for each alert
   - Add links to runbooks in alert annotations
   - Test runbook procedures with synthetic incidents

---

**Status:** ✅ Ready for Production Deployment

**Blockers:** None - All configurations validated and ready to import

**Owner:** Platform Team

**Next Review:** After 7-day baseline period
