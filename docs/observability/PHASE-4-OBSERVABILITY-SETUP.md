# Phase 4: Observability Setup Plan

**Date:** 2025-10-11
**Sprint:** 54 - Gmail Rich Email Integration
**Status:** 📋 Planning
**Duration:** Parallel with 24-48hr controller observation

## Overview

Phase 4 establishes production-grade observability for the Gmail Rich Email integration, enabling real-time monitoring, alerting, and troubleshooting through Grafana dashboards and Prometheus alerts.

**Success Criteria:**
- ✅ Grafana dashboards displaying key metrics (latency, errors, throughput)
- ✅ Prometheus alert rules configured (controller health, error rates)
- ✅ Structured error frequency tracking
- ✅ Rollout controller decision visibility
- ✅ SLO monitoring queries documented

---

## Architecture

```
┌─────────────────────┐
│  Gmail Action       │
│  Adapter            │──────┐
└─────────────────────┘      │
                              │ Prometheus Metrics
┌─────────────────────┐      │ (Counter, Histogram, Gauge)
│  MIME Builder       │──────┤
└─────────────────────┘      │
                              │
┌─────────────────────┐      │
│  Rollout Controller │──────┘
└─────────────────────┘
                              │
                              ▼
                    ┌──────────────────┐
                    │  Prometheus      │
                    │  (metrics store) │
                    └──────────────────┘
                              │
                              │ PromQL Queries
                              ▼
                    ┌──────────────────┐
                    │  Grafana         │
                    │  (dashboards)    │
                    └──────────────────┘
                              │
                              │ Alert Manager
                              ▼
                    ┌──────────────────┐
                    │  Notifications   │
                    │  (Slack, Email)  │
                    └──────────────────┘
```

---

## Part 1: Prometheus Metrics Inventory

### Existing Metrics (from `src/telemetry/prom.py`)

#### Action Execution Metrics
```python
action_exec_total = Counter(
    "action_exec_total",
    "Total action executions",
    ["action", "status"],  # status: success, error, validation_error
)

action_exec_duration_seconds = Histogram(
    "action_exec_duration_seconds",
    "Action execution latency",
    ["action"],
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0],
)
```

**Labels:**
- `action`: "google_gmail_send"
- `status`: "success", "error", "validation_error"

#### MIME Builder Metrics
```python
mime_build_duration_seconds = Histogram(
    "mime_build_duration_seconds",
    "MIME message build time",
    buckets=[0.01, 0.05, 0.1, 0.5, 1.0],
)

mime_sanitization_changes = Counter(
    "mime_sanitization_changes",
    "HTML sanitization changes made",
    ["change_type"],  # e.g., "script_removed", "event_handler_removed"
)

mime_attachment_bytes = Counter(
    "mime_attachment_bytes",
    "Total bytes in attachments",
)
```

#### Rollout Controller Metrics (from Sprint 53 Phase B)
```python
rollout_decision_total = Counter(
    "rollout_decision_total",
    "Rollout controller decisions",
    ["decision"],  # promote, rollback, hold, dry_run_would_promote, dry_run_would_rollback
)

rollout_current_percentage = Gauge(
    "rollout_current_percentage",
    "Current rollout percentage for feature",
    ["feature"],  # e.g., "gmail_rich_email"
)

rollout_slo_compliance = Gauge(
    "rollout_slo_compliance",
    "Whether feature is meeting SLOs (1=yes, 0=no)",
    ["feature"],
)
```

### New Metrics to Add

#### Structured Error Tracking
```python
# Add to src/telemetry/prom.py
structured_error_total = Counter(
    "structured_error_total",
    "Structured errors by code",
    ["error_code", "action"],  # error_code: validation_error_*, internal_error_*
)
```

**Usage in `src/actions/adapters/google.py`:**
```python
from src.telemetry.prom import structured_error_total

def _create_structured_error(self, error_code: str, message: str, field: Optional[str] = None, details: Optional[dict] = None):
    structured_error_total.labels(error_code=error_code, action="google_gmail_send").inc()
    # ... rest of method
```

---

## Part 2: Grafana Dashboard Specifications

### Dashboard 1: Gmail Rich Email Integration Overview

**Purpose:** High-level health and performance monitoring

#### Panel 1.1: Request Rate & Status
**Type:** Graph (Time Series)
**Query:**
```promql
# Total requests per minute
sum(rate(action_exec_total{action="google_gmail_send"}[1m])) by (status)
```

