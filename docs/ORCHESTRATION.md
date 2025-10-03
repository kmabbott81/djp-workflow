# Orchestration - DAG Core (Sprint 27A)

Minimal DAG execution system for chaining workflows. Scheduler, state persistence, and observability come in 27B/27C.

## Purpose

Run multiple workflows in sequence or parallel, passing outputs between tasks. Useful for:
- Weekly operations chains (inbox sweep → report → meeting brief)
- Multi-stage data pipelines
- Complex workflows with dependencies

## Quick Start

### 1. Define a DAG (YAML)

```yaml
name: weekly_ops_chain
tenant_id: local-dev

tasks:
  - id: sweep
    workflow_ref: inbox_drive_sweep
    params:
      inbox_items: "Email list..."
    retries: 1
    depends_on: []

  - id: report
    workflow_ref: weekly_report_pack
    params:
      start_date: "2025-10-01"
      end_date: "2025-10-07"
    retries: 1
    depends_on:
      - sweep  # Waits for sweep to complete

  - id: brief
    workflow_ref: meeting_transcript_brief
    params:
      meeting_title: "Sprint Review"
    retries: 1
    depends_on:
      - report
```

### 2. Run with Dry-Run

```bash
python scripts/run_dag_min.py --dag configs/dags/weekly_ops_chain.min.yaml --dry-run
```

**Output:**
```
DRY RUN: DAG 'weekly_ops_chain'
Tenant: local-dev
Tasks: 3

Execution Plan:
  1. sweep (workflow: inbox_drive_sweep, depends_on: none)
  2. report (workflow: weekly_report_pack, depends_on: sweep)
  3. brief (workflow: meeting_transcript_brief, depends_on: report)
```

### 3. Execute Live

```bash
python scripts/run_dag_min.py --dag configs/dags/weekly_ops_chain.min.yaml
```

**Output:**
```
DAG EXECUTION COMPLETE
DAG: weekly_ops_chain
Tasks Succeeded: 3
Tasks Failed: 0
Duration: 2.34s
```

## Payload Passing

Upstream task outputs are automatically merged into downstream params with namespaced keys:

**Example:**
- Task `sweep` returns `{"summary": "Prioritized 15 items"}`
- Task `report` (depends on `sweep`) receives params:
  ```python
  {
    "start_date": "2025-10-01",  # Original param
    "sweep__summary": "Prioritized 15 items"  # Namespaced upstream output
  }
  ```

This avoids key collisions between tasks.

## Retries

Set `retries` per task. Failed tasks retry with exponential backoff (reuses `src/queue/retry.py`).

```yaml
- id: flaky_task
  workflow_ref: some_workflow
  retries: 2  # Retry up to 2 times (3 attempts total)
```

## Event Logging

All executions emit events to `logs/orchestrator_events.jsonl`:

```json
{"timestamp": "2025-10-03T10:00:00", "event": "dag_start", "dag_name": "weekly_ops_chain"}
{"timestamp": "2025-10-03T10:00:01", "event": "task_start", "task_id": "sweep"}
{"timestamp": "2025-10-03T10:00:02", "event": "task_ok", "task_id": "sweep"}
{"timestamp": "2025-10-03T10:00:03", "event": "dag_done", "tasks_succeeded": 3}
```

## Available Workflows

Current workflow registry (`src/workflows/adapter.py`):
- `inbox_drive_sweep` - Inbox/drive prioritization
- `weekly_report_pack` - Weekly status reports
- `meeting_transcript_brief` - Meeting summaries

## Scheduling & State (Sprint 27B)

### State Store

JSONL append-only store tracks all scheduler events and DAG run metadata at `logs/orchestrator_state.jsonl`.

**Functions:**
```python
from src.orchestrator.state_store import record_event, last_runs, index_by

# Record event
record_event({"event": "run_finished", "status": "success"})

# Get last 20 events
events = last_runs(limit=20)

# Index by schedule_id
by_schedule = index_by("schedule_id", limit=100)
```

