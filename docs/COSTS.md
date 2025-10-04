# Cost Governance & Budget Guardrails (Sprint 30)

## Overview

Sprint 30 introduces production-grade cost governance and budget enforcement on top of Sprint 25's cost telemetry. The system provides:

- **Per-tenant and global budgets** with daily/monthly limits
- **Dual-threshold enforcement**: soft (throttle) and hard (deny)
- **Statistical anomaly detection** using rolling baselines
- **Governance event logging** for auditing and alerting
- **Dashboard integration** for real-time budget monitoring
- **CLI reporting tool** for cost analysis

## Architecture

### Components

```
src/cost/
├── ledger.py       # Load and aggregate cost events from Sprint 25
├── budgets.py      # Budget configuration (env + YAML)
├── enforcer.py     # Budget enforcement with soft/hard thresholds
├── anomaly.py      # Statistical anomaly detection
└── alerts.py       # Alert emission (console + governance log)

scripts/
└── cost_report.py  # CLI tool for cost reporting

dashboards/
└── observability_tab.py  # Cost governance dashboard panel
```

### Data Flow

```
Sprint 25 Cost Telemetry
       ↓
logs/cost_events.jsonl
       ↓
cost/ledger.py (load & aggregate)
       ↓
┌──────────────┬──────────────┐
│              │              │
enforcer.py   anomaly.py   budgets.py
│              │              │
└──────────────┴──────────────┘
       ↓
logs/governance_events.jsonl
       ↓
Dashboard & Alerts
```

## Configuration

### Environment Variables

#### Global Budgets
```bash
GLOBAL_BUDGET_DAILY=25.0          # Global daily budget (default: $25)
GLOBAL_BUDGET_MONTHLY=500.0       # Global monthly budget (default: $500)
```

#### Tenant Budgets
```bash
TENANT_BUDGET_DAILY_DEFAULT=5.0   # Default daily budget per tenant (default: $5)
TENANT_BUDGET_MONTHLY_DEFAULT=100.0  # Default monthly budget per tenant (default: $100)
```

#### Enforcement Thresholds
```bash
BUDGET_SOFT_THRESHOLD=0.8         # Soft threshold for throttling (default: 0.8 = 80%)
BUDGET_HARD_THRESHOLD=1.0         # Hard threshold for denial (default: 1.0 = 100%)
```

#### Anomaly Detection
```bash
ANOMALY_SIGMA=3.0                 # Sigma threshold for anomaly detection (default: 3.0)
ANOMALY_MIN_DOLLARS=3.0           # Minimum spend to flag anomaly (default: $3)
ANOMALY_MIN_EVENTS=10             # Minimum events for baseline (default: 10)
```

#### File Paths
```bash
COST_EVENTS_PATH=logs/cost_events.jsonl  # Cost events from Sprint 25
GOVERNANCE_EVENTS_PATH=logs/governance_events.jsonl  # Governance events
BUDGETS_PATH=config/budgets.yaml  # Optional YAML budget overrides
```

### YAML Configuration (Optional)

For per-tenant budget customization, create `config/budgets.yaml`:

```yaml
global:
  daily: 100.0
  monthly: 2000.0

tenants:
  premium-tenant:
    daily: 20.0
    monthly: 400.0

  trial-tenant:
    daily: 1.0
    monthly: 10.0

  enterprise-tenant:
    daily: 50.0
    monthly: 1000.0
```

YAML overrides take precedence over environment variables.

## Budget Enforcement

### Dual-Threshold System

The enforcer provides two levels of control:

1. **Soft Threshold (Throttle)**: At 80% of budget (configurable via `BUDGET_SOFT_THRESHOLD`)
   - Emit governance event (`budget_throttle`)
   - Return warning message
   - Allow execution to continue (with rate limiting integration from Sprint 29)

2. **Hard Threshold (Deny)**: At 100% of budget (configurable via `BUDGET_HARD_THRESHOLD`)
   - Emit governance event (`budget_deny`)
   - Raise `BudgetExceededError`
   - Reject execution (send to DLQ from Sprint 29)

### Usage

```python
from src.cost.enforcer import should_deny, should_throttle, BudgetExceededError

# Check before executing workflow
deny, reason = should_deny(tenant="tenant-1")
if deny:
    raise BudgetExceededError(reason)

throttle, reason = should_throttle(tenant="tenant-1")
if throttle:
    # Apply rate limiting or warn user
    logger.warning(reason)
```

### Integration Points

#### OpenAI Adapter (Sprint 25)
Add budget check before API calls:

```python
from src.cost.enforcer import should_deny, BudgetExceededError

async def call_openai_api(tenant: str, ...):
    # Check budget before making API call
    deny, reason = should_deny(tenant)
    if deny:
        raise BudgetExceededError(reason)

    # Proceed with API call
    response = await openai.chat.completions.create(...)

    # Log cost event (existing Sprint 25 logic)
    emit_cost_event(tenant, response.usage, ...)
```

#### Worker (Sprint 28/29)
Add budget check in job execution:

```python
from src.cost.enforcer import should_deny, BudgetExceededError

async def execute_job(job: Job):
    try:
        # Check budget before execution
        deny, reason = should_deny(job.tenant)
        if deny:
            # Send to DLQ with budget_exceeded reason
            await dlq_send(job, reason="budget_exceeded", details=reason)
            return

        # Execute job
        await run_workflow(job)

    except BudgetExceededError as e:
        # Send to DLQ on budget errors
        await dlq_send(job, reason="budget_exceeded", details=str(e))
```

## Anomaly Detection

### Algorithm

Uses simple statistical baseline for deterministic, testable anomaly detection:

1. **Compute Baseline**: Calculate mean and std_dev of daily spend for last 7 days
2. **Detect Anomalies**: Flag if today's spend > baseline_mean + (sigma * std_dev)
3. **Thresholds**:
   - Must exceed `ANOMALY_SIGMA` standard deviations (default: 3σ)
   - Must exceed `ANOMALY_MIN_DOLLARS` absolute threshold (default: $3)
   - Must have `ANOMALY_MIN_EVENTS` baseline events (default: 10)

### Usage

```python
from src.cost.anomaly import detect_anomalies

# Detect anomalies for all tenants
anomalies = detect_anomalies()

# Detect anomalies for specific tenant
anomalies = detect_anomalies(tenant="tenant-1")

for anom in anomalies:
    print(f"Tenant {anom['tenant']} today: ${anom['today_spend']:.2f}")
    print(f"Baseline: ${anom['baseline_mean']:.2f} (σ={anom['baseline_std_dev']:.2f})")
    print(f"Threshold: ${anom['threshold']:.2f} ({anom['sigma']}σ)")
```

### Governance Events

Anomalies emit `cost_anomaly` governance events:

```json
{
  "event": "cost_anomaly",
  "tenant": "tenant-1",
  "today_spend": 50.0,
  "baseline_mean": 5.0,
  "threshold": 11.0,
  "sigma": 3.0,
  "timestamp": "2025-10-03T12:00:00Z"
}
```

## Cost Reporting

### CLI Tool

The `scripts/cost_report.py` CLI provides text and JSON output modes:

```bash
# Global report (last 30 days)
python scripts/cost_report.py

# Tenant-specific report
python scripts/cost_report.py --tenant tenant-1

# Custom time window
python scripts/cost_report.py --days 7

# JSON output for programmatic consumption
python scripts/cost_report.py --json > report.json
```

### Text Output

```
=== Cost Report (Last 30 Days) ===

Global Spend:
  Daily:   $8.45
  Monthly: $234.67

Per-Tenant Spend:
Tenant               Daily       Monthly  Budget Status
-----------------------------------------------------------------
tenant-1             $5.23       $156.78  ✅
tenant-2             $2.45       $67.89   ✅
tenant-3             $0.77       $10.00   🚨

=== Cost Anomalies ===

Tenant: tenant-3
  Today:    $10.00
  Baseline: $2.00 (σ=0.50)
  Threshold: $3.50 (3σ)
```

### JSON Output

```json
{
  "window_days": 30,
  "tenant_filter": null,
  "global": {
    "daily": 8.45,
    "monthly": 234.67
  },
  "tenants": [
    {
      "tenant": "tenant-1",
      "daily_spend": 5.23,
      "monthly_spend": 156.78,
      "budget": {"daily": 5.0, "monthly": 100.0},
      "over_budget": {"daily": true, "monthly": true}
    }
  ],
  "anomalies": [
    {
      "tenant": "tenant-3",
      "today_spend": 10.0,
      "baseline_mean": 2.0,
      "baseline_std_dev": 0.5,
      "threshold": 3.5,
      "sigma": 3.0
    }
  ]
}
```

## Dashboard Integration

The observability dashboard includes a new **Cost Governance** panel showing:

1. **Global Budget Status**: Daily/monthly spend vs budgets with percentage indicators
2. **Top Tenants by Spend**: Daily/monthly breakdown with budget status icons (✅/🚨)
3. **Cost Anomalies**: Tenants with anomalous spend today
4. **Recent Governance Events**: Budget throttle/deny events and anomaly detections

Access the dashboard:
```bash
streamlit run dashboards/app.py
```

Navigate to the **Observability** tab to view cost governance metrics.

## Governance Events

