# Staging Observability: Dashboards & Alerts

This guide covers Prometheus scraping of `/metrics`, Grafana dashboards, Tempo/Jaeger trace viewing, and a minimal alert rule for latency.

**Prerequisites:**
- Sprint 46: Prometheus metrics at `/metrics` endpoint
- Sprint 47: OpenTelemetry tracing with OTLP exporter
- Staging deployment on Railway (or similar PaaS)
- Docker environment for Prometheus/Grafana/Tempo stack

---

## 1. Architecture Overview

```
┌─────────────────────┐
│  DJP Workflow API   │
│  (Railway Staging)  │
│                     │
│  /metrics endpoint  │◄─────── Prometheus (scrape every 15s)
│  OTLP traces        │────────► Tempo/Jaeger (gRPC :4317)
└─────────────────────┘
         │
         │ traces + metrics
         ▼
┌─────────────────────┐
│      Grafana        │
│  - Prometheus DS    │
│  - Tempo DS         │
│  - Golden Signals   │
│  - Alert Rules      │
└─────────────────────┘
```

**Key Components:**
- **DJP Workflow API**: FastAPI service exposing `/metrics` and sending OTLP traces
- **Prometheus**: Scrapes metrics from `/metrics` endpoint every 15s
- **Tempo/Jaeger**: Receives OTLP traces via gRPC on port 4317
- **Grafana**: Visualizes metrics and traces with Golden Signals dashboard

---

## 2. Environment Configuration

### Staging Environment Variables (Railway Dashboard)

Set these in your Railway environment:

```bash
# Telemetry (Sprint 46-47)
TELEMETRY_ENABLED=true
TELEMETRY_BACKEND=hybrid          # Prometheus + OpenTelemetry

# OpenTelemetry Tracing
OTEL_EXPORTER=otlp                # Send to Tempo/Jaeger
OTEL_ENDPOINT=http://tempo:4317   # gRPC endpoint (adjust for your setup)
OTEL_SERVICE_NAME=djp-workflow-staging
OTEL_TRACE_SAMPLE=0.05            # 5% sampling (balance cost/visibility)

# API Configuration
APP_ENV=staging
LOG_LEVEL=INFO
```

**Important Notes:**
- `OTEL_ENDPOINT`: If running Tempo locally via Docker, use `http://localhost:4317`. If Tempo is in a separate container/service, use the service name or IP.
- `OTEL_TRACE_SAMPLE=0.05`: Samples 5% of traces. Adjust based on traffic volume and storage costs.
- `TELEMETRY_BACKEND=hybrid`: Enables both Prometheus metrics and OpenTelemetry traces.

---

## 3. Prometheus Configuration

### prometheus.yml

Create a `prometheus.yml` configuration to scrape your staging API:

```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    environment: 'staging'
    cluster: 'djp-workflow'

scrape_configs:
  - job_name: 'djp-workflow-staging'
    metrics_path: '/metrics'
    scheme: https
    static_configs:
      - targets:
          - '<your-railway-url>.up.railway.app'  # Replace with actual Railway URL
    scrape_interval: 15s
    scrape_timeout: 10s
    honor_labels: true

# Alert rules (loaded from external file)
rule_files:
  - 'alerts.yml'
```

**Deployment Options:**

**Option A: Docker Compose (Local/VPS)**
```yaml
version: '3.8'
services:
  prometheus:
    image: prom/prometheus:latest
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - ./alerts.yml:/etc/prometheus/alerts.yml
      - prometheus-data:/prometheus
    ports:
      - "9090:9090"
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'

volumes:
  prometheus-data:
```

**Option B: Railway Service**
Deploy Prometheus as a separate Railway service with the config mounted.

### Verification

After deploying Prometheus, verify scraping:

1. Access Prometheus UI: `http://localhost:9090` (or your Prometheus URL)
2. Navigate to **Status → Targets**
3. Confirm `djp-workflow-staging` target is `UP`
4. Query metrics in the **Graph** tab:
   ```promql
   http_requests_total{job="djp-workflow-staging"}
   ```

