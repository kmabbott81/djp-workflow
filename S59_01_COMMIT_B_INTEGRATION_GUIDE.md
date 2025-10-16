# Sprint 59 S59-01 Commit B: Integration Guide
## workspace_id Label Wiring for Multi-Tenant Metrics

**Commit A Merge Date:** 2025-10-16
**Commit B Status:** Planning Phase
**Target Date:** Sprint 59 Week 2

This guide provides the integration plan for Commit B, which wires the workspace_id labels from Commit A into the orchestration system.

---

## ARCHITECTURE RECAP (Commit A)

**What Commit A provided:**
- `is_workspace_label_enabled()` - Check if feature flag is on
- `canonical_workspace_id(value)` - Validate and canonicalize workspace_id
- Updated function signatures: `record_queue_job(..., workspace_id=None)`, `record_action_execution(..., workspace_id=None)`
- 28 tests covering all validation paths
- Disabled by default (no production changes until flag is enabled)

**What Commit B must do:**
- Plumb workspace_id from context into metric recording calls
- Update Prometheus metric definitions to include workspace_id label
- Add integration tests verifying labels appear in output
- Canary test and monitoring plan

---

## INTEGRATION POINTS

### 1. ACTION EXECUTION RECORDING

**Current State (no workspace_id):**
```python
# src/actions/adapters/google.py - line ~290
async def execute(self, action: str, params: dict[str, Any], workspace_id: str, actor_id: str) -> dict[str, Any]:
    ...
    # Record metrics WITHOUT workspace_id
    record_action_execution(provider="google", action="gmail.send", status="ok", duration_seconds=duration)
```

**Commit B Changes:**
```python
# src/actions/adapters/google.py
async def execute(self, action: str, params: dict[str, Any], workspace_id: str, actor_id: str) -> dict[str, Any]:
    ...
    # Record metrics WITH workspace_id
    record_action_execution(
        provider="google",
        action="gmail.send",
        status="ok",
        duration_seconds=duration,
        workspace_id=workspace_id  # <-- NEW
    )
```

**Files to Update:**
1. `/c/Users/kylem/openai-agents-workflows-2025.09.28-v1/src/actions/adapters/google.py`
   - Locations: All `record_action_execution()` calls (approximately 6-8 calls)
   - Pattern: Add `workspace_id=workspace_id` parameter

2. `/c/Users/kylem/openai-agents-workflows-2025.09.28-v1/src/actions/adapters/microsoft.py`
   - Locations: All `record_action_execution()` calls (approximately 8-10 calls)
   - Pattern: Add `workspace_id=workspace_id` parameter

3. `/c/Users/kylem/openai-agents-workflows-2025.09.28-v1/src/actions/adapters/independent.py`
   - Check for any `record_action_execution()` calls
   - Pattern: Add `workspace_id=workspace_id` parameter

4. `/c/Users/kylem/openai-agents-workflows-2025.09.28-v1/src/actions/execution.py`
   - Check for `record_action_execution()` calls
   - Pattern: Extract workspace_id from context and pass down

**Validation:**
```bash
# Find all calls to record_action_execution in adapters
grep -n "record_action_execution" src/actions/adapters/*.py
# Expected output should show all locations to update
```

---

### 2. QUEUE JOB RECORDING

**Current State:**
```bash
# Search for existing calls
grep -rn "record_queue_job" src/
# Expected: Very few or no results currently
```

**Finding Queue Job Calls:**

1. **Orchestrator Scheduler** - `/c/Users/kylem/openai-agents-workflows-2025.09.28-v1/src/orchestrator/scheduler.py`
   - Likely location: Job execution completion point
   - Pattern: After job completes, record metrics

2. **Queue Backends** - `/c/Users/kylem/openai-agents-workflows-2025.09.28-v1/src/queue/backends/*.py`
   - Likely location: After job processing
   - Pattern: When job duration is measured

3. **Workflow Runner** - `/c/Users/kylem/openai-agents-workflows-2025.09.28-v1/src/workflows/` or orchestrator
   - Likely location: After workflow execution
   - Pattern: Job metrics recording

**Implementation Pattern:**
```python
# When recording queue job metrics
from src.telemetry.prom import record_queue_job

# Extract workspace_id from job context (varies by implementation)
workspace_id = job_context.get("workspace_id") or workflow.workspace_id

record_queue_job(
    job_type="workflow_run",  # or job_type from job definition
    duration_seconds=job_duration,
    workspace_id=workspace_id  # <-- NEW
)
```