**Visualization:**
- Line graph with 3 series: success (green), error (red), validation_error (yellow)
- Y-axis: Requests/sec
- Legend: Show current, min, max, avg

#### Panel 1.2: Latency Percentiles
**Type:** Graph (Time Series)
**Query:**
```promql
# P50 latency
histogram_quantile(0.5, rate(action_exec_duration_seconds_bucket{action="google_gmail_send"}[5m]))

# P95 latency
histogram_quantile(0.95, rate(action_exec_duration_seconds_bucket{action="google_gmail_send"}[5m]))

# P99 latency
histogram_quantile(0.99, rate(action_exec_duration_seconds_bucket{action="google_gmail_send"}[5m]))
```

**Visualization:**
- 3 lines: P50 (blue), P95 (orange), P99 (red)
- Y-axis: Seconds
- Threshold line at 2.0s (SLO target: P95 < 2s)

#### Panel 1.3: Error Rate
**Type:** Stat (Single Value)
**Query:**
```promql
# Error rate over last 5 minutes
sum(rate(action_exec_total{action="google_gmail_send",status=~"error|validation_error"}[5m]))
/
sum(rate(action_exec_total{action="google_gmail_send"}[5m]))
* 100
```

**Visualization:**
- Large number showing percentage
- Color thresholds:
  - Green: < 1%
  - Yellow: 1-5%
  - Red: > 5%

#### Panel 1.4: MIME Build Time
**Type:** Graph (Time Series)
**Query:**
```promql
# P95 MIME build time
histogram_quantile(0.95, rate(mime_build_duration_seconds_bucket[5m]))
```

**Visualization:**
- Single line graph
- Y-axis: Seconds
- Threshold line at 0.5s (target: sub-second)

#### Panel 1.5: Attachment Throughput
**Type:** Graph (Time Series)
**Query:**
```promql
# Bytes per minute
rate(mime_attachment_bytes[1m])
```

**Visualization:**
- Area graph
- Y-axis: Bytes/sec (formatted as MB/s)

#### Panel 1.6: HTML Sanitization Activity
**Type:** Graph (Time Series)
**Query:**
```promql
# Sanitization changes per minute
sum(rate(mime_sanitization_changes[1m])) by (change_type)
```

**Visualization:**
- Stacked area chart by change_type
- Shows how often XSS attempts are blocked

---

### Dashboard 2: Rollout Controller Monitoring

**Purpose:** Track rollout controller decisions and health

#### Panel 2.1: Current Rollout Percentage
**Type:** Gauge
**Query:**
```promql
rollout_current_percentage{feature="gmail_rich_email"}
```

**Visualization:**
- Circular gauge 0-100%
- Color gradient: 0% (red) → 100% (green)

#### Panel 2.2: Controller Decisions
**Type:** Graph (Time Series)
**Query:**
```promql
# Decision rate per hour
sum(rate(rollout_decision_total[1h])) by (decision)
```

**Visualization:**
- Stacked bar chart
- Series: promote, rollback, hold, dry_run_would_promote, dry_run_would_rollback

#### Panel 2.3: SLO Compliance
**Type:** Stat (Binary)
**Query:**
```promql
rollout_slo_compliance{feature="gmail_rich_email"}
```

**Visualization:**
- Show "COMPLIANT" (green) or "NON-COMPLIANT" (red)
- Value mapping: 1 → "COMPLIANT", 0 → "NON-COMPLIANT"

#### Panel 2.4: Decision Timeline
**Type:** State Timeline
**Query:**
```promql
rollout_decision_total
```

**Visualization:**
- Timeline showing when decisions were made
- Color-coded by decision type

#### Panel 2.5: Feature Health Score
**Type:** Graph (Time Series)
**Query:**
```promql
# Combined health metric (success rate * slo_compliance)
(
  sum(rate(action_exec_total{action="google_gmail_send",status="success"}[5m]))
  /
  sum(rate(action_exec_total{action="google_gmail_send"}[5m]))
)
* rollout_slo_compliance{feature="gmail_rich_email"}
```

**Visualization:**
- Single line graph (0.0 to 1.0)
- Threshold lines: 0.95 (warning), 0.99 (target)

---

### Dashboard 3: Structured Error Analysis

**Purpose:** Deep dive into validation and internal errors

#### Panel 3.1: Error Frequency by Code
**Type:** Bar Chart
**Query:**
```promql
# Count of each error code in last 24 hours
sum(increase(structured_error_total[24h])) by (error_code)
```

**Visualization:**
- Horizontal bar chart sorted by count
- Top 10 error codes