---

## 4. Grafana Dashboards

### Grafana Setup

**Option A: Docker Compose**
```yaml
version: '3.8'
services:
  grafana:
    image: grafana/grafana:latest
    volumes:
      - grafana-data:/var/lib/grafana
      - ./grafana/provisioning:/etc/grafana/provisioning
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=admin  # Change in production!
      - GF_USERS_ALLOW_SIGN_UP=false
    ports:
      - "3000:3000"
    depends_on:
      - prometheus
      - tempo

volumes:
  grafana-data:
```

**Option B: Grafana Cloud**
Use Grafana Cloud's free tier for hosted Grafana. Configure data sources to point to your Prometheus and Tempo endpoints.

### Data Source Configuration

**Prometheus Data Source:**
```yaml
# grafana/provisioning/datasources/prometheus.yml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
```

**Tempo Data Source:**
```yaml
# grafana/provisioning/datasources/tempo.yml
apiVersion: 1
datasources:
  - name: Tempo
    type: tempo
    access: proxy
    url: http://tempo:3200
    editable: true
    jsonData:
      httpMethod: GET
      tracesToLogs:
        datasourceUid: 'loki'  # Optional: link traces to logs
```

### Golden Signals Dashboard

Create a dashboard with these panels:

#### Panel 1: Request Rate (Traffic)
```promql
# Requests per second by endpoint
sum(rate(http_requests_total{job="djp-workflow-staging"}[5m])) by (endpoint)
```

#### Panel 2: Error Rate
```promql
# Error rate percentage by endpoint
sum(rate(http_requests_total{job="djp-workflow-staging", status=~"5.."}[5m])) by (endpoint)
  /
sum(rate(http_requests_total{job="djp-workflow-staging"}[5m])) by (endpoint)
  * 100
```

#### Panel 3: P50/P95/P99 Latency
```promql
# P50 latency (median)
histogram_quantile(0.50,
  sum(rate(http_request_duration_seconds_bucket{job="djp-workflow-staging"}[5m])) by (le, endpoint)
)

# P95 latency
histogram_quantile(0.95,
  sum(rate(http_request_duration_seconds_bucket{job="djp-workflow-staging"}[5m])) by (le, endpoint)
)

# P99 latency
histogram_quantile(0.99,
  sum(rate(http_request_duration_seconds_bucket{job="djp-workflow-staging"}[5m])) by (le, endpoint)
)
```

#### Panel 4: Saturation - In-Flight Requests
```promql
# Current in-flight requests
http_requests_in_flight{job="djp-workflow-staging"}
```

#### Panel 5: DJP Workflow Metrics
```promql
# Triage workflow duration (P95)
histogram_quantile(0.95,
  sum(rate(triage_duration_seconds_bucket{job="djp-workflow-staging"}[5m])) by (le)
)

# Debate rounds per workflow
rate(debate_rounds_total{job="djp-workflow-staging"}[5m])

# Published vs redacted decisions
sum(rate(publish_decisions_total{job="djp-workflow-staging"}[5m])) by (status)
```

### Example Dashboard JSON

Save this as `grafana/provisioning/dashboards/golden-signals.json`:

```json
{
  "dashboard": {
    "title": "DJP Workflow - Golden Signals (Staging)",
    "tags": ["staging", "golden-signals", "djp"],
    "timezone": "browser",
    "panels": [
      {
        "id": 1,
        "title": "Request Rate (req/s)",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{job=\"djp-workflow-staging\"}[5m])) by (endpoint)",
            "legendFormat": "{{endpoint}}"
          }
        ],
        "type": "graph"
      },
      {
        "id": 2,
        "title": "Error Rate (%)",
        "targets": [
          {
            "expr": "sum(rate(http_requests_total{job=\"djp-workflow-staging\", status=~\"5..\"}[5m])) by (endpoint) / sum(rate(http_requests_total{job=\"djp-workflow-staging\"}[5m])) by (endpoint) * 100",
            "legendFormat": "{{endpoint}}"
          }
        ],
        "type": "graph"
      },
      {
        "id": 3,
        "title": "Latency Percentiles",
        "targets": [
          {
            "expr": "histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket{job=\"djp-workflow-staging\"}[5m])) by (le, endpoint))",
            "legendFormat": "P50 - {{endpoint}}"
          },
          {
            "expr": "histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job=\"djp-workflow-staging\"}[5m])) by (le, endpoint))",
            "legendFormat": "P95 - {{endpoint}}"
          },
          {
            "expr": "histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{job=\"djp-workflow-staging\"}[5m])) by (le, endpoint))",
            "legendFormat": "P99 - {{endpoint}}"
          }
        ],
        "type": "graph"
      }
    ]
  }
}
```