**Action Items:**
- [ ] Find all existing `record_queue_job()` calls (if any)
- [ ] Find all places where job metrics should be recorded
- [ ] Identify how to extract workspace_id from job context
- [ ] Update calls with workspace_id parameter

---

### 3. PROMETHEUS METRIC DEFINITIONS

**Current State (prom.py):**
```python
# Lines ~180-200 (approximate, in init_prometheus())
_action_exec_total = Counter(
    name="action_exec_total",
    documentation="Total action executions",
    labelnames=["provider", "action", "status"]
)

_action_latency_seconds = Histogram(
    name="action_latency_seconds",
    documentation="Action execution latency",
    labelnames=["provider", "action"]
)
```

**Commit B Changes:**
```python
# Add conditional logic based on is_workspace_label_enabled()
from src.telemetry.prom import is_workspace_label_enabled

def init_prometheus() -> None:
    ...
    # Option 1: Single metric with conditional label (simpler)
    workspace_labels = ["workspace_id"] if is_workspace_label_enabled() else []

    _action_exec_total = Counter(
        name="action_exec_total",
        documentation="Total action executions",
        labelnames=["provider", "action", "status"] + workspace_labels
    )

    # OR Option 2: Separate metrics (cleaner for gradual rollout)
    # _action_exec_total stays as-is
    # _action_exec_total_by_workspace = Counter(...)  # New metric when enabled
```

**RECOMMENDATION: Use Option 2 (Separate Metrics)**
- Allows gradual rollout without breaking existing dashboards
- Can deprecate old metric after monitoring proves stable
- Cleaner from monitoring perspective

**Implementation:**
```python
# In init_prometheus()
global _action_exec_total_by_workspace, _action_latency_seconds_by_workspace
global _queue_job_latency_by_workspace

if is_workspace_label_enabled():
    _action_exec_total_by_workspace = Counter(
        name="action_exec_total_by_workspace",
        documentation="Total action executions per workspace",
        labelnames=["workspace_id", "provider", "action", "status"]
    )

    _action_latency_seconds_by_workspace = Histogram(
        name="action_latency_seconds_by_workspace",
        documentation="Action execution latency per workspace",
        labelnames=["workspace_id", "provider", "action"]
    )

    _queue_job_latency_by_workspace = Histogram(
        name="queue_job_latency_seconds_by_workspace",
        documentation="Queue job latency per workspace",
        labelnames=["workspace_id", "job_type"]
    )
```

**Files to Update:**
- `/c/Users/kylem/openai-agents-workflows-2025.09.28-v1/src/telemetry/prom.py`
  - Update `init_prometheus()` function to create workspace-scoped metrics when flag enabled
  - Update `record_action_execution()` to use workspace metric when enabled
  - Update `record_queue_job()` to use workspace metric when enabled

---

### 4. RECORDING RULES (PROMETHEUS CONFIG)

**Current State:**
```yaml
# config/prometheus/prometheus-recording.yml
groups:
- name: gmail_send_recording
  interval: 30s
  rules:
  - record: job:gmail_send_exec_rate:5m
    expr: sum(rate(action_exec_total{provider="google",action="gmail.send"}[5m]))
  # ... more rules ...
```

**Commit B Changes:**
Add new recording rules for workspace-scoped metrics when enabled:

```yaml
- name: gmail_send_recording_by_workspace
  interval: 30s
  rules:
  # Only applied when workspace labels present
  - record: job:gmail_send_exec_rate_by_workspace:5m
    expr: sum(rate(action_exec_total_by_workspace{provider="google",action="gmail.send"}[5m])) by (workspace_id)

  - record: job:gmail_send_latency_p95_by_workspace:5m
    expr: histogram_quantile(0.95, sum(rate(action_latency_seconds_by_workspace_bucket{provider="google",action="gmail.send"}[5m])) by (le, workspace_id))

  # Per-workspace error rate
  - record: job:gmail_send_errors_rate_by_workspace:5m
    expr: |
      sum(rate(action_error_total{provider="google",action="gmail.send"}[5m])) by (workspace_id)
      / clamp_min(job:gmail_send_exec_rate_by_workspace:5m, 1)
```

