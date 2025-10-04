# Connector Observability & Resilience

**Version:** 1.0 (Sprint 34C)
**Status:** ✅ Production Ready

---

## Overview

Sprint 34C adds production-grade observability and resilience to the Connector Framework:
- **Metrics & Health**: Record operations, compute health status based on thresholds
- **OAuth2 Token Store**: CI-safe local token storage with refresh detection
- **Retry Logic**: Exponential backoff with jitter
- **Circuit Breaker**: Prevent cascading failures with closed/open/half-open states

---

## Metrics & Health

### Recording Metrics

```python
from src.connectors.metrics import record_call

# Record operation
record_call(
    connector_id="outlook",
    operation="list_resources",
    status="success",
    duration_ms=125.5,
    error=None
)
```

### Health Status

```python
from src.connectors.metrics import health_status

health = health_status("outlook", window_minutes=60)
# {
#   "status": "healthy" | "degraded" | "down" | "unknown",
#   "reason": "...",
#   "metrics": {
#     "total_calls": 150,
#     "error_rate": 0.02,
#     "p50_ms": 100.0,
#     "p95_ms": 250.0,
#     "p99_ms": 500.0
#   }
# }
```

### Health Thresholds

| Environment Variable | Default | Description |
|---------------------|---------|-------------|
| `CONNECTOR_HEALTH_P95_MS` | `2000` | p95 latency threshold (ms) |
| `CONNECTOR_HEALTH_ERROR_RATE` | `0.10` | Error rate threshold (0.0-1.0) |

**Health States:**
- `healthy` - All metrics within thresholds
- `degraded` - One or more thresholds exceeded, error rate < 50%
- `down` - Error rate > 50%
- `unknown` - No metrics available

---

## OAuth2 Token Store

### Saving Tokens

```python
from src.connectors.oauth2 import save_token

save_token(
    connector_id="outlook",
    access_token="ya29.a0...",
    refresh_token="1//0g...",
    expires_at="2025-10-05T12:00:00"
)
```

### Loading & Refresh

```python
from src.connectors.oauth2 import load_token, needs_refresh

token = load_token("outlook")
if token and needs_refresh(token):
    # Refresh token before expiry
    # (refresh_token implementation TBD)
    pass
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `OAUTH_TOKEN_PATH` | `logs/connectors/tokens.jsonl` | Token storage path |
| `OAUTH_REFRESH_SAFETY_WINDOW_S` | `300` | Refresh N seconds before expiry |
| `OAUTH2_REQUIRED` | `false` | Require OAuth2 for mock connectors |

---

## Retry Logic

### Exponential Backoff

```python
from src.connectors.retry import compute_backoff_ms

delay = compute_backoff_ms(attempt=2)
# Returns: ~1600ms (400 * 2^2 ± jitter)
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `RETRY_MAX_ATTEMPTS` | `3` | Maximum retry attempts |
| `RETRY_BASE_MS` | `400` | Base delay in milliseconds |
| `RETRY_CAP_MS` | `60000` | Maximum delay cap (1 minute) |
| `RETRY_JITTER_PCT` | `0.2` | Jitter percentage (±20%) |

**Formula:** `delay = min(base_ms * 2^attempt ± jitter, cap_ms)`

---

## Circuit Breaker

### States

- **Closed** (normal): All requests allowed
- **Open** (failing): No requests allowed until cooldown expires
- **Half-Open** (testing): Probabilistic requests allowed to test recovery

### Usage

```python
from src.connectors.circuit import CircuitBreaker

cb = CircuitBreaker("outlook")

if cb.allow():
    try:
        # Perform operation
        result = connector.list_resources("messages")
        cb.record_success()
    except Exception:
        cb.record_failure()
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CB_FAILURES_TO_OPEN` | `5` | Failures before opening circuit |
| `CB_COOLDOWN_S` | `60` | Cooldown before half-open (seconds) |
| `CB_HALF_OPEN_PROB` | `0.2` | Probability of allowing half-open requests |

---

## Best Practices

### 1. Monitor Health Regularly

```python
# Check health before critical operations
health = health_status("outlook")
if health["status"] == "down":
    # Fallback or alert
    pass
```