---

## 5. Tempo/Jaeger Trace Backend

### Tempo Configuration

**Docker Compose:**
```yaml
version: '3.8'
services:
  tempo:
    image: grafana/tempo:latest
    command: [ "-config.file=/etc/tempo.yaml" ]
    volumes:
      - ./tempo.yaml:/etc/tempo.yaml
      - tempo-data:/tmp/tempo
    ports:
      - "3200:3200"   # Tempo HTTP
      - "4317:4317"   # OTLP gRPC
      - "4318:4318"   # OTLP HTTP

volumes:
  tempo-data:
```

**tempo.yaml:**
```yaml
server:
  http_listen_port: 3200

distributor:
  receivers:
    otlp:
      protocols:
        grpc:
          endpoint: 0.0.0.0:4317
        http:
          endpoint: 0.0.0.0:4318

storage:
  trace:
    backend: local
    local:
      path: /tmp/tempo/blocks

compactor:
  compaction:
    block_retention: 48h  # Keep traces for 2 days in staging
```

### Viewing Traces in Grafana

1. Navigate to **Explore** in Grafana
2. Select **Tempo** data source
3. Search by:
   - **Trace ID**: Paste trace ID from logs (see Sprint 47 log correlation)
   - **Service Name**: `djp-workflow-staging`
   - **Span Name**: `http.server`, `job.run`, `external.api.call`
4. View trace waterfall with timing breakdown

**Example Trace Flow:**
```
http.server (POST /api/triage)  [1.2s total]
├─ job.run (triage_workflow)    [1.1s]
│  ├─ external.api.call (openai/gpt-4o)     [450ms]
│  ├─ external.api.call (anthropic/claude)  [500ms]
│  └─ external.api.call (judge)             [150ms]
└─ http.response                             [10ms]
```

---

## 6. Alert Rules

Create `alerts.yml` for Prometheus alert rules:

```yaml
groups:
  - name: djp_workflow_staging
    interval: 15s
    rules:
      # Alert: High P99 latency
      - alert: HighP99Latency
        expr: |
          histogram_quantile(0.99,
            sum(rate(http_request_duration_seconds_bucket{job="djp-workflow-staging"}[5m])) by (le, endpoint)
          ) > 1
        for: 5m
        labels:
          severity: warning
          environment: staging
        annotations:
          summary: "High P99 latency on {{ $labels.endpoint }}"
          description: "P99 latency is {{ $value }}s (threshold: 1s) for endpoint {{ $labels.endpoint }}"

      # Alert: High error rate
      - alert: HighErrorRate
        expr: |
          sum(rate(http_requests_total{job="djp-workflow-staging", status=~"5.."}[5m])) by (endpoint)
            /
          sum(rate(http_requests_total{job="djp-workflow-staging"}[5m])) by (endpoint)
            > 0.05
        for: 5m
        labels:
          severity: critical
          environment: staging
        annotations:
          summary: "High error rate on {{ $labels.endpoint }}"
          description: "Error rate is {{ $value | humanizePercentage }} (threshold: 5%) for endpoint {{ $labels.endpoint }}"

      # Alert: Workflow processing time too high
      - alert: SlowTriageWorkflow
        expr: |
          histogram_quantile(0.95,
            sum(rate(triage_duration_seconds_bucket{job="djp-workflow-staging"}[5m])) by (le)
          ) > 3
        for: 10m
        labels:
          severity: warning
          environment: staging
        annotations:
          summary: "Triage workflow P95 latency exceeds 3s"
          description: "Triage workflow P95 latency is {{ $value }}s (threshold: 3s)"

      # Alert: Too many redactions (may indicate quality issue)
      - alert: HighRedactionRate
        expr: |
          sum(rate(publish_decisions_total{job="djp-workflow-staging", status="redacted"}[15m]))
            /
          sum(rate(publish_decisions_total{job="djp-workflow-staging"}[15m]))
            > 0.20
        for: 15m
        labels:
          severity: info
          environment: staging
        annotations:
          summary: "High redaction rate detected"
          description: "{{ $value | humanizePercentage }} of workflows are being redacted (threshold: 20%)"
```