**Files to Update:**
- `/c/Users/kylem/openai-agents-workflows-2025.09.28-v1/config/prometheus/prometheus-recording.yml`
  - Add new recording rules for workspace-scoped aggregations
  - Include rules for all major metrics (action_exec, action_latency, queue_latency)

---

### 5. METRIC RECORDING LOGIC (prom.py Updates)

**Current Implementation:**
```python
def record_action_execution(
    provider: str, action: str, status: str, duration_seconds: float, workspace_id: str | None = None
) -> None:
    """Record action execution metrics."""
    if not _PROM_AVAILABLE or not _METRICS_INITIALIZED:
        return

    try:
        _action_exec_total.labels(provider=provider, action=action, status=status).inc()
        _action_latency_seconds.labels(provider=provider, action=action).observe(duration_seconds)
    except Exception as exc:
        _LOG.warning("Failed to record action execution metric: %s", exc)
```

**Commit B Implementation:**
```python
def record_action_execution(
    provider: str, action: str, status: str, duration_seconds: float, workspace_id: str | None = None
) -> None:
    """Record action execution metrics."""
    if not _PROM_AVAILABLE or not _METRICS_INITIALIZED:
        return

    try:
        # Always record baseline metrics
        _action_exec_total.labels(provider=provider, action=action, status=status).inc()
        _action_latency_seconds.labels(provider=provider, action=action).observe(duration_seconds)

        # Record workspace-scoped metrics if enabled and valid
        if is_workspace_label_enabled():
            canonical_id = canonical_workspace_id(workspace_id)
            if canonical_id:
                _action_exec_total_by_workspace.labels(
                    workspace_id=canonical_id,
                    provider=provider,
                    action=action,
                    status=status
                ).inc()
                _action_latency_seconds_by_workspace.labels(
                    workspace_id=canonical_id,
                    provider=provider,
                    action=action
                ).observe(duration_seconds)
    except Exception as exc:
        _LOG.warning("Failed to record action execution metric: %s", exc)
```

**Similar pattern for `record_queue_job()`**

---

## TESTING STRATEGY

### Unit Tests (Extend existing test_workspace_metrics.py)

```python
class TestRecordActionExecutionWithWorkspaceLabel:
    """Test record_action_execution() actually records workspace_id label."""

    def test_records_baseline_metrics_without_workspace_label(self, monkeypatch):
        """Baseline metrics should be recorded even without workspace_id."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "true")
        monkeypatch.setenv("METRICS_WORKSPACE_LABEL", "off")

        init_prometheus()
        record_action_execution("google", "gmail.send", "success", 1.5)

        # Should have recorded baseline metric
        # Check _action_exec_total was incremented

    def test_records_workspace_metrics_when_enabled(self, monkeypatch):
        """Workspace metrics should be recorded when flag enabled."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "true")
        monkeypatch.setenv("METRICS_WORKSPACE_LABEL", "on")
        monkeypatch.setenv("METRICS_WORKSPACE_ALLOWLIST", "workspace-1")

        init_prometheus()
        record_action_execution("google", "gmail.send", "success", 1.5, workspace_id="workspace-1")

        # Should have recorded BOTH baseline and workspace metrics
        # Check _action_exec_total_by_workspace was incremented

    def test_ignores_invalid_workspace_id(self, monkeypatch):
        """Invalid workspace_id should be ignored, baseline metrics still recorded."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "true")
        monkeypatch.setenv("METRICS_WORKSPACE_LABEL", "on")
        monkeypatch.setenv("METRICS_WORKSPACE_ALLOWLIST", "workspace-1")

        init_prometheus()
        record_action_execution("google", "gmail.send", "success", 1.5, workspace_id="INVALID")

        # Should have recorded baseline metric
        # Should NOT have recorded workspace metric
```

### Integration Tests

```python
class TestWorkspaceMetricsIntegration:
    """Test workspace_id flows through full action execution pipeline."""

    def test_action_adapter_passes_workspace_id_to_metrics(self, monkeypatch):
        """Verify workspace_id flows from adapter to metrics."""
        monkeypatch.setenv("TELEMETRY_ENABLED", "true")
        monkeypatch.setenv("METRICS_WORKSPACE_LABEL", "on")
        monkeypatch.setenv("METRICS_WORKSPACE_ALLOWLIST", "test-workspace")

        adapter = GmailSendAdapter()

        # Execute action with workspace_id
        result = await adapter.execute(
            action="gmail.send",
            params={"to": "test@example.com", "subject": "Test"},
            workspace_id="test-workspace",
            actor_id="actor-1"
        )

        # Query Prometheus and verify workspace label is present
        metrics_output = generate_metrics_text()
        assert 'workspace_id="test-workspace"' in metrics_output
        assert 'action_exec_total_by_workspace' in metrics_output
```