### Scheduler

Cron-like scheduler for automated DAG execution.

**Define Schedule (YAML):**
```yaml
- id: weekly_ops_chain
  cron: "*/5 * * * *"  # Every 5 minutes
  dag: configs/dags/weekly_ops_chain.min.yaml
  tenant: local-dev
  enabled: true
```

Place in `configs/schedules/*.yaml`.

**Cron Format:**
```
minute hour day month weekday
*/5    *    *   *     *        # Every 5 minutes
0      9    *   *     *        # Daily at 9:00 AM
0      */2  *   *     *        # Every 2 hours
*      *    *   *     *        # Every minute (not recommended)
```

**Run Once (CI-safe):**
```bash
python -m src.orchestrator.scheduler --dir configs/schedules --once
```

Runs single tick, enqueues matching schedules, drains queue, exits.

**Serve Continuously:**
```bash
python -m src.orchestrator.scheduler --dir configs/schedules --serve
```

Runs until Ctrl+C. Ticks at `SCHED_TICK_MS` interval (default 1000ms).

**Environment Variables:**
```bash
STATE_STORE_PATH=logs/orchestrator_state.jsonl
ORCH_EVENTS_PATH=logs/orchestrator_events.jsonl
SCHED_TICK_MS=1000           # Tick interval in milliseconds
SCHED_MAX_PARALLEL=3         # Max concurrent DAG runs
```

**State Events:**
- `schedule_enqueued` - Schedule matched, run queued
- `run_started` - DAG execution started
- `run_finished` - DAG execution completed (success/failed)

**De-duplication:**
Scheduler prevents double-enqueue within same minute using `{schedule_id, minute}` key.

### Reading Logs

**State store (scheduler events):**
```bash
tail -f logs/orchestrator_state.jsonl | grep run_finished
```

**Orchestrator events (task-level):**
```bash
tail -f logs/orchestrator_events.jsonl | grep task_fail
```

## Observability (Sprint 27C)

Dashboard panel showing DAG runs, schedules, and per-tenant metrics.

### Data Sources

**Orchestrator Events** (`logs/orchestrator_events.jsonl`)
- Task-level events from DAG execution
- Written by runner during execution
- Events: `dag_start`, `task_start`, `task_ok`, `task_fail`, `task_retry`, `dag_done`

**State Store** (`logs/orchestrator_state.jsonl`)
- Scheduler-level events
- Written by scheduler when enqueuing/running schedules
- Events: `schedule_enqueued`, `run_started`, `run_finished`

### Dashboard Metrics

**Task KPIs (Last 24h):**
- ✅ Tasks OK - Successful task completions
- ❌ Tasks Failed - Failed task executions
- ⏱️ Avg Duration - Average task execution time
- 📊 Error Rate - Percentage of failed tasks

**Recent DAG Runs:**
- Table showing last 15 DAG executions
- Status, start time, duration, tasks OK/failed per run

**Schedules:**
- Schedule ID, last run time, status (success/failed)
- Enqueued count, success count, failed count

**Per-Tenant Load (Last 24h):**
- Tenant ID, run count, task count
- Error rate and average latency per tenant

### Environment Variables

```bash
ORCH_EVENTS_PATH=logs/orchestrator_events.jsonl
STATE_STORE_PATH=logs/orchestrator_state.jsonl
ORCH_PANEL_WINDOW_H=24  # Time window for recent metrics
```

### Accessing Dashboard

```bash
streamlit run main.py
```

Navigate to "Observability" tab → "🔀 Orchestrator (DAGs & Schedules)" section.

### Analytics API

Pure Python helpers for programmatic access:

```python
from src.orchestrator.analytics import (
    load_events,
    summarize_tasks,
    summarize_dags,
    summarize_schedules,
    per_tenant_load,
)

# Load events
events = load_events("logs/orchestrator_events.jsonl", limit=5000)

# Get task stats
stats = summarize_tasks(events, window_hours=24)
print(f"Error rate: {stats['last_24h']['error_rate'] * 100:.1f}%")

# Get recent DAG runs
runs = summarize_dags(events, limit=10)
for run in runs:
    print(f"{run['dag_name']}: {run['status']} ({run['duration']:.1f}s)")

# Get per-tenant metrics
tenants = per_tenant_load(events, window_hours=24)
for tenant in tenants:
    print(f"{tenant['tenant']}: {tenant['runs']} runs, {tenant['error_rate']*100:.1f}% errors")
```

## Persistent Queue (Sprint 28)

Durable job queue with pluggable backends for cross-region distribution and at-least-once delivery.

### Queue Backends

**Memory Backend (Default):**
- In-memory queue for development/testing
- Non-persistent (lost on restart)
- Thread-safe for single-process use

**Redis Backend (Production):**
- Persistent storage in Redis
- Supports multiple workers
- Cross-region job distribution
- At-least-once delivery guarantee

### Configuration

```bash
# Queue backend selection
QUEUE_BACKEND=memory  # or "redis"

# Redis connection (if QUEUE_BACKEND=redis)
REDIS_URL=redis://localhost:6379/0

# Worker settings
SCHED_MAX_JOBS_PER_DRAIN=100  # Max jobs to process per drain
```

### Running Scheduler with Persistent Queue

The scheduler automatically uses the configured queue backend:

```bash
# With memory backend (default)
python -m src.orchestrator.scheduler --serve

# With Redis backend
QUEUE_BACKEND=redis REDIS_URL=redis://localhost:6379/0 python -m src.orchestrator.scheduler --serve
```

### Running Workers

Launch standalone workers to consume jobs:

```bash
# Single worker
python -m src.queue.worker --worker-id worker-1

# Multiple workers (horizontal scaling)
python -m src.queue.worker --worker-id worker-1 &
python -m src.queue.worker --worker-id worker-2 &
python -m src.queue.worker --worker-id worker-3 &
```

Workers poll the queue and execute jobs independently. With Redis backend, multiple workers can run on different machines.

### Job Model

Jobs represent scheduled DAG executions:

```python
from src.queue.persistent_queue import Job, JobStatus

job = Job(
    id="unique-job-id",
    dag_path="configs/dags/my_dag.yaml",
    tenant_id="tenant-123",
    schedule_id="daily-report",
    status=JobStatus.PENDING,
    enqueued_at="2025-10-03T10:00:00Z",
    max_retries=2,
)
```

**Job Lifecycle:**
1. `PENDING` - Enqueued, waiting for worker
2. `RUNNING` - Being executed by worker
3. `SUCCESS` - Completed successfully
4. `FAILED` - Failed after all retries
5. `RETRY` - Failed, will retry (if attempts < max_retries)

### Queue Dashboard

View queue status in Observability tab:
- Pending/Running/Success/Failed counts
- Recent jobs with status
- Job IDs, schedules, tenants

**Note:** Queue stats only available when `QUEUE_BACKEND=redis`

## Features

- ✅ DAG validation and execution
- ✅ Retries and event logging
- ✅ Payload passing
- ✅ Scheduler with cron expressions (Sprint 27B)
- ✅ State persistence (Sprint 27B)
- ✅ Observability dashboard (Sprint 27C)
- ✅ Persistent queue with Redis backend (Sprint 28)

## Troubleshooting

**Cycle detected:**
```
CycleDetectedError: Cycle detected in DAG 'my_dag'
```
Fix: Remove circular dependencies in `depends_on`.

**Unknown workflow:**
```
RunnerError: Unknown workflow: invalid_workflow
```
Fix: Use workflow_ref from WORKFLOW_MAP in `src/workflows/adapter.py`.

**Task failed after retries:**
```
RunnerError: Task 'task1' failed after 3 attempts
```
Check `logs/orchestrator_events.jsonl` for error details.