### Alert Notification Channels

Configure Grafana notification channels in **Alerting → Notification channels**:

- **Slack**: Post alerts to #staging-alerts channel
- **Email**: Send to devops@yourcompany.com
- **PagerDuty**: For critical alerts (optional for staging)

---

## 7. Verification Scripts

Use `scripts/verify_staging.py` to test the staging observability stack:

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate   # Windows

# Run verification
python scripts/verify_staging.py
```

This script will:
1. Check if `/metrics` endpoint is accessible and returning Prometheus metrics
2. Send a test request to `/api/triage` to generate traces
3. Verify trace ID is returned in logs
4. Check Prometheus for recent metrics (requires Prometheus URL)
5. Search Tempo for the trace ID (requires Tempo URL)

---

## 8. Deployment Checklist

### Pre-Deployment
- [ ] Review `configs/.env.example` staging configuration
- [ ] Set all telemetry environment variables in Railway dashboard
- [ ] Deploy Prometheus with scraping configuration
- [ ] Deploy Tempo with OTLP receivers enabled
- [ ] Deploy Grafana with Prometheus and Tempo data sources

### Post-Deployment
- [ ] Verify Railway deployment is healthy (check logs)
- [ ] Access `/metrics` endpoint and confirm metrics are exposed
- [ ] Check Prometheus targets (should show `djp-workflow-staging` as UP)
- [ ] Run `scripts/verify_staging.py` to generate test traces
- [ ] View traces in Grafana Explore (Tempo data source)
- [ ] Import Golden Signals dashboard
- [ ] Configure alert rules and notification channels
- [ ] Monitor for 24 hours to establish baseline performance

### 24-Hour Stability Validation
After deployment, monitor these metrics for 24 hours:

- **Request rate**: Should be stable, no unexpected spikes
- **Error rate**: Should be < 1% (excluding expected 4xx client errors)
- **P99 latency**: Should be < 1s for `/api/render`, < 3s for `/api/triage`
- **Memory usage**: Should not grow unboundedly (check Railway metrics)
- **Trace sampling**: Verify traces are appearing in Tempo at expected rate

---

## 9. Troubleshooting

### Metrics Not Appearing in Prometheus

**Symptoms:**
- Prometheus target shows as DOWN
- No metrics in Grafana queries

**Solutions:**
1. Check Railway logs for errors in telemetry initialization
2. Verify `TELEMETRY_ENABLED=true` and `TELEMETRY_BACKEND=prom` or `hybrid`
3. Test `/metrics` endpoint directly: `curl https://<your-url>/metrics`
4. Check Prometheus scrape config has correct URL and scheme (https)
5. Verify Railway firewall/security groups allow Prometheus access

### Traces Not Appearing in Tempo

**Symptoms:**
- No traces in Grafana Explore
- Logs show trace IDs but traces not searchable

**Solutions:**
1. Check `OTEL_EXPORTER=otlp` is set (not `console` or `none`)
2. Verify `OTEL_ENDPOINT` points to correct Tempo gRPC endpoint (`:4317`)
3. Check Tempo logs for OTLP receiver errors
4. Test OTLP endpoint connectivity from Railway:
   ```bash
   # In Railway console
   curl -v http://tempo:4317
   ```
