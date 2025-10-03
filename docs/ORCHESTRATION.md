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

## Limitations (Sprint 27A)

- ✅ DAG validation and execution
- ✅ Retries and event logging
- ✅ Payload passing
- ⏸️ Scheduler (coming in 27B)
- ⏸️ State persistence (coming in 27B)
- ⏸️ Observability dashboard (coming in 27C)

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