All enforcement and anomaly events are logged to `logs/governance_events.jsonl` for auditing.

### Event Types

#### budget_throttle
```json
{
  "event": "budget_throttle",
  "tenant": "tenant-1",
  "reason": "daily_budget_approaching",
  "daily_spend": 8.5,
  "daily_budget": 10.0,
  "threshold": 0.8,
  "timestamp": "2025-10-03T12:00:00Z"
}
```

#### budget_deny
```json
{
  "event": "budget_deny",
  "tenant": "tenant-1",
  "reason": "daily_budget_exceeded",
  "daily_spend": 15.0,
  "daily_budget": 10.0,
  "timestamp": "2025-10-03T12:00:00Z"
}
```

#### cost_anomaly
```json
{
  "event": "cost_anomaly",
  "tenant": "tenant-1",
  "today_spend": 50.0,
  "baseline_mean": 5.0,
  "threshold": 11.0,
  "sigma": 3.0,
  "timestamp": "2025-10-03T12:00:00Z"
}
```

#### alert
```json
{
  "event": "alert",
  "kind": "budget_exceeded",
  "tenant": "tenant-1",
  "message": "Daily budget exceeded",
  "severity": "critical",
  "timestamp": "2025-10-03T12:00:00Z"
}
```

## Testing

Sprint 30 includes comprehensive test coverage:

```bash
# Run all cost governance tests
pytest tests/test_cost_ledger.py -v
pytest tests/test_budgets.py -v
pytest tests/test_enforcer.py -v
pytest tests/test_anomaly.py -v
pytest tests/test_cost_report_cli.py -v

# Run all tests
pytest tests/ -v
```

### Test Coverage

- `test_cost_ledger.py`: Event loading, rollups, window sums
- `test_budgets.py`: Env/YAML config, tenant vs global budgets
- `test_enforcer.py`: Soft/hard thresholds, governance event emission
- `test_anomaly.py`: Baseline calculation, sigma thresholding
- `test_cost_report_cli.py`: Text/JSON output modes

## Operational Considerations

### Budget Breach Runbook

When a tenant exceeds their budget:

1. **Immediate**: Jobs are denied and sent to DLQ (if integrated with worker)
2. **Alert**: Governance event logged and dashboard updated
3. **Investigation**: Use cost report CLI to analyze spend patterns
4. **Resolution Options**:
   - Increase tenant budget in `config/budgets.yaml`
   - Review and optimize workflow costs
   - Contact tenant about usage
5. **Recovery**: Replay DLQ jobs after budget reset

### DLQ Replay After Budget Reset

```bash
# Reset monthly budget (first of month)
# Edit config/budgets.yaml to increase limits

# Replay DLQ jobs from previous period
python scripts/dlq_replay.py --reason budget_exceeded --tenant tenant-1
```

### Monitoring Recommendations

1. **Daily**: Review dashboard for budget status and anomalies
2. **Weekly**: Run cost report CLI to analyze trends
3. **Monthly**: Reset budgets and review governance events
4. **Alerts**: Configure external alerts for budget_deny events

### Cost Optimization

If global or tenant budgets are consistently exceeded:

1. **Analyze Spend**: `python scripts/cost_report.py --json > report.json`
2. **Identify High-Cost Workflows**: Check "Cost by Workflow" section
3. **Optimize Prompts**: Reduce token usage in high-cost workflows
4. **Model Selection**: Use cheaper models for non-critical workflows
5. **Caching**: Implement caching layer for repeated queries (Sprint 31+)

## Security Considerations

### RBAC for Budget Editing

Restrict access to budget configuration:

- **config/budgets.yaml**: Read-only for workers, writable only by admins
- **Environment variables**: Set at deployment time, not runtime
- **Governance events**: Append-only log for audit trail

### Governance Event Auditing

All budget enforcement decisions are logged for compliance:

- Track who exceeded budgets and when
- Audit budget increase requests
- Detect potential abuse or misconfiguration

## Future Enhancements

Potential Sprint 31+ improvements:

1. **Email/Teams Alerts**: Integrate with external notification systems
2. **Predictive Budgets**: Forecast month-end spend based on current trends
3. **Cost Attribution**: Track costs by workflow type, user, or feature
4. **Budget Rollover**: Allow unused budget to carry over between periods
5. **Rate Limiting Integration**: Automatic throttling when approaching budgets
6. **Cost Optimization Suggestions**: AI-powered recommendations for reducing spend

## References

- Sprint 25: Cost Telemetry (logs/cost_events.jsonl)
- Sprint 28/29: Worker & DLQ (job rejection on budget exceeded)
- OPERATIONS.md: Runbooks for budget breach scenarios
- SECURITY.md: RBAC policies for budget configuration