#### Panel 3.2: Validation Error Breakdown
**Type:** Pie Chart
**Query:**
```promql
# Validation errors only
sum(increase(structured_error_total{error_code=~"validation_error_.*"}[24h])) by (error_code)
```

**Visualization:**
- Pie chart showing proportions of each validation error type

#### Panel 3.3: Error Rate Over Time
**Type:** Graph (Time Series)
**Query:**
```promql
# Top 5 error codes over time
topk(5, sum(rate(structured_error_total[5m])) by (error_code))
```

**Visualization:**
- Line graph with top 5 error codes
- Auto-legend with current values

#### Panel 3.4: Critical Errors (Table)
**Type:** Table
**Query:**
```promql
# Errors in last hour, sorted by count
topk(20, sum(increase(structured_error_total[1h])) by (error_code, action))
```

**Visualization:**
- Table columns: Error Code, Action, Count
- Sortable by count

---

## Part 3: Prometheus Alert Rules

### Alert Configuration File
**File:** `config/prometheus/alerts/gmail_integration.yml`

```yaml
groups:
  - name: gmail_rich_email_integration
    interval: 30s
    rules:

      # Alert 1: High Error Rate
      - alert: GmailSendHighErrorRate
        expr: |
          (
            sum(rate(action_exec_total{action="google_gmail_send",status=~"error"}[5m]))
            /
            sum(rate(action_exec_total{action="google_gmail_send"}[5m]))
          ) > 0.05
        for: 5m
        labels:
          severity: warning
          component: gmail_adapter
        annotations:
          summary: "Gmail send error rate above 5%"
          description: "Error rate is {{ $value | humanizePercentage }} over the last 5 minutes (threshold: 5%)"
          dashboard: "https://grafana/d/gmail-integration/overview"

      # Alert 2: High Latency (P95)
      - alert: GmailSendHighLatency
        expr: |
          histogram_quantile(0.95,
            rate(action_exec_duration_seconds_bucket{action="google_gmail_send"}[5m])
          ) > 2.0
        for: 10m
        labels:
          severity: warning
          component: gmail_adapter
        annotations:
          summary: "Gmail send P95 latency above 2 seconds"
          description: "P95 latency is {{ $value }}s (threshold: 2.0s)"
          dashboard: "https://grafana/d/gmail-integration/overview"

      # Alert 3: Rollout Controller Stalled
      - alert: RolloutControllerStalled
        expr: |
          (
            time() - max(rollout_decision_total) by (feature)
          ) > 3600
        for: 5m
        labels:
          severity: critical
          component: rollout_controller
        annotations:
          summary: "Rollout controller hasn't made a decision in 1+ hour"
          description: "Feature {{ $labels.feature }} hasn't had a controller decision in {{ $value | humanizeDuration }}"
          runbook: "https://docs/runbooks/rollout-controller-stalled"

      # Alert 4: Rollout Controller Failing SLO
      - alert: RolloutControllerSLOViolation
        expr: |
          rollout_slo_compliance{feature="gmail_rich_email"} == 0
        for: 15m
        labels:
          severity: warning
          component: rollout_controller
        annotations:
          summary: "Feature is not meeting SLO requirements"
          description: "Feature {{ $labels.feature }} has been non-compliant for 15+ minutes"
          dashboard: "https://grafana/d/rollout-controller/monitoring"

      # Alert 5: Validation Error Spike
      - alert: GmailValidationErrorSpike
        expr: |
          (
            sum(rate(structured_error_total{error_code=~"validation_error_.*"}[5m]))
            /
            sum(rate(action_exec_total{action="google_gmail_send"}[5m]))
          ) > 0.10
        for: 5m
        labels:
          severity: info
          component: validation
        annotations:
          summary: "Validation errors above 10% of requests"
          description: "{{ $value | humanizePercentage }} of requests are failing validation (may indicate client issue)"
          dashboard: "https://grafana/d/errors/structured-errors"

      # Alert 6: MIME Builder Slow
      - alert: MimeBuilderSlowPerformance
        expr: |
          histogram_quantile(0.95,
            rate(mime_build_duration_seconds_bucket[5m])
          ) > 0.5
        for: 10m
        labels:
          severity: warning
          component: mime_builder
        annotations:
          summary: "MIME builder P95 time above 500ms"
          description: "P95 MIME build time is {{ $value }}s (threshold: 0.5s)"
          dashboard: "https://grafana/d/gmail-integration/overview"

      # Alert 7: Sanitization High Activity
      - alert: HighSanitizationActivity
        expr: |
          sum(rate(mime_sanitization_changes[5m])) > 1.0
        for: 10m
        labels:
          severity: info
          component: html_sanitization
        annotations:
          summary: "High rate of HTML sanitization changes"
          description: "{{ $value }} sanitization changes/sec (may indicate malicious input attempts)"
          dashboard: "https://grafana/d/gmail-integration/overview"
```

