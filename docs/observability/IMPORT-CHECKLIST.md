# Observability Stack Import Checklist

**Sprint 52 – Agent Orchestration (Phase 1)**
**Date:** October 7, 2025
**Purpose:** Step-by-step guide for importing Prometheus alerts and Grafana dashboard to production

---

## Prerequisites

Before importing, verify the following:

- [ ] **Prometheus deployed** and accessible (Railway service or external)
- [ ] **Grafana deployed** and accessible (Railway service or external)
- [ ] **Prometheus datasource configured** in Grafana
- [ ] **Backend exporting metrics** at `/metrics` endpoint (validated in Sprint 51 Phase 3)
- [ ] **Admin access** to both Prometheus and Grafana UIs

**Deployment Context:**
- If using Railway: Prometheus + Grafana deployed as separate services (see OBSERVABILITY-DEPLOYMENT.md)
- If using managed service: Ensure Prometheus scrape config points to backend `/metrics`

---

## Part 1: Import Prometheus Alerts

### Step 1: Prepare Alert Rules File

**Source File:** `observability/dashboards/alerts.json`

Convert JSON alert definitions to Prometheus YAML format:

```bash
# Create a Prometheus-compatible rules file
cat > prometheus-alerts.yml <<'EOF'
groups:
  - name: relay_slo_alerts
    interval: 30s
    rules:
      # Light Endpoint Latency
      - alert: LightEndpointLatencyHigh
        expr: histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{path=~"/actions|/audit"}[5m])) > 0.05
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Light endpoint p99 latency exceeds 50ms"
          description: "p99 latency is {{ $value | humanizeDuration }} (SLO: ≤50ms)"

      # Webhook Execute Latency
      - alert: WebhookExecuteLatencyHigh
        expr: histogram_quantile(0.95, rate(http_request_duration_seconds_bucket{path="/actions/execute"}[5m])) > 1.2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Webhook execute p95 latency exceeds 1.2s"
          description: "p95 latency is {{ $value | humanizeDuration }} (SLO: ≤1.2s)"

      # Actions Error Rate
      - alert: ActionsErrorRateHigh
        expr: (sum(rate(http_requests_total{path=~"/actions.*", status=~"5.."}[5m])) / sum(rate(http_requests_total{path=~"/actions.*"}[5m]))) > 0.01
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Actions error rate exceeds 1%"
          description: "Error rate is {{ $value | humanizePercentage }} (SLO: ≤1%)"

      # High Error Streak
      - alert: HighErrorStreak
        expr: (sum(rate(http_requests_total{status=~"5.."}[1m])) / sum(rate(http_requests_total[1m]))) > 0.05
        for: 2m
        labels:
          severity: page
        annotations:
          summary: "Sustained error spike detected"
          description: "Error rate {{ $value | humanizePercentage }} over last 2min (threshold: 5%)"

      # Service Down
      - alert: ServiceDown
        expr: up{job="relay-backend"} == 0
        for: 1m
        labels:
          severity: page
        annotations:
          summary: "Relay backend service is down"
          description: "Service has been unavailable for 1 minute"

      # Rate Limit Breaches
      - alert: RateLimitBreaches
        expr: sum(increase(http_requests_total{status="429"}[5m])) > 100
        for: 5m
        labels:
          severity: info
        annotations:
          summary: "High rate of 429 responses"
          description: "{{ $value }} rate limit breaches in last 5 minutes"

      # Database Connection Pool
      - alert: DatabaseConnectionPoolExhausted
        expr: db_pool_connections_in_use / db_pool_connections_max > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Database connection pool near capacity"
          description: "{{ $value | humanizePercentage }} of pool connections in use"

      # Redis Down
      - alert: RedisDown
        expr: redis_up == 0
        for: 2m
        labels:
          severity: warning
        annotations:
          summary: "Redis (rate limiter) is unavailable"
          description: "Falling back to in-process rate limiter"
EOF
```

### Step 2: Deploy to Prometheus

**Option A: Railway Deployment (Recommended)**

