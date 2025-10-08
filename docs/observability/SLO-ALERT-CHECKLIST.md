# SLO ↔ Alert ↔ Dashboard Alignment Checklist

**Sprint 52 – Agent Orchestration (Phase 1)**
**Date:** October 7, 2025
**Purpose:** Verify alignment between Service Level Objectives, Prometheus alerts, and Grafana dashboard panels

---

## Core SLO Alignment Matrix

| SLO | Target | Window | Alert Name(s) | Dashboard Panel(s) | Status | Notes |
|-----|--------|--------|---------------|-------------------|--------|-------|
| **Light Endpoints p99 Latency** | ≤ 50ms | 30d | `LightEndpointLatencyHigh` | "Latency (p50/p95/p99) - Light Endpoints" | ✅ | Alert fires at >50ms for 5min. Panel shows threshold line at 50ms. |
| **Webhook Execute p95 Latency** | ≤ 1.2s | 30d | `WebhookExecuteLatencyHigh` | "Latency (p50/p95) - Webhook Execute" | ✅ | Alert fires at >1.2s for 5min. Panel shows p95 with SLO label. |
| **Error Rate** | ≤ 1% | 7d | `ActionsErrorRateHigh`, `HighErrorStreak` | "Error Rate (%)", "SLO Error Budget Remaining" | ✅ | Two alerts: sustained high rate + error streaks. Two panels: real-time + error budget gauge. |
| **Availability** | ≥ 99.9% | 30d | `ServiceDown` | "Service Availability (Uptime %)" | ✅ | Alert fires when `up` metric = 0. Panel shows 30d average with color thresholds. |

---

## Supporting Observability Components

### Alerts (Not Directly SLO-Mapped)

| Alert Name | Purpose | Severity | Mapped to SLO? |
|------------|---------|----------|----------------|
| `RateLimitBreaches` | Detect excessive 429 responses | `info` | ❌ Supporting metric |
| `DatabaseConnectionPoolExhausted` | Detect DB connection exhaustion | `warning` | ❌ Infrastructure reliability |
| `RedisDown` | Detect Redis (rate limiter) outage | `warning` | ❌ Infrastructure reliability |

**Notes:**
- These alerts are **operational signals** that may impact SLOs but are not direct SLO thresholds.
- `RateLimitBreaches` → May cause user-perceived errors if legitimate traffic is rate-limited.
- `DatabaseConnectionPoolExhausted` → Will cause 500 errors, impacting Error Rate SLO.
- `RedisDown` → Falls back to in-process rate limiter, no direct SLO impact.

### Dashboard Panels (Not Directly SLO-Mapped)

| Panel Title | Purpose | Mapped to SLO? |
|-------------|---------|----------------|
| "Request Rate (RPM)" | Traffic volume monitoring | ❌ Golden signal (traffic) |
| "Rate Limit Hits (429s)" | Rate limiting effectiveness | ❌ Supporting metric |
| "Total Requests (24h)" | Daily volume summary | ❌ Supporting metric |

**Notes:**
- These panels provide **context** for SLO interpretation (e.g., high error rate under low traffic vs. high traffic).
- "Request Rate (RPM)" is the Traffic golden signal (TELS: Traffic, Errors, Latency, Saturation).

---

## Verification Checklist

### SLO Definitions (docs/observability/SLOs.md)

- [x] **SLO 1:** Light Endpoints p99 ≤ 50ms (30-day window)
- [x] **SLO 2:** Webhook Execute p95 ≤ 1.2s (30-day window)
- [x] **SLO 3:** Error Rate ≤ 1% (7-day window)
- [x] **SLO 4:** Availability ≥ 99.9% (monthly)

### Prometheus Alerts (observability/dashboards/alerts.json)

- [x] **SLO 1 → Alert:** `LightEndpointLatencyHigh` (severity: `warning`, for: `5m`)
- [x] **SLO 2 → Alert:** `WebhookExecuteLatencyHigh` (severity: `warning`, for: `5m`)
- [x] **SLO 3 → Alerts:** `ActionsErrorRateHigh` (severity: `critical`, for: `5m`) + `HighErrorStreak` (severity: `page`, for: `2m`)
- [x] **SLO 4 → Alert:** `ServiceDown` (severity: `page`, for: `1m`)
- [x] **Supporting Alerts:** `RateLimitBreaches`, `DatabaseConnectionPoolExhausted`, `RedisDown`

### Grafana Dashboard (observability/dashboards/golden-signals.json)

- [x] **SLO 1 → Panel:** "Latency (p50/p95/p99) - Light Endpoints" (id: 3, threshold: 50ms)
- [x] **SLO 2 → Panel:** "Latency (p50/p95) - Webhook Execute" (id: 4, threshold: 1.2s)
- [x] **SLO 3 → Panels:** "Error Rate (%)" (id: 2, threshold: 1%) + "SLO Error Budget Remaining" (id: 6, gauge)
- [x] **SLO 4 → Panel:** "Service Availability (Uptime %)" (id: 7, threshold: 99.9%)
- [x] **Supporting Panels:** "Request Rate (RPM)", "Rate Limit Hits (429s)", "Total Requests (24h)"
- [x] **Annotations:** Firing alerts displayed on dashboard timeline

---

## Gaps & Recommendations

### ✅ No Critical Gaps Identified

All 4 core SLOs have:
1. ✅ Clear definition in SLOs.md with PromQL queries
2. ✅ Corresponding Prometheus alert(s) with appropriate severity
3. ✅ Grafana dashboard panel(s) with visual thresholds
4. ✅ Alert annotations displayed on dashboard

### 🟡 Minor Enhancements (Optional)

**1. Error Rate SLO: Dual Time Windows**
- **Current:** SLO uses 7-day window, alert uses 5-minute window
- **Recommendation:** Add a second alert for 7-day trend to match SLO evaluation period
- **Impact:** Low (5min alert is sufficient for immediate response)

**2. Dashboard Panel Consistency**
- **Current:** SLO 3 has two panels (real-time error rate + 7-day error budget)
- **Recommendation:** Consider adding similar budget gauges for latency SLOs
- **Impact:** Low (latency thresholds are easier to visualize on time-series graphs)

**3. Alert Runbook Documentation**
- **Current:** Alert names are descriptive but lack runbook links
- **Recommendation:** Add `runbook_url` annotation to each alert in alerts.json
- **Impact:** Medium (improves on-call response time)

---

## Sign-Off

**Alignment Status:** ✅ **COMPLETE**

All 4 core SLOs are properly instrumented with alerts and dashboard visualizations. The observability stack is ready for production monitoring.

**Validated By:** Sprint 52 Agent Orchestration (Phase 1)
**Date:** October 7, 2025
**Next Action:** Import alerts and dashboard to production (see IMPORT-CHECKLIST.md)