---

## Part 4: Infrastructure Setup

### Step 1: Verify Prometheus is Running

```bash
# Check if Prometheus is already running
curl http://localhost:9090/api/v1/status/config

# If not, check Railway services
railway service list

# If Prometheus not deployed, check docker-compose or local setup
docker ps | grep prometheus
```

**Expected State:**
- Prometheus should be scraping metrics from the application
- Application exposes `/metrics` endpoint (FastAPI + prometheus_client)

### Step 2: Configure Prometheus Scrape Config

**File:** `config/prometheus/prometheus.yml`

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Main application metrics
  - job_name: 'openai-agents-workflows'
    static_configs:
      - targets: ['localhost:8003']  # Adjust port as needed
    metrics_path: '/metrics'
    scrape_interval: 10s

  # Rollout controller metrics (if separate service)
  - job_name: 'rollout-controller'
    static_configs:
      - targets: ['localhost:8004']  # Adjust if controller runs separately
    metrics_path: '/metrics'
    scrape_interval: 30s

# Load alert rules
rule_files:
  - 'alerts/gmail_integration.yml'

# Alertmanager configuration
alerting:
  alertmanagers:
    - static_configs:
        - targets: ['localhost:9093']
```

### Step 3: Set Up Grafana Datasource

**Option A: Grafana UI**
1. Navigate to Configuration → Data Sources
2. Add new Prometheus datasource
3. URL: `http://localhost:9090` (or Prometheus service URL)
4. Access: Server (default)
5. Save & Test

**Option B: Provisioned Datasource**

**File:** `config/grafana/datasources/prometheus.yml`

```yaml
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://localhost:9090
    isDefault: true
    editable: true
    jsonData:
      timeInterval: "10s"
```

### Step 4: Deploy Alert Manager (Optional but Recommended)

**File:** `config/alertmanager/alertmanager.yml`

```yaml
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'critical-alerts'
    - match:
        severity: warning
      receiver: 'warning-alerts'

receivers:
  - name: 'default'
    webhook_configs:
      - url: 'http://localhost:5001/alerts'  # Internal webhook handler

  - name: 'critical-alerts'
    # Add Slack, PagerDuty, or email config here
    webhook_configs:
      - url: 'http://localhost:5001/alerts/critical'

  - name: 'warning-alerts'
    webhook_configs:
      - url: 'http://localhost:5001/alerts/warning'

inhibit_rules:
  - source_match:
      severity: 'critical'
    target_match:
      severity: 'warning'
    equal: ['alertname', 'component']
```

---

## Part 5: Dashboard JSON Exports

### Dashboard 1: Gmail Integration Overview (Simplified)

**File:** `config/grafana/dashboards/gmail_integration_overview.json`

```json
{
  "dashboard": {
    "title": "Gmail Rich Email Integration - Overview",
    "tags": ["gmail", "actions", "integration"],
    "timezone": "utc",
    "panels": [
      {
        "id": 1,
        "title": "Request Rate by Status",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(action_exec_total{action=\"google_gmail_send\"}[1m])) by (status)",
            "legendFormat": "{{ status }}"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Latency Percentiles",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.5, rate(action_exec_duration_seconds_bucket{action=\"google_gmail_send\"}[5m]))",
            "legendFormat": "P50"
          },
          {
            "expr": "histogram_quantile(0.95, rate(action_exec_duration_seconds_bucket{action=\"google_gmail_send\"}[5m]))",
            "legendFormat": "P95"
          },
          {
            "expr": "histogram_quantile(0.99, rate(action_exec_duration_seconds_bucket{action=\"google_gmail_send\"}[5m]))",
            "legendFormat": "P99"
          }
        ],
        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
      },
      {
        "id": 3,
        "title": "Error Rate",
        "type": "stat",
        "targets": [
          {
            "expr": "sum(rate(action_exec_total{action=\"google_gmail_send\",status=~\"error|validation_error\"}[5m])) / sum(rate(action_exec_total{action=\"google_gmail_send\"}[5m])) * 100"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "green"},
                {"value": 1, "color": "yellow"},
                {"value": 5, "color": "red"}
              ]
            }
          }
        },
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 8}
      }
    ]
  }
}
```

