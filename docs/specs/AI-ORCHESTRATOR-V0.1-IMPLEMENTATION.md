# AI Orchestrator v0.1 Implementation Plan

## Status: IN PROGRESS

## Overview
Implement AI iPaaS brain that can plan and execute across providers (Gmail, Outlook) from natural language prompts.

## Completed
- ✅ Created schema: `src/schemas/ai_plan.py` (PlanResult, PlannedAction)
- ✅ Updated config: `src/config.py` (added get_openai_client_and_limits helper)
- ✅ Set up environment configuration defaults

## In Progress
- 🚧 Creating v2 planner with strict JSON schema + cost control
- 🚧 Adding telemetry helpers
- 🚧 Creating /ai/plan2 endpoint

## Remaining Work

### Slice 1: Schemas + planner + /ai/plan2 + telemetry
- [ ] Create `src/ai/planner_v2.py` with strict JSON schema mode
- [ ] Add telemetry functions to `src/telemetry/prom.py`:
  - `record_ai_planner(status, duration_seconds)`
  - `record_ai_tokens(tokens_input, tokens_output)`
- [ ] Add `/ai/plan2` endpoint to `src/webapi.py`
- [ ] Test planning with Gmail/Outlook actions

### Slice 2: Queue + execute + worker + runner
- [ ] Create `src/security/permissions.py` (can_execute function)
- [ ] Create `src/queue/simple_queue.py` (Redis-based job queue)
- [ ] Create `src/queue/keys.py` (Redis key helpers)
- [ ] Create `src/actions/runner.py` (adapter router)
- [ ] Add `/ai/execute` endpoint (enqueue jobs)
- [ ] Add `/ai/jobs/{job_id}` endpoint (job status)
- [ ] Create `scripts/worker_actions.py` (job processor)
- [ ] Add queue telemetry metrics

### Slice 3: Dev UI
- [ ] Update `static/dev/action-runner.js`:
  - Add "Plan (v2)" button
  - Add "Plan → Execute" button with polling
- [ ] Keep existing OAuth-aware behavior

### Slice 4: Prometheus rules
- [ ] Add recording rules to `config/prometheus/prometheus-recording.yml`
- [ ] Add alerts to `config/prometheus/prometheus-alerts.yml`

### Slice 5: Tests
- [ ] Create `tests/ai/test_plan2_schema_unit.py`
- [ ] Create `tests/ai/test_execute_queue_unit.py`
- [ ] Create `tests/ai/test_worker_happy_path_unit.py`

### Slice 6: Evidence
- [ ] Create `docs/evidence/sprint-55/AI-ORCHESTRATOR-V0.1-COMPLETE.md`
- [ ] Include screenshots (Dev UI, PromQL, sample plan JSON)
- [ ] Add self-critique paragraph

## Environment Variables

```bash
# AI Planning
AI_MODEL=gpt-4o-mini
AI_MAX_OUTPUT_TOKENS=800
AI_MAX_TOKENS_PER_MIN=8000

# Permissions
ALLOW_ACTIONS_DEFAULT=gmail.send,outlook.send

# Existing (reused)
OPENAI_API_KEY=...
REDIS_URL=...
```

## Key Design Decisions

1. **Idempotency**: Use `client_request_id` with Redis SETNX (15m TTL)
2. **Cost Control**: Token budget enforcement in planner
3. **Permissions**: Simple env-based allowlist for v0.1
4. **Queue**: Redis lists (LPUSH/RPOP) + hash for results
5. **Rollout**: Reuse existing rollout gate for adapter execution
6. **Telemetry**: Counters, histograms, gauges for full observability

## API Endpoints

### POST /ai/plan2
```json
Request:
{
  "prompt": "Send email to john@example.com saying thanks for the meeting"
}

Response:
{
  "plan": {
    "intent": "send_email",
    "confidence": 0.95,
    "actions": [{
      "provider": "google",
      "action": "gmail.send",
      "params": {"to": "john@example.com", "subject": "Thanks", "text": "..."},
      "client_request_id": "uuid-here"
    }]
  },
  "meta": {
    "model": "gpt-4o-mini",
    "duration": 1.23,
    "tokens_in": 150,
    "tokens_out": 200
  }
}
```

### POST /ai/execute
```json
Request:
{
  "actions": [...],  // From PlanResult
  "workspace_id": "uuid",
  "actor_id": "user@example.com"
}

Response:
{
  "job_ids": ["job-uuid-1", "job-uuid-2"]
}
```

### GET /ai/jobs/{job_id}
```json
Response:
{
  "status": "completed",  // pending|running|completed|error
  "result": {...},
  "error": null,
  "duration_ms": 1234
}
```

## Success Criteria

- ✅ Can plan Gmail send from NL prompt
- ✅ Can plan Outlook send from NL prompt
- ✅ Can execute planned actions via queue
- ✅ Idempotency prevents duplicate sends
- ✅ Permissions block unauthorized actions
- ✅ Cost cap prevents runaway token usage
- ✅ All metrics emitting to Prometheus
- ✅ Dev UI buttons working end-to-end
- ✅ Tests green