### Canary Test (Manual)

```bash
# Enable workspace metrics with small allowlist
export TELEMETRY_ENABLED=true
export METRICS_WORKSPACE_LABEL=on
export METRICS_WORKSPACE_ALLOWLIST="canary-1"

# Run workflow with workspace_id="canary-1"
python -m workflows.runner --workspace-id canary-1 --workflow test-workflow

# Check Prometheus output
curl http://localhost:9090/metrics | grep workspace_id

# Expected output:
# action_exec_total_by_workspace{action="gmail.send",provider="google",status="success",workspace_id="canary-1"} 1
# action_latency_seconds_by_workspace_bucket{...workspace_id="canary-1"...} X
```

---

## ROLLOUT PLAN

### Phase 1: Development & Testing (Sprint 59 Week 1)
- [ ] Implement Commit B changes (plumbing)
- [ ] Write unit tests (test coverage)
- [ ] Write integration tests
- [ ] Code review & approval
- [ ] Merge to main

### Phase 2: Canary Rollout (Sprint 59 Week 2)
- [ ] Deploy with METRICS_WORKSPACE_LABEL=off (default)
- [ ] Verify baseline metrics still working
- [ ] Enable flag for canary workspace in staging
- [ ] Monitor Prometheus cardinality

### Phase 3: Gradual Rollout (Sprint 59 Week 3+)
- [ ] Start with METRICS_WORKSPACE_ALLOWLIST with 5 workspaces
- [ ] Monitor memory/CPU of Prometheus
- [ ] Expand allowlist to 10, 20, 50 workspaces gradually
- [ ] Update Grafana dashboards to support workspace filters

### Phase 4: Production (Sprint 59-02+)
- [ ] Enable for all active workspaces
- [ ] Remove baseline-only metrics after 2-week transition
- [ ] Update alerting rules to use workspace-scoped metrics

---

## SUCCESS CRITERIA

- [ ] All unit tests passing (>90% coverage of new code)
- [ ] Integration tests verify workspace_id labels appear in Prometheus
- [ ] Canary test with METRICS_WORKSPACE_ALLOWLIST="canary-1" succeeds
- [ ] Prometheus cardinality stays below 10K series
- [ ] Prometheus memory consumption stays below 500MB
- [ ] Action latency baseline test shows <1% overhead
- [ ] Grafana dashboards updated to support workspace filtering
- [ ] Operator runbook updated with troubleshooting

---

## MIGRATION PATH (Commit C+)

Future enhancements after Commit B stabilizes:

1. **Sampling (Sprint 60):**
   - Add METRICS_WORKSPACE_SAMPLE_RATE=0.1 (record only 10% of workspaces)
   - Reduces cardinality while maintaining visibility

2. **Dynamic Allowlist (Sprint 60):**
   - Load allowlist from database instead of env var
   - Sync with active workspaces list
   - No restart needed to update allowlist

3. **Reconciliation (Sprint 60):**
   - Compare allowlist against actual workspace list
   - Alert if allowlist diverges from reality

4. **Hierarchical Workspaces (Sprint 61):**
   - Support team/workspace hierarchy in metrics
   - Example: workspace_id="team-eng/workspace-api"

---

## KEY CONTACTS

- **Architecture Review:** Completed by Tech Lead
- **Commit A Owner:** kmabbott81 (author)
- **Commit B Owner:** (To be assigned)
- **Sprint Lead:** (To be assigned)

---

## REFERENCE DOCUMENTS

1. Commit A Architecture Review: `/ARCHITECTURE_REVIEW_S59_01_COMMIT_A.md`
2. Commit A Changes: Commit 9daeadb in branch `sprint-59/s59-01-metrics-workspace`
3. Test Suite: `tests/test_workspace_metrics.py` (28 tests)
4. Prometheus Best Practices: https://prometheus.io/docs/practices/naming/

---

**Last Updated:** 2025-10-16
**Status:** Ready for Commit B Planning