### Dashboard 2: Rollout Controller (Simplified)

**File:** `config/grafana/dashboards/rollout_controller.json`

```json
{
  "dashboard": {
    "title": "Rollout Controller - Gmail Rich Email",
    "tags": ["rollout", "controller", "slo"],
    "timezone": "utc",
    "panels": [
      {
        "id": 1,
        "title": "Current Rollout %",
        "type": "gauge",
        "targets": [
          {
            "expr": "rollout_current_percentage{feature=\"gmail_rich_email\"}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "unit": "percent",
            "min": 0,
            "max": 100,
            "thresholds": {
              "mode": "absolute",
              "steps": [
                {"value": 0, "color": "red"},
                {"value": 50, "color": "yellow"},
                {"value": 100, "color": "green"}
              ]
            }
          }
        },
        "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
      },
      {
        "id": 2,
        "title": "Controller Decisions",
        "type": "graph",
        "targets": [
          {
            "expr": "sum(rate(rollout_decision_total[1h])) by (decision)",
            "legendFormat": "{{ decision }}"
          }
        ],
        "gridPos": {"h": 8, "w": 18, "x": 6, "y": 0}
      },
      {
        "id": 3,
        "title": "SLO Compliance",
        "type": "stat",
        "targets": [
          {
            "expr": "rollout_slo_compliance{feature=\"gmail_rich_email\"}"
          }
        ],
        "fieldConfig": {
          "defaults": {
            "mappings": [
              {"value": 1, "text": "COMPLIANT", "color": "green"},
              {"value": 0, "text": "NON-COMPLIANT", "color": "red"}
            ]
          }
        },
        "gridPos": {"h": 4, "w": 6, "x": 0, "y": 8}
      }
    ]
  }
}
```

---

## Part 6: Implementation Checklist

### Phase 4A: Metrics Enhancement (Day 1)

- [ ] **Add structured error tracking metric**
  - [ ] Update `src/telemetry/prom.py` with `structured_error_total` counter
  - [ ] Instrument `src/actions/adapters/google.py` to track error codes
  - [ ] Test metric collection with validation error scenario

- [ ] **Verify existing metrics are being collected**
  - [ ] Check `/metrics` endpoint shows `action_exec_total`
  - [ ] Check `action_exec_duration_seconds_bucket` has data
  - [ ] Check `mime_build_duration_seconds_bucket` has data
  - [ ] Check `rollout_decision_total` is being incremented (dry-run mode)

### Phase 4B: Prometheus Configuration (Day 1)

- [ ] **Set up Prometheus scrape config**
  - [ ] Create/update `config/prometheus/prometheus.yml`
  - [ ] Configure scrape interval (10-15s recommended)
  - [ ] Add job for main application
  - [ ] Verify Prometheus can scrape `/metrics` endpoint

- [ ] **Create alert rules**
  - [ ] Create `config/prometheus/alerts/gmail_integration.yml`
  - [ ] Add all 7 alert rules (high error rate, latency, controller health, etc.)
  - [ ] Load alert rules in Prometheus config
  - [ ] Validate alert rule syntax with `promtool check rules`

### Phase 4C: Grafana Setup (Day 1-2)

- [ ] **Configure Grafana datasource**
  - [ ] Add Prometheus datasource
  - [ ] Test connection
  - [ ] Set as default datasource

- [ ] **Create Dashboard 1: Integration Overview**
  - [ ] Panel 1.1: Request rate by status
  - [ ] Panel 1.2: Latency percentiles (P50, P95, P99)
  - [ ] Panel 1.3: Error rate stat
  - [ ] Panel 1.4: MIME build time
  - [ ] Panel 1.5: Attachment throughput
  - [ ] Panel 1.6: Sanitization activity
  - [ ] Export JSON and save to `config/grafana/dashboards/`

- [ ] **Create Dashboard 2: Rollout Controller**
  - [ ] Panel 2.1: Current rollout percentage gauge
  - [ ] Panel 2.2: Controller decisions timeline
  - [ ] Panel 2.3: SLO compliance stat
  - [ ] Panel 2.4: Decision timeline (state timeline)
  - [ ] Panel 2.5: Feature health score
  - [ ] Export JSON and save to `config/grafana/dashboards/`

- [ ] **Create Dashboard 3: Structured Errors**
  - [ ] Panel 3.1: Error frequency by code (bar chart)
  - [ ] Panel 3.2: Validation error breakdown (pie chart)
  - [ ] Panel 3.3: Error rate over time
  - [ ] Panel 3.4: Critical errors table
  - [ ] Export JSON and save to `config/grafana/dashboards/`