1. **Copy rules file to Prometheus service:**
   ```bash
   # In Railway CLI or dashboard
   railway run --service prometheus cp prometheus-alerts.yml /etc/prometheus/rules/relay_slo_alerts.yml
   ```

2. **Update Prometheus config** to include rules:
   ```yaml
   # prometheus.yml (add to rule_files section)
   rule_files:
     - /etc/prometheus/rules/*.yml
   ```

3. **Reload Prometheus config:**
   ```bash
   # Send SIGHUP to reload
   railway run --service prometheus pkill -HUP prometheus
   ```

4. **Verify alerts loaded:**
   - Navigate to Prometheus UI: `https://[prometheus-url]/alerts`
   - Confirm all 8 alerts are visible (may be in "Inactive" state if not firing)

**Option B: Managed Prometheus (Grafana Cloud, etc.)**

1. **Navigate to Alerting → Alert rules**
2. **Import YAML file** via UI
3. **Verify alert rules** appear in dashboard

### Step 3: Validate Alert Configuration

- [ ] **Open Prometheus UI:** `https://[prometheus-url]/alerts`
- [ ] **Verify all 8 alerts listed:**
  - LightEndpointLatencyHigh
  - WebhookExecuteLatencyHigh
  - ActionsErrorRateHigh
  - HighErrorStreak
  - ServiceDown
  - RateLimitBreaches
  - DatabaseConnectionPoolExhausted
  - RedisDown
- [ ] **Run test query** in Prometheus to verify metrics exist:
  ```promql
  http_request_duration_seconds_bucket{path=~"/actions|/audit"}
  ```
- [ ] **Trigger test alert** (optional):
  ```bash
  # Generate high latency traffic to trigger LightEndpointLatencyHigh
  for i in {1..100}; do curl -X GET https://[backend-url]/actions?sleep=100; done
  ```

---

## Part 2: Import Grafana Dashboard

### Step 1: Prepare Dashboard JSON

**Source File:** `observability/dashboards/golden-signals.json`

The file is already in Grafana-compatible format. No conversion needed.

### Step 2: Import to Grafana

**Option A: Via Grafana UI (Recommended)**

1. **Open Grafana:** `https://[grafana-url]`
2. **Navigate to:** Dashboards → Import
3. **Upload JSON:**
   - Click "Upload JSON file"
   - Select `observability/dashboards/golden-signals.json`
   - Or paste JSON content directly
4. **Configure Import:**
   - **Name:** "Relay Golden Signals"
   - **Folder:** "Production Monitoring"
   - **Prometheus Datasource:** Select your Prometheus instance
   - **UID:** Leave auto-generated or use `relay-golden-signals`
5. **Click "Import"**

**Option B: Via Grafana API**

```bash
# Set Grafana API key (create in Grafana UI → Configuration → API Keys)
export GRAFANA_API_KEY="your-api-key-here"
export GRAFANA_URL="https://your-grafana-instance.com"

# Import dashboard
curl -X POST \
  -H "Authorization: Bearer $GRAFANA_API_KEY" \
  -H "Content-Type: application/json" \
  -d @observability/dashboards/golden-signals.json \
  "$GRAFANA_URL/api/dashboards/db"
```

### Step 3: Validate Dashboard Configuration

- [ ] **Open Dashboard:** Dashboards → "Relay Golden Signals"
- [ ] **Verify 8 panels render correctly:**
  1. Request Rate (RPM) - Shows traffic volume
  2. Error Rate (%) - Shows error percentage with 1% threshold
  3. Latency - Light Endpoints - Shows p50/p95/p99 with 50ms threshold
  4. Latency - Webhook Execute - Shows p50/p95/p99 with 1.2s threshold
  5. Rate Limit Hits (429s) - Shows 24h total
  6. SLO Error Budget Remaining - Gauge showing % remaining
  7. Service Availability (Uptime %) - Shows 30d average
  8. Total Requests (24h) - Shows daily volume
