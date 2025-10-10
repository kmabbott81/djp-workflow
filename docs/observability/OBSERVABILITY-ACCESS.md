# Observability Access Guide

Quick reference for accessing logs, metrics, and alerts.

## 🔍 Monitoring Dashboards

### Grafana Dashboard
- **URL:** http://localhost:3000/d/relay-golden-signals/relay-actions-api-golden-signals
- **Login:** admin / (your Grafana password)
- **Panels:** Request rate, latency, error rate, SLOs, availability

### Prometheus UI
- **URL:** http://localhost:9090
- **Alerts:** http://localhost:9090/alerts
- **Rules:** http://localhost:9090/rules
- **Query:** http://localhost:9090/graph

## 📊 Alert Rules

All configured alerts are visible at: http://localhost:9090/alerts

**Active Alerts (8 rules):**
1. LightEndpointLatencyHigh - p99 > 50ms for 5m
2. WebhookExecuteLatencyHigh - p95 > 1.2s for 5m
3. ActionsErrorRateHigh - 5xx rate > 1% for 5m (CRITICAL)
4. HighErrorStreak - 5xx rate > 10% for 3m (PAGE)
5. RateLimitBreaches - 429s detected for 10m
6. ServiceDown - Health check failing for 1m (PAGE)
7. DatabaseConnectionPoolExhausted - Pool > 90% for 5m
8. RedisDown - Redis unavailable for 5m

**Severity Levels:**
- `page` - Immediate attention required
- `critical` - Urgent issue, check within minutes
- `warning` - Investigate soon
- `info` - Informational only

## 📝 Application Logs

### Railway Production Logs
**Access via Railway Dashboard:**
1. Go to https://railway.app/dashboard
2. Select your project: "Relay"
3. Click on "relay-backend" service
4. Click "Deployments" tab
5. Click on active deployment
6. View logs in real-time

**Access via CLI:**
```bash
# Install Railway CLI if not already installed
npm i -g @railway/cli

# Login
railway login

# View logs
railway logs
```

### Local Docker Logs

**Prometheus Container:**
```bash
# View recent logs
docker logs prom --tail 100

# Follow logs in real-time
docker logs prom -f

# View logs since specific time
docker logs prom --since 1h
```

**Grafana Container:**
```bash
# View recent logs
docker logs grafana --tail 100

# Follow logs in real-time
docker logs grafana -f
```

## 🔧 Prometheus Metrics

### View Raw Metrics
**Production metrics endpoint:**
- URL: https://relay-production-f2a6.up.railway.app/metrics
- Format: Prometheus text format
- Scrape interval: 15s

**Query metrics directly:**
```bash
# Total requests
curl -s http://localhost:9090/api/v1/query?query=http_requests_total

# Current error rate
curl -s http://localhost:9090/api/v1/query?query='rate(http_requests_total{status_code=~"5.."}[5m])'

# Service uptime
curl -s http://localhost:9090/api/v1/query?query='up{job="djp-workflow-staging"}'
```

## 🗂️ Log File Locations

### Prometheus Data & Logs
**Container path:** `/prometheus`
**Config:** `/etc/prometheus/prometheus.yml`
**Alert rules:** `/etc/prometheus/alerts.yml`

**Access files:**
```bash
# View Prometheus config
docker exec prom cat /etc/prometheus/prometheus.yml

# View alert rules
docker exec prom cat /etc/prometheus/alerts.yml

# Check Prometheus data directory
docker exec prom ls -lh /prometheus
```

### Grafana Data & Logs
**Container path:** `/var/lib/grafana`
**Config:** `/etc/grafana/grafana.ini`

**Access files:**
```bash
# View Grafana config
docker exec grafana cat /etc/grafana/grafana.ini

# Check Grafana logs
docker exec grafana cat /var/log/grafana/grafana.log
```

## 📈 Common Queries

### Check System Health
```bash
# Is Prometheus running?
curl -s http://localhost:9090/-/healthy

# Is Grafana running?
curl -s http://localhost:3000/api/health

# Is production API responding?
curl -s https://relay-production-f2a6.up.railway.app/
```

### View Active Alerts
```bash
# All active alerts
curl -s http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.state=="firing")'

# Count of firing alerts
curl -s http://localhost:9090/api/v1/alerts | jq '[.data.alerts[] | select(.state=="firing")] | length'
```

### Recent Error Logs (Railway)
```bash
# Via Railway CLI
railway logs --filter "error" --tail 100
railway logs --filter "exception" --tail 100
railway logs --filter "5xx" --tail 50
```

## 🚨 Troubleshooting

### Alerts Not Showing Up
1. Check Prometheus loaded rules: http://localhost:9090/rules
2. Verify alert file exists: `docker exec prom cat /etc/prometheus/alerts.yml`
3. Check Prometheus logs: `docker logs prom --tail 50`

### Dashboard Shows "No Data"
1. Verify Prometheus is scraping: http://localhost:9090/targets
2. Check data source in Grafana: Connections → Data sources → Prometheus
3. Test query in Prometheus UI: http://localhost:9090/graph

### Production Logs Not Accessible
1. Ensure you're logged into Railway: `railway login`
2. Link to correct project: `railway link`
3. Check Railway dashboard for deployment status

## 📚 Additional Resources

- **SLO Documentation:** `docs/observability/SLOs.md`
- **Alert Runbooks:** See `runbook_url` in each alert annotation
- **Prometheus Documentation:** https://prometheus.io/docs
- **Grafana Documentation:** https://grafana.com/docs
- **Railway Logs:** https://docs.railway.app/guides/logs

## 🔐 Credentials Reference

**Grafana API Key:** Stored in `configs/.env` as `GRAFANA_API_KEY`
**Railway Access:** Authenticated via `railway login` CLI command
**Prometheus:** No authentication required (local only)

---

**Last Updated:** 2025-10-08
**Maintained By:** Sprint 52 Platform Alignment