### Phase 4D: Alerting (Day 2, Optional)

- [ ] **Set up Alert Manager** (if not already running)
  - [ ] Deploy Alert Manager container/service
  - [ ] Create `config/alertmanager/alertmanager.yml`
  - [ ] Configure notification channels (webhook, Slack, email)
  - [ ] Test alert routing with test alert

- [ ] **Test alert rules**
  - [ ] Trigger test validation error to test `GmailValidationErrorSpike`
  - [ ] Verify alert fires in Alert Manager
  - [ ] Verify notification is sent

### Phase 4E: Documentation (Day 2)

- [ ] **Create runbooks**
  - [ ] Runbook: `RolloutControllerStalled` - what to check, how to restart
  - [ ] Runbook: `GmailSendHighErrorRate` - common causes, mitigation
  - [ ] Runbook: `GmailSendHighLatency` - performance troubleshooting

- [ ] **Document PromQL queries**
  - [ ] Create `docs/observability/PROMETHEUS-QUERIES.md`
  - [ ] Example queries for common troubleshooting scenarios
  - [ ] SLO calculation queries

- [ ] **Create dashboard screenshots**
  - [ ] Screenshot Dashboard 1 with real data
  - [ ] Screenshot Dashboard 2 showing dry-run decisions
  - [ ] Add to `docs/evidence/sprint-54/`

---

## Part 7: Testing & Validation

### Test 1: Verify Metrics Collection

```bash
# Check metrics endpoint
curl http://localhost:8003/metrics | grep action_exec

# Expected output:
# action_exec_total{action="google_gmail_send",status="success"} 6
# action_exec_duration_seconds_bucket{action="google_gmail_send",le="0.5"} 3
# mime_build_duration_seconds_bucket{le="0.1"} 5
```

### Test 2: Query Prometheus

```bash
# Check if Prometheus has data
curl -G http://localhost:9090/api/v1/query \
  --data-urlencode 'query=action_exec_total{action="google_gmail_send"}'

# Expected: JSON response with metric values
```

### Test 3: Trigger Alert (Validation Error Spike)

```bash
# Run E2E test with multiple validation errors
python scripts/e2e_gmail_test.py --scenarios 6 --repeat 20

# Check if alert fires
curl http://localhost:9090/api/v1/alerts | jq '.data.alerts[] | select(.labels.alertname=="GmailValidationErrorSpike")'
```

### Test 4: Dashboard Queries

Open Grafana Explore and test each panel query:

```promql
# Test 1: Request rate
sum(rate(action_exec_total{action="google_gmail_send"}[1m])) by (status)

# Test 2: P95 latency
histogram_quantile(0.95, rate(action_exec_duration_seconds_bucket{action="google_gmail_send"}[5m]))

# Test 3: Error rate
sum(rate(action_exec_total{action="google_gmail_send",status=~"error"}[5m])) / sum(rate(action_exec_total{action="google_gmail_send"}[5m])) * 100
```

**Expected:** All queries return data, no syntax errors

---

## Part 8: Rollout Controller Observation Plan

### Observation Period: 24-48 Hours

**What to Monitor:**
1. **Decision Frequency**: Controller should evaluate every 5-15 minutes
2. **Dry-Run Decisions**: Track what controller WOULD do (promote/rollback/hold)
3. **SLO Compliance**: Should remain at 1.0 (compliant) if Gmail integration is healthy
4. **Metrics Continuity**: No gaps in time-series data

### Data Collection Queries

```promql
# Query 1: Decision timeline
increase(rollout_decision_total[24h])

# Query 2: SLO compliance over time
rollout_slo_compliance{feature="gmail_rich_email"}

# Query 3: Rollout percentage changes
delta(rollout_current_percentage{feature="gmail_rich_email"}[24h])

# Query 4: Would-promote count
increase(rollout_decision_total{decision="dry_run_would_promote"}[24h])

# Query 5: Would-rollback count
increase(rollout_decision_total{decision="dry_run_would_rollback"}[24h])
```

### Success Criteria for Observation

- ✅ Controller makes decisions regularly (no stalls)
- ✅ Dry-run decisions logged to audit trail
- ✅ SLO compliance metric updates correctly
- ✅ No unexpected errors in controller logs
- ✅ Metrics flow continuously to Prometheus

### After Observation Period