- [ ] **Verify alert annotations visible:**
  - Red vertical lines should appear when alerts fire
  - Hover over lines to see alert name
- [ ] **Verify time range controls work:**
  - Test "Last 15 minutes", "Last 1 hour", "Last 24 hours"
- [ ] **Verify refresh works:**
  - Set to auto-refresh (e.g., "10s")
  - Confirm panels update with new data

### Step 4: Configure Alerting (Optional)

If using Grafana Alerting (instead of Prometheus Alertmanager):

1. **Navigate to:** Alerting → Alert rules
2. **Create alert from panel:**
   - Select "Error Rate (%)" panel
   - Click "More" → "New alert rule from this panel"
   - Configure notification channel (Slack, PagerDuty, email)
3. **Repeat for critical panels:**
   - Service Availability (Uptime %)
   - SLO Error Budget Remaining

---

## Part 3: Post-Import Validation

### End-to-End Smoke Test

Run this script to verify the full observability stack:

```bash
#!/bin/bash
# File: scripts/validate_observability.sh

BACKEND_URL="https://your-backend-url.com"
PROMETHEUS_URL="https://your-prometheus-url.com"
GRAFANA_URL="https://your-grafana-url.com"

echo "=== Observability Stack Validation ==="

# 1. Verify backend /metrics endpoint
echo "[1/5] Checking backend /metrics..."
curl -sf "$BACKEND_URL/metrics" | grep -q "http_request_duration_seconds" && echo "✅ Metrics endpoint OK" || echo "❌ Metrics endpoint FAILED"

# 2. Verify Prometheus is scraping
echo "[2/5] Checking Prometheus scraping..."
curl -sf "$PROMETHEUS_URL/api/v1/query?query=up{job=\"relay-backend\"}" | jq -r '.data.result[0].value[1]' | grep -q "1" && echo "✅ Prometheus scraping OK" || echo "❌ Prometheus scraping FAILED"

# 3. Verify alert rules loaded
echo "[3/5] Checking alert rules..."
ALERT_COUNT=$(curl -sf "$PROMETHEUS_URL/api/v1/rules" | jq -r '[.data.groups[].rules[] | select(.type=="alerting")] | length')
[[ "$ALERT_COUNT" -ge 8 ]] && echo "✅ Alert rules loaded ($ALERT_COUNT found)" || echo "❌ Alert rules FAILED ($ALERT_COUNT found, expected ≥8)"

# 4. Verify Grafana dashboard exists
echo "[4/5] Checking Grafana dashboard..."
curl -sf -H "Authorization: Bearer $GRAFANA_API_KEY" "$GRAFANA_URL/api/search?query=Relay%20Golden%20Signals" | jq -r '.[0].uid' | grep -q "." && echo "✅ Grafana dashboard OK" || echo "❌ Grafana dashboard FAILED"

# 5. Run sample query against SLO metrics
echo "[5/5] Validating SLO metrics..."
LATENCY_P99=$(curl -sf "$PROMETHEUS_URL/api/v1/query?query=histogram_quantile(0.99,%20rate(http_request_duration_seconds_bucket{path=~\"/actions|/audit\"}[5m]))" | jq -r '.data.result[0].value[1]')
if [[ -n "$LATENCY_P99" ]]; then
  echo "✅ SLO metrics OK (p99 latency: ${LATENCY_P99}s)"
else
  echo "❌ SLO metrics FAILED (no data returned)"
fi

echo ""
echo "=== Validation Complete ==="
```

**Expected Output:**
```
✅ Metrics endpoint OK
✅ Prometheus scraping OK
✅ Alert rules loaded (8 found)
✅ Grafana dashboard OK
✅ SLO metrics OK (p99 latency: 0.023s)
```

### Manual Verification Checklist

- [ ] **Generate test traffic:**
  ```bash
  # Send 100 requests to /actions endpoint
  for i in {1..100}; do curl -X GET "https://[backend-url]/actions"; done
  ```
- [ ] **Check Grafana dashboard updates:**
  - Request Rate panel should show spike
  - Total Requests (24h) should increment
