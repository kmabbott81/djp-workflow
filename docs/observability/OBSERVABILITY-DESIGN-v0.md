# Observability Design (v0) — OTel vs Prom vs Hybrid

## Objectives
- Add production-grade telemetry **without** changing core behavior
- Keep costs predictable; preserve privacy and least-privilege data handling
- Preserve the clean seam added in Sprint 42 (TELEMETRY_ENABLED + noop stub)

## Candidate Architectures

### Option A — OpenTelemetry (OTel) end-to-end
**Architecture**: Traces, metrics, logs via OTel SDK + Collector

**Pros**:
- Vendor-agnostic, rich context propagation across services
- Unified instrumentation for traces/metrics/logs
- Strong ecosystem (exporters for Jaeger, Tempo, Datadog, etc.)
- Native distributed tracing with automatic context injection

**Cons**:
- Complexity: OTel Collector setup + configuration
- Operational overhead: Collector deployment, scaling, monitoring
- Learning curve for full stack
- More moving parts (SDK + Collector + backend)

### Option B — Prometheus-first (metrics) + existing logs
**Architecture**: Exporter → Prom scrape → Alertmanager; logs stay in app logger sink

**Pros**:
- Simple, battle-tested, ops-friendly
- Lower cost (local storage + aggregation)
- Easy SLI/SLO dashboards (Grafana integration)
- Well-understood operational model

**Cons**:
- Weak tracing support (no native distributed traces)
- Limited cross-hop context (no trace correlation)
- Metrics-only; logs stay separate
- Missing request-level observability

### Option C — Hybrid (OTel traces/logs + Prom metrics)
**Architecture**: OTel SDK for traces/logs, Prom for SLI/SLO metrics via exporter

**Pros**:
- Best of both worlds: distributed tracing + proven metrics
- Gradual migration path (start with Prom, add OTel later)
- Cost optimization (Prom for high-cardinality metrics)
- Flexible: can swap backends without code changes

**Cons**:
- Two moving parts to maintain
- Requires careful label cardinality management
- Dual instrumentation overhead (though minimal)
- Potential for metric/trace correlation gaps

## Data Model (MVP)

### Resource Attributes
- `app=djp-workflow`
- `service=(web|worker|scheduler)`
- `env=(dev|staging|prod)`
- `version=<git-sha>`
- `tenant_id=<hashed-tenant-id>` (optional, for multi-tenant analysis)

### Metrics (SLIs)
**Request-level**:
- `http_request_duration_seconds` (histogram) - API endpoint latency
- `http_requests_total` (counter) - Request count by status code
- `http_request_size_bytes` (histogram) - Request payload size

**Queue/Worker**:
- `queue_job_latency_seconds` (histogram) - Job processing time
- `queue_depth_total` (gauge) - Current queue depth
- `queue_job_failures_total` (counter) - Failed jobs by error type

**External APIs**:
- `external_api_calls_total` (counter) - Calls by service (Outlook/Teams/Slack/etc.)
- `external_api_duration_seconds` (histogram) - External API latency
- `external_api_errors_total` (counter) - Errors by service + status code

**Cost Tracking**:
- `token_cost_usd` (gauge or counter) - Token costs by model + tenant
- `workflow_cost_usd` (counter) - Workflow execution cost

### Traces
**Critical Flows** (MVP scope):
- Span: `/api/*` HTTP handlers
- Span: Batch runner tasks
- Span: External API edges (connectors)
- Span: Workflow execution (debate → judge → publish)

**Attributes**:
- `http.method`, `http.route`, `http.status_code`
- `workflow.name`, `workflow.id`
- `tenant.id` (hashed)
- `error=true` (for failed spans)

### Logs
- Keep existing structured logs (`src/telemetry/noop.py` placeholder)
- Add `trace_id` correlation field when OTel traces enabled
- Redact PII at source (no email content, just metadata counts)

## Privacy & PII Posture

### Default Privacy Stance
- **No payloads**: Metadata only (counts, durations, status codes)
- **No content**: Never log email bodies, chat messages, file contents
- **Hashed IDs**: User IDs, tenant IDs hashed before export
- **Configurable**: PII redaction enforced at SDK level

### Data Classification
- **Safe**: Request counts, durations, status codes, queue depth
- **Sensitive**: Tenant IDs (hash), user IDs (hash), workflow names
- **Prohibited**: Email content, chat messages, file contents, PII

### Export Controls
- Separate dev/staging/prod exporters with different retention policies
- Staging: 7-day retention, full sampling
- Prod: 30-day retention, sampled traces (1-5%)
- Dev: Local-only, no export

## Cost Controls

### Cardinality Management
- **Low-cardinality labels**: env, service, endpoint_group (not full path)
- **No user-specific labels**: Use tenant_id (hashed) aggregations
- **Bounded values**: Limit enum values (e.g., `http.status_code` → `2xx`, `4xx`, `5xx`)

### Sampling Strategy
**Traces**:
- Dev: 100% (local only)
- Staging: 100%
- Prod: 1-5% sample rate (head-based sampling)
- Always sample: Errors (100%), slow requests (>2s)