**Review Checklist:**
1. Export time-series data from Prometheus
2. Analyze decision patterns (any anomalies?)
3. Check audit logs for correlation IDs
4. Review structured error frequencies
5. Document findings in `docs/evidence/sprint-54/ROLLOUT-OBSERVATION-REPORT.md`

**Decision Point:**
- If observation successful → Proceed to gradual rollout (disable dry-run mode)
- If issues found → Investigate and extend observation period

---

## Part 9: SLO Monitoring Examples

### SLO 1: Availability (Success Rate > 99%)

```promql
# Current success rate (5-minute window)
sum(rate(action_exec_total{action="google_gmail_send",status="success"}[5m]))
/
sum(rate(action_exec_total{action="google_gmail_send"}[5m]))
* 100

# Target: > 99%
```

### SLO 2: Latency (P95 < 2 seconds)

```promql
# P95 latency
histogram_quantile(0.95,
  rate(action_exec_duration_seconds_bucket{action="google_gmail_send"}[5m])
)

# Target: < 2.0
```

### SLO 3: Error Budget (1% over 30 days)

```promql
# Total errors in last 30 days
sum(increase(action_exec_total{action="google_gmail_send",status=~"error"}[30d]))

# Total requests in last 30 days
sum(increase(action_exec_total{action="google_gmail_send"}[30d]))

# Error budget remaining
1 - (
  sum(increase(action_exec_total{action="google_gmail_send",status=~"error"}[30d]))
  /
  sum(increase(action_exec_total{action="google_gmail_send"}[30d]))
)

# Target: > 0 (error budget not exhausted)
```

### SLO 4: MIME Build Performance (P95 < 500ms)

```promql
# P95 MIME build time
histogram_quantile(0.95, rate(mime_build_duration_seconds_bucket[5m]))

# Target: < 0.5
```

---

## Part 10: Troubleshooting Guide

### Issue 1: Metrics Not Appearing in Prometheus

**Symptoms:**
- Grafana shows "No data"
- Prometheus query returns empty result

**Diagnosis:**
```bash
# Check if app is exposing metrics
curl http://localhost:8003/metrics

# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check Prometheus logs
docker logs prometheus-container
```

**Solutions:**
- Verify app is running on correct port
- Check Prometheus scrape config has correct target
- Ensure firewall allows Prometheus to reach app
- Check app logs for metric registration errors

### Issue 2: Alert Not Firing

**Symptoms:**
- Condition met but no alert in Alert Manager

**Diagnosis:**
```bash
# Check if alert rule is loaded
curl http://localhost:9090/api/v1/rules

# Check alert state
curl http://localhost:9090/api/v1/alerts

# Check Alert Manager logs
docker logs alertmanager-container
```

**Solutions:**
- Validate alert rule syntax with `promtool check rules`
- Ensure `for` duration has elapsed
- Check Alert Manager config for route issues
- Verify notification channel configuration

### Issue 3: Dashboard Shows Partial Data

**Symptoms:**
- Some panels work, others show "No data"

**Diagnosis:**
- Check Grafana query inspector (click query, view "Query Inspector")
- Run query directly in Prometheus to verify data exists
- Check time range selector in Grafana

**Solutions:**
- Adjust time range (some metrics may not have historical data yet)
- Verify metric names match exactly (case-sensitive)
- Check label selectors are correct

### Issue 4: Rollout Controller Not Recording Decisions

**Symptoms:**
- `rollout_decision_total` counter not incrementing

**Diagnosis:**
```bash
# Check if controller is running
ps aux | grep rollout

# Check controller logs
tail -f logs/connectors.jsonl | grep rollout

# Check Redis connection
redis-cli ping
```

**Solutions:**
- Ensure `ROLLOUT_DRY_RUN=true` is set in environment
- Verify controller loop is executing (check logs)
- Check Redis connection for metrics storage
- Restart controller process if stalled

---

## Part 11: Phase 4 Timeline

### Day 1 (Parallel with Controller Observation)
**Hours 1-2:**
- Add `structured_error_total` metric to codebase
- Verify existing metrics are being collected
- Test `/metrics` endpoint

**Hours 3-4:**
- Create Prometheus alert rules file
- Update Prometheus config to load alerts
- Validate alert syntax

**Hours 5-8:**
- Set up Grafana datasource
- Create Dashboard 1: Integration Overview
- Create Dashboard 2: Rollout Controller

### Day 2 (Parallel with Controller Observation)
**Hours 1-3:**
- Create Dashboard 3: Structured Errors
- Export all dashboard JSONs
- Test dashboard queries with real data