### 2. Tune Retry Parameters

- **Fast operations** (< 100ms): Lower base delay (`RETRY_BASE_MS=100`)
- **Slow operations** (> 1s): Higher base delay (`RETRY_BASE_MS=1000`)
- **External APIs**: Always use jitter to prevent thundering herd

### 3. Circuit Breaker Thresholds

- **High traffic**: Lower `CB_FAILURES_TO_OPEN` (e.g., 3)
- **Low traffic**: Higher threshold (e.g., 10)
- **Critical systems**: Longer cooldown (`CB_COOLDOWN_S=300`)

### 4. OAuth2 Token Management

- Always check `needs_refresh()` before operations
- Store refresh tokens securely (not in git)
- Use safety window to avoid mid-operation expiry

---

## Troubleshooting

### High Error Rate

1. Check metrics: `summarize("connector_id")`
2. Review recent failures in metrics JSONL
3. Verify external system status
4. Check circuit breaker state

### Circuit Stuck Open

1. Verify cooldown period elapsed
2. Check if half-open requests succeeding
3. Manually reset circuit (delete state entry)

### Token Refresh Failures

1. Verify refresh token validity
2. Check OAuth provider status
3. Ensure `OAUTH_REFRESH_SAFETY_WINDOW_S` appropriate
4. Implement refresh_token() for provider

---

## Dashboard & CLI (Sprint 35A)

### Observability Dashboard

The **Connectors** panel in the observability dashboard (`dashboards/observability_tab.py`) displays:

- **Connector Status**: Lists all enabled connectors with health icon (✅/⚠️/🚨/❓)
- **P95 Latency**: 95th percentile latency over last 60 minutes
- **Error Rate**: Percentage of failed operations
- **Calls (60m)**: Total operations in last hour
- **Circuit State**: Circuit breaker status (🟢 closed / 🔴 open / 🟡 half-open)

**Empty States:**
- No connectors: Shows registration instructions and link to SDK docs
- No metrics: Displays "N/A" for metrics until operations recorded

### Health CLI

**Location:** `scripts/connectors_health.py`

#### List Command

Show brief status for all connectors:

```bash
# Text output (default)
python scripts/connectors_health.py list

# JSON output
python scripts/connectors_health.py list --json
```

**Example Output:**
```
Connector                 Health       P95 (ms)   Error %    Calls (60m)  Circuit
------------------------------------------------------------------------------------------
outlook                   ✅ healthy   245        0.5        1523         🟢 closed
slack                     ⚠️ degraded  3200       2.1        842          🟢 closed
teams                     🚨 down      5100       65.3       234          🔴 open
```

#### Drill Command

Show detailed status for specific connector:

```bash
# Text output
python scripts/connectors_health.py drill outlook

# JSON output
python scripts/connectors_health.py drill outlook --json
```

**Example Output:**
```
Connector: outlook
Health: degraded
Reason: p95 latency 2450ms exceeds 2000ms

Metrics (Last 60 Minutes):
  Total Calls: 1523
  Error Rate: 0.5%
  P50 Latency: 150ms
  P95 Latency: 2450ms
  P99 Latency: 4200ms

Circuit State: closed

Recent Failures (Last 5):
  - 2025-10-04T14:23:15: list_resources - Timeout after 5000ms
  - 2025-10-04T14:18:42: connect - Authentication failed
```

#### Exit Codes

| Code | Meaning | Description |
|------|---------|-------------|
| `0` | Success | All connectors healthy |
| `1` | Degraded/Down | One or more connectors degraded or down |
| `2` | RBAC Denied | Insufficient permissions (requires Operator role) |
| `3` | Error/Not Found | Connector not found, invalid arguments, or system error |

**RBAC Check:**
```bash
# Set USER_ROLE environment variable
export USER_ROLE=Operator  # Required: Admin, Deployer, or Operator
python scripts/connectors_health.py list
```

---

## See Also

- `docs/CONNECTOR_SDK.md` - Base connector interface
- `docs/CONNECTORS.md` - Connector framework overview
- `docs/OPERATIONS.md` - Operational runbooks