- [ ] **Trigger a test alert:**
  ```bash
  # Stop backend service temporarily (triggers ServiceDown alert)
  railway service stop relay-backend
  # Wait 2 minutes for alert to fire
  # Check Prometheus UI for firing alert
  # Restart service
  railway service start relay-backend
  ```
- [ ] **Verify alert annotations appear on dashboard:**
  - Red vertical line should appear at time of alert
  - Hover over line to see "ServiceDown" alert name

---

## Part 4: Ongoing Maintenance

### Weekly Tasks

- [ ] **Review SLO compliance:**
  - Check "SLO Error Budget Remaining" gauge in Grafana
  - If budget < 80%, investigate error trends
- [ ] **Review firing alerts:**
  - Check Prometheus UI for any critical/page alerts
  - Verify alerts are actionable (not noisy)
- [ ] **Validate dashboard accuracy:**
  - Compare dashboard metrics to raw Prometheus queries
  - Ensure no stale data (check "Last updated" timestamp)

### Monthly Tasks

- [ ] **Update alert thresholds:**
  - Review SLO targets based on actual performance
  - Adjust alert `for` duration if alerts are too noisy/quiet
- [ ] **Rotate Grafana API keys:**
  - Generate new key in Grafana UI
  - Update CI/CD secrets if using automated imports
- [ ] **Backup dashboard JSON:**
  ```bash
  # Export current dashboard from Grafana
  curl -H "Authorization: Bearer $GRAFANA_API_KEY" \
    "$GRAFANA_URL/api/dashboards/uid/relay-golden-signals" > golden-signals-backup.json
  ```

### Quarterly Tasks

- [ ] **Conduct SLO review:**
  - Analyze 90-day trends in error budget consumption
  - Update SLO targets based on business requirements
- [ ] **Update alert runbooks:**
  - Add `runbook_url` annotations to alerts.json
  - Document response procedures for each alert

---

## Troubleshooting

### Issue: Dashboard Shows "No Data"

**Possible Causes:**
1. Prometheus not scraping backend metrics
2. Incorrect datasource selected in Grafana
3. Time range set to future/past with no data

**Resolution:**
```bash
# Verify Prometheus scraping
curl -sf "https://[prometheus-url]/api/v1/targets" | jq -r '.data.activeTargets[] | select(.labels.job=="relay-backend") | .health'
# Expected: "up"

# Check if metrics exist
curl -sf "https://[prometheus-url]/api/v1/query?query=http_requests_total" | jq -r '.data.result | length'
# Expected: >0
```

### Issue: Alerts Not Firing

**Possible Causes:**
1. Alert rule syntax error
2. Metrics not matching label selectors
3. `for` duration not yet elapsed

**Resolution:**
```bash
# Validate alert expression manually
curl -sf "https://[prometheus-url]/api/v1/query?query=histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{path=~\"/actions|/audit\"}[5m]))"
# Should return numeric value

# Check alert state in Prometheus UI
# Navigate to: /alerts
# Look for alert in "Pending" state (waiting for `for` duration)
```

### Issue: Rate Limiting Metrics Missing

**Possible Causes:**
1. Backend not exporting `http_requests_total{status="429"}` metric
2. No rate limit breaches in timeframe (metric counter = 0)

**Resolution:**
```bash
# Trigger rate limit intentionally
for i in {1..200}; do curl -X GET "https://[backend-url]/actions"; done
# Expected: Some requests return 429 status

# Verify metric exists
curl -sf "https://[prometheus-url]/api/v1/query?query=http_requests_total{status=\"429\"}" | jq -r '.data.result'
```

---

## Sign-Off

**Import Status:** ⏳ **PENDING DEPLOYMENT**

Once alerts and dashboard are imported to production, mark this checklist complete.

**Responsible Team:** Platform + SRE
**Next Milestone:** 24-hour production monitoring to validate SLO compliance
**Reference:** See SLO-ALERT-CHECKLIST.md for alignment verification
