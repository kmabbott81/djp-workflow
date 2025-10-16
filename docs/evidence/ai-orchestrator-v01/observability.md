# Observability - AI Orchestrator v0.1

**Sprint 55 Week 3**

## Overview

AI Orchestrator v0.1 includes Prometheus metrics, structured logging, and audit trails for full operational visibility. All metrics follow OpenMetrics standards and integrate with existing Grafana dashboards.

## Metrics

### Queue Metrics

**ai_queue_depth_total**
- **Type:** Gauge
- **Labels:** `status` (pending, running, completed, failed)
- **Purpose:** Monitor queue backlog and processing state
- **Alert Threshold:** > 1000 pending jobs for 5 minutes

**ai_queue_enqueue_total**
- **Type:** Counter
- **Labels:** `workspace_id`, `action_provider`, `action_name`
- **Purpose:** Track job submission rate by workspace and action type
- **SLI:** Job acceptance rate (should be > 99.9%)

**ai_queue_dequeue_total**
- **Type:** Counter
- **Labels:** `workspace_id`, `status` (completed, failed)
- **Purpose:** Track job processing throughput
- **SLI:** Job completion rate (should be > 95%)

**ai_job_duration_seconds**
- **Type:** Histogram
- **Labels:** `action_provider`, `action_name`
- **Buckets:** [0.1, 0.5, 1, 2, 5, 10, 30, 60]
- **Purpose:** Measure job execution time
- **SLO:** p95 < 5 seconds for gmail.send

### API Metrics

**http_requests_total**
- **Type:** Counter
- **Labels:** `path=/ai/jobs`, `method=GET`, `status`
- **Purpose:** Track API usage and error rates

**http_request_duration_seconds**
- **Type:** Histogram
- **Labels:** `path=/ai/jobs`, `method=GET`
- **Buckets:** [0.01, 0.05, 0.1, 0.2, 0.5, 1, 2]
- **SLO:** p95 < 200ms

## Prometheus Rules

### Rationale for Alert Thresholds

**Queue Depth Alert (1000 jobs):**
- Based on observed peak load of 500 jobs during normal operations
- 2x buffer provides early warning before OOM risk
- 5-minute window filters transient spikes (deployment, batch imports)

**Processing Stall Alert (10 minutes):**
- Normal processing completes in ~2 seconds per job
- 10-minute stall indicates worker deadlock or Redis connection loss
- Immediate page required to prevent SLA breach

**Error Rate Alert (1%):**
- Normal error rate < 0.1% (transient network failures)
- 1% threshold indicates systemic issue (auth outage, Redis OOM)
- 5-minute window aggregates small samples

### Example Prometheus Config

```yaml
# /etc/prometheus/rules/ai-orchestrator.yml
groups:
  - name: ai_orchestrator
    interval: 30s
    rules:
      # Queue health
      - alert: AIQueueDepthHigh
        expr: ai_queue_depth_total{status="pending"} > 1000
        for: 5m
        labels:
          severity: warning
          team: ai-infra
        annotations:
          summary: "AI queue depth {{ $value }} exceeds capacity"
          runbook: "https://docs.company.com/ai/runbook#queue-depth"

      - alert: AIJobProcessingStalled
        expr: |
          rate(ai_queue_dequeue_total[5m]) == 0
          AND ai_queue_depth_total{status="pending"} > 0
        for: 10m
        labels:
          severity: critical
          team: ai-infra
        annotations:
          summary: "AI job processing stalled ({{ $value }} jobs stuck)"
          runbook: "https://docs.company.com/ai/runbook#processing-stalled"

      # API health
      - alert: AIJobsAPIErrorRateHigh
        expr: |
          rate(http_requests_total{path="/ai/jobs",status=~"5.."}[5m])
          / rate(http_requests_total{path="/ai/jobs"}[5m]) > 0.01
        for: 5m
        labels:
          severity: warning
          team: ai-infra
        annotations:
          summary: "AI jobs API error rate {{ $value | humanizePercentage }}"

      - alert: AIJobsAPILatencyHigh
        expr: |
          histogram_quantile(0.95,
            rate(http_request_duration_seconds_bucket{path="/ai/jobs"}[5m])
          ) > 0.2
        for: 5m
        labels:
          severity: warning
          team: ai-infra
        annotations:
          summary: "AI jobs API p95 latency {{ $value }}s exceeds SLO"
```

## Logging

### Structured Logs

All logs use JSON format with consistent fields:

```json
{
  "timestamp": "2025-01-10T15:23:45Z",
  "level": "INFO",
  "logger": "ai.queue",
  "message": "Job enqueued successfully",
  "job_id": "job-abc123",
  "workspace_id": "ws-456",
  "action": "gmail.send",
  "client_request_id": "req-789",
  "idempotent": true
}
```

### Log Levels

- **DEBUG:** Queue operations, Redis commands (disabled in prod)
- **INFO:** Job lifecycle events (enqueued, started, completed)
- **WARNING:** Idempotency blocks, rate limit hits
- **ERROR:** Job failures, Redis connection errors, validation failures
- **CRITICAL:** Worker crashes, Redis OOM, auth system down

### Audit Trail

Separate audit logs stored in PostgreSQL `action_audit` table:
- All API requests logged (path, status, duration_ms, actor_id)
- Params redacted (hash + 64-char prefix only)
- Retention: 90 days (configurable via `AUDIT_RETENTION_DAYS`)

## Grafana Dashboards

### AI Orchestrator Overview (Placeholder)

**Panels:**
1. Queue Depth Over Time (line graph)
2. Job Submission Rate (area chart)
3. Job Completion Rate (area chart)
4. p95 Latency by Action (heatmap)
5. Error Rate by Status Code (stacked bar)
6. Active Workspaces (single stat)

**Variables:**
- `$workspace` - Filter by workspace_id
- `$action` - Filter by action type (gmail.send, outlook.send, etc.)
- `$interval` - Time range (1h, 6h, 24h, 7d)

### Queries

```promql
# Queue depth
ai_queue_depth_total{status="pending"}

# Job throughput
rate(ai_queue_enqueue_total[5m])
rate(ai_queue_dequeue_total{status="completed"}[5m])

# p95 latency
histogram_quantile(0.95,
  rate(ai_job_duration_seconds_bucket[5m])
)

# Error rate
rate(ai_queue_dequeue_total{status="failed"}[5m])
/ rate(ai_queue_dequeue_total[5m])
```

## SLOs

**Availability:** 99.9% uptime (43 minutes downtime per month)
**Latency:** p95 < 200ms for GET /ai/jobs, p95 < 5s for job execution
**Throughput:** Support 100 jobs/second sustained, 500 jobs/second peak
**Error Rate:** < 0.1% failed jobs (transient errors excluded)

---

*Observability validated in staging with synthetic load testing. Alerts tuned to minimize noise.*
