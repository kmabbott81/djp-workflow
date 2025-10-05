# Grafana Golden Signals Queries

Copy these queries into Grafana dashboard panels for the DJP Workflow staging environment.

## Panel 1: Request Rate (Traffic)
**Query:**
```promql
sum(rate(http_requests_total{job="djp-workflow-staging"}[5m])) by (endpoint)
```
**Panel Type:** Graph
**Legend:** `{{endpoint}}`

---

## Panel 2: Error Rate (%)
**Query:**
```promql
sum(rate(http_requests_total{job="djp-workflow-staging", status_code=~"5.."}[5m])) by (endpoint)
  /
sum(rate(http_requests_total{job="djp-workflow-staging"}[5m])) by (endpoint)
  * 100
```
**Panel Type:** Graph
**Unit:** Percent (0-100)
**Legend:** `{{endpoint}}`

---

## Panel 3: P50 Latency
**Query:**
```promql
histogram_quantile(0.50, sum(rate(http_request_duration_seconds_bucket{job="djp-workflow-staging"}[5m])) by (le, endpoint))
```
**Panel Type:** Graph
**Unit:** Seconds (s)
**Legend:** `P50 - {{endpoint}}`

---

## Panel 4: P95 Latency
**Query:**
```promql
histogram_quantile(0.95, sum(rate(http_request_duration_seconds_bucket{job="djp-workflow-staging"}[5m])) by (le, endpoint))
```
**Panel Type:** Graph
**Unit:** Seconds (s)
**Legend:** `P95 - {{endpoint}}`
**Alert Threshold:** 500ms (warning)

---

## Panel 5: P99 Latency
**Query:**
```promql
histogram_quantile(0.99, sum(rate(http_request_duration_seconds_bucket{job="djp-workflow-staging"}[5m])) by (le, endpoint))
```
**Panel Type:** Graph
**Unit:** Seconds (s)
**Legend:** `P99 - {{endpoint}}`
**Alert Threshold:** 1s (critical)

---

## Panel 6: Request Count by Status Code
**Query:**
```promql
sum(rate(http_requests_total{job="djp-workflow-staging"}[5m])) by (endpoint, status_code)
```
**Panel Type:** Stacked Graph
**Legend:** `{{endpoint}} - {{status_code}}`

---

## Panel 7: In-Flight Requests (Saturation)
**Query:**
```promql
http_requests_in_flight{job="djp-workflow-staging"}
```
**Panel Type:** Graph
**Legend:** `In-flight requests`

---

## Panel 8: Memory Usage
**Query:**
```promql
process_resident_memory_bytes{job="djp-workflow-staging"}
```
**Panel Type:** Graph
**Unit:** Bytes
**Legend:** `Resident memory`

---

## Panel 9: CPU Usage
**Query:**
```promql
rate(process_cpu_seconds_total{job="djp-workflow-staging"}[5m])
```
**Panel Type:** Graph
**Unit:** Percent (0-1)
**Legend:** `CPU utilization`

---

## Grafana Dashboard Import

Save these panels in a dashboard JSON and import via:
- Grafana UI → Dashboards → Import → Paste JSON

Or use the Grafana HTTP API:
```bash
curl -X POST http://localhost:3000/api/dashboards/db \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <api-token>" \
  -d @dashboard.json
```