5. Verify `OTEL_TRACE_SAMPLE` is > 0 (e.g., `0.05` for 5% sampling)
6. Check if sample rate is too low for low-traffic staging

### Trace IDs Not in Logs

**Symptoms:**
- Logs don't show `trace_id` field
- Can't correlate traces with logs

**Solutions:**
1. Verify `TELEMETRY_BACKEND=otel` or `hybrid` (not `prom` only)
2. Check `src/telemetry/log_correlation.py` is being initialized
3. Confirm structured logging format supports extra fields
4. Check log handler configuration (JSON format recommended)

### High Cardinality Warning

**Symptoms:**
- Prometheus queries slow down
- Grafana timeouts

**Solutions:**
1. Check endpoint normalization in `TelemetryMiddleware` (see Sprint 46)
2. Verify dynamic path segments are being normalized (e.g., `/api/user/123` → `/api/user/:id`)
3. Review metric labels - avoid high-cardinality labels like request_id, user_id, trace_id

---

## 10. Performance Impact

Based on Sprint 47 testing:

- **Metrics collection (Prometheus)**: < 1ms overhead per request
- **Trace creation (OTel, console exporter)**: < 2ms overhead per request
- **Trace export (OTLP)**: Asynchronous, no blocking, < 5ms amortized
- **Sampling at 5%**: 95% of requests have zero tracing overhead

**Memory Usage:**
- Prometheus client: ~10MB baseline
- OpenTelemetry SDK: ~20MB baseline
- Per-trace memory: ~5KB (spans, attributes, context)

**Network Bandwidth:**
- Metrics scrape (15s interval): ~5KB per scrape (~20KB/min)
- OTLP traces (5% sampling, 100 req/min): ~15KB/min
- Total: ~35KB/min (~2MB/hour)

**Recommendations:**
- Start with 5% sampling, adjust based on traffic volume
- Use OTLP HTTP (port 4318) if gRPC is blocked
- Consider head-based sampling in high-traffic environments

---

## 11. Next Steps

After 24-hour stability validation:

1. **Sprint 49: Invite-only Beta**
   - API key management
   - Usage metering (Prometheus metrics)
   - Rate limiting per API key
   - Beta user dashboards

2. **Production Deployment**
   - Replicate staging setup with production URLs
   - Increase sampling rate (10-20% for production)
   - Add SLO dashboards (Service Level Objectives)
   - Configure production alert escalation

3. **Advanced Observability**
   - Distributed tracing for external API calls (OpenAI, Anthropic)
   - Custom span attributes for workflow metadata (draft count, model, citations)
   - Exemplars: Link Prometheus metrics to Tempo traces
   - Log aggregation: Loki integration for centralized logging

---

## 12. References

- **Sprint 46**: [SPRINT46-NOTES.md](../perf/SPRINT46-NOTES.md) - Prometheus metrics
- **Sprint 47**: [SPRINT47-NOTES.md](../perf/SPRINT47-NOTES.md) - OpenTelemetry tracing
- **Prometheus Docs**: https://prometheus.io/docs/
- **Grafana Dashboards**: https://grafana.com/docs/grafana/latest/dashboards/
- **Tempo Docs**: https://grafana.com/docs/tempo/latest/
- **OpenTelemetry**: https://opentelemetry.io/docs/
- **Railway Deployment**: https://docs.railway.app/

---

## Success Criteria

Sprint 48 is complete when:

- ✅ Staging environment has telemetry enabled (`TELEMETRY_BACKEND=hybrid`)
- ✅ Prometheus is scraping `/metrics` every 15s
- ✅ Tempo is receiving OTLP traces via gRPC
- ✅ Grafana has Golden Signals dashboard with P50/P95/P99 panels
- ✅ Alert rules configured for high latency and error rate
- ✅ Verification script passes all checks
- ✅ 24-hour stability validation shows < 1% error rate, P99 < 1s
- ✅ Documentation complete and operational runbook tested

**Next**: Sprint 49 - Invite-only Beta with API keys and usage metering.