**Hours 4-6:**
- Set up Alert Manager (optional)
- Test alert rules with validation errors
- Configure notification channels

**Hours 7-8:**
- Create runbooks for common alerts
- Document PromQL queries
- Take dashboard screenshots

### End of 24-48hr Observation Period
**Review & Report:**
- Export controller metrics from Prometheus
- Analyze decision patterns
- Check audit logs
- Create observation report
- Decide: Proceed to rollout or investigate issues

---

## Part 12: Success Metrics

Phase 4 is considered complete when:

1. **Metrics Visibility:**
   - ✅ All metrics (action, MIME, controller) visible in Prometheus
   - ✅ Structured error tracking working
   - ✅ No gaps in time-series data

2. **Dashboards Operational:**
   - ✅ 3 Grafana dashboards created and functional
   - ✅ All panels showing real data
   - ✅ Dashboards exported as JSON

3. **Alerting Configured:**
   - ✅ 7 alert rules loaded in Prometheus
   - ✅ Alert Manager routing configured (if used)
   - ✅ At least 1 alert tested and verified

4. **Documentation Complete:**
   - ✅ Runbooks created for critical alerts
   - ✅ PromQL query examples documented
   - ✅ Troubleshooting guide available

5. **Controller Observation:**
   - ✅ 24-48 hours of dry-run metrics collected
   - ✅ Decision patterns analyzed
   - ✅ Observation report created
   - ✅ Go/no-go decision made for rollout

---

## Part 13: Next Steps After Phase 4

### If Observation Successful:
1. **Phase 5: Gradual Rollout**
   - Disable dry-run mode (`ROLLOUT_DRY_RUN=false`)
   - Start at 5% rollout
   - Monitor dashboards closely for 24 hours
   - Increment to 10%, 25%, 50%, 75%, 100% over 1-2 weeks

2. **Production Readiness**
   - Set up production Prometheus/Grafana instances
   - Configure production alert channels (PagerDuty, Slack)
   - Create on-call runbooks
   - Train team on dashboard usage

### If Issues Found During Observation:
1. **Investigate and Fix**
   - Analyze controller logs and metrics
   - Identify root cause of anomalies
   - Fix bugs or configuration issues
   - Extend observation period

2. **Re-test**
   - Run additional E2E tests
   - Verify fixes with isolated tests
   - Restart observation period

---

## Appendix A: File Locations

```
project_root/
├── config/
│   ├── prometheus/
│   │   ├── prometheus.yml                    # Prometheus config
│   │   └── alerts/
│   │       └── gmail_integration.yml         # Alert rules
│   ├── grafana/
│   │   ├── datasources/
│   │   │   └── prometheus.yml                # Datasource config
│   │   └── dashboards/
│   │       ├── gmail_integration_overview.json
│   │       ├── rollout_controller.json
│   │       └── structured_errors.json
│   └── alertmanager/
│       └── alertmanager.yml                  # Alert routing
├── docs/
│   ├── observability/
│   │   ├── PHASE-4-OBSERVABILITY-SETUP.md    # This document
│   │   ├── PROMETHEUS-QUERIES.md             # Query examples
│   │   └── RUNBOOKS.md                       # Alert runbooks
│   └── evidence/
│       └── sprint-54/
│           └── ROLLOUT-OBSERVATION-REPORT.md # Post-observation report
└── src/
    └── telemetry/
        └── prom.py                           # Metrics definitions
```

---

## Appendix B: References

- **Prometheus Documentation:** https://prometheus.io/docs/
- **Grafana Dashboard Guide:** https://grafana.com/docs/grafana/latest/dashboards/
- **PromQL Cheat Sheet:** https://promlabs.com/promql-cheat-sheet/
- **Alert Manager Configuration:** https://prometheus.io/docs/alerting/latest/configuration/

**Internal References:**
- Phase 3 Completion: `2025.10.10-2341-PHASE-3-COMPLETE.md`
- E2E Test Suite: `scripts/e2e_gmail_test.py`
- Existing Metrics: `src/telemetry/prom.py:60-199`
- Gmail Adapter: `src/actions/adapters/google.py:344-513`
- Rollout Controller: `src/rollout/controller.py` (Sprint 53 Phase B)

---

**Status:** Ready for implementation
**Estimated Duration:** 2 days (parallel with controller observation)
**Priority:** High (required for production rollout)

**Next Action:** Begin Phase 4A (Metrics Enhancement) while rollout controller runs in dry-run mode.