**Metrics**:
- Full for counters and gauges (low overhead)
- Histograms with narrow buckets (avoid label explosion)

**Logs**:
- INFO+ in prod (DEBUG in staging/dev)
- Rate limit per service (100/sec max)

### Retention Policies
- **Raw data**: 7-14 days
- **Aggregates**: 30-90 days
- **Alerting data**: Real-time + 24h lookback
- **Cost data**: 90 days (for budget analysis)

## Phased Rollout Plan

### Phase 0 (Current - Sprint 42) ✅
- Telemetry seam in place (`src/telemetry/noop.py`)
- `TELEMETRY_ENABLED` flag (default: false)
- No runtime impact

### Phase 1 (Metrics) - Sprint 46
- **Goal**: Prometheus exporter for SLI metrics
- **Deliverables**:
  - `src/telemetry/prom.py` - Prometheus exporter
  - HTTP `/metrics` endpoint (port 9090)
  - Grafana dashboard templates (latency, error rate, throughput)
- **Success Criteria**:
  - Metrics available in Grafana
  - No perf degradation (< 1ms overhead per request)
  - Zero runtime crashes

### Phase 2 (Traces) - Sprint 47
- **Goal**: OTel tracing for critical flows
- **Deliverables**:
  - `src/telemetry/otel.py` - OTel tracer
  - Span instrumentation for HTTP handlers, workflows, external APIs
  - Jaeger backend (staging) + Tempo (prod)
- **Success Criteria**:
  - End-to-end traces visible in Jaeger
  - Trace IDs in logs for correlation
  - < 2% perf overhead

### Phase 3 (Alerts) - Sprint 48
- **Goal**: SLO-based alerts
- **Deliverables**:
  - Alertmanager rules (latency p99, error rate, queue depth)
  - PagerDuty/Slack integration
  - Runbooks for common alerts
- **Success Criteria**:
  - Alerts fire on real incidents
  - No false positives (< 5% false alarm rate)
  - MTTD (Mean Time To Detect) < 5 minutes

### Phase 4 (Cost/Security) - Sprint 49
- **Goal**: Harden exporters, cost budgets, PII audits
- **Deliverables**:
  - Budget alarms for telemetry costs (CloudWatch/Datadog costs)
  - PII redaction audit (automated scan for leaks)
  - Security review + pen-test
- **Success Criteria**:
  - No PII leaks detected
  - Telemetry costs < $X/month target
  - Security audit pass

## Rollout & Safe Defaults

### Environment Flags
- `TELEMETRY_ENABLED=false` (default: disabled in all envs)
- `TELEMETRY_BACKEND=noop|prom|otel` (default: noop)
- `OTEL_EXPORTER_ENDPOINT=<collector-url>` (optional)
- `PROM_EXPORT_PORT=9090` (default)

### Dark Launch Strategy
1. **Phase 1**: Enable in staging with synthetic load (7 days)
2. **Phase 2**: Enable in prod for 5% of requests (canary)
3. **Phase 3**: Gradual rollout to 100% over 2 weeks
4. **Rollback**: Feature flag toggle (no deploys needed)

### Pre-Merge Validation
- Load tests with telemetry enabled (p99 latency < baseline + 2%)
- Memory profiling (no leaks, < 10MB overhead)
- Integration tests (metrics/traces exported correctly)

## Decision Record (Initial Recommendation)

**Recommendation**: **Option C - Hybrid (Prom metrics + OTel traces)**

**Rationale**:
- Leverage proven Prometheus for SLI dashboards (Phase 1)
- Add OTel tracing later for distributed context (Phase 2)
- Gradual migration path minimizes risk
- Cost-optimized (Prom local storage, OTel sampling)
- No vendor lock-in (can swap backends)

**Trade-offs Accepted**:
- Dual instrumentation (minimal overhead)
- Two systems to maintain (acceptable for ops team)
- Metric/trace correlation may require custom dashboards

**Next Sprint Decision Points**:
- After Phase 1 (metrics): Evaluate Prom exporter perf + ops overhead
- After Phase 2 (traces): Evaluate OTel collector stability + cost
- After Phase 3 (alerts): Decide on unified observability backend (Datadog/New Relic vs self-hosted)

## Next Steps

### Code Stubs (Sprint 46)
1. Draft `src/telemetry/prom.py` - Prometheus exporter interface (behind seam)
2. Draft `src/telemetry/otel.py` - OTel tracer init stub (no-op until Phase 2)
3. Update `src/telemetry/__init__.py` - Factory pattern for backend selection

### Documentation
1. Security review checklist - PII redaction, data classification
2. Runbook stubs - Metrics collection, alert response
3. Cost model - Estimated telemetry costs by environment

### Infrastructure (Deferred to Sprint 46)
- Prometheus server deployment (staging)
- Grafana dashboards (latency, errors, queue depth)
- OTel Collector (staging) - for Phase 2 prep

## References
- [src/telemetry/noop.py](../../src/telemetry/noop.py) - Current telemetry stub
- [OpenTelemetry Docs](https://opentelemetry.io/docs/)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)
- [Sprint 42](../perf/README.md) - Telemetry groundwork
