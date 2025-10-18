# Sprint 60 Phase 3: Backfill Script for Zero-Downtime Migration

## Overview

Phase 3 implements the backfill script to migrate existing jobs from old schema (`ai:jobs:{job_id}`) to new schema (`ai:job:{workspace_id}:{job_id}`) with zero downtime and full observability.

## Files

- `scripts/backfill_redis_keys.py` - Main backfill script (~250 LOC)
- `tests/test_backfill_script.py` - Comprehensive test suite (9 tests, ~280 LOC)
- `src/telemetry/prom.py` - Backfill telemetry metrics
- `Makefile` - Backfill convenience targets

## Quick Start

### Dry Run (Safe, No Writes)

```bash
# Using Makefile
make backfill-dry-run

# Or directly
python -m scripts.backfill_redis_keys --dry-run --rps 200 --batch 1000
```

### Execute Migration

```bash
# Using Makefile
make backfill-exec

# Or directly
python -m scripts.backfill_redis_keys --execute --rps 100 --batch 500
```

### Run Tests

```bash
make backfill-test
# Or
pytest tests/test_backfill_script.py -v
```

## CLI Options

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--dry-run` | flag | - | Count migrations without writing (required: one of --dry-run or --execute) |
| `--execute` | flag | - | Execute migrations (required: one of --dry-run or --execute) |
| `--rps` | int | 100 | Rate limit (requests per second) |
| `--batch` | int | 500 | SCAN batch size |
| `--cursor` | str | "0" | Starting cursor (for manual resume) |
| `--max-keys` | int | - | Optional maximum keys to process |
| `--workspace` | str | - | Optional workspace ID filter |
| `--progress-key` | str | "ai:backfill" | Progress key prefix in Redis |
| `--redis-url` | str | $REDIS_URL | Redis connection URL |

## Features

### 1. Idempotency

The script is fully idempotent - running multiple times will skip already-migrated keys:

```python
# Second run skips existing keys
stats = backfill_keys(...)
# stats["skipped_exists"] > 0
```

### 2. Resumability

Progress is automatically tracked in Redis. If interrupted, restart with the same `--progress-key` to continue:

```bash
# First run (interrupted)
python -m scripts.backfill_redis_keys --execute --rps 100

# Resume automatically
python -m scripts.backfill_redis_keys --execute --rps 100
```

Progress keys:
- `{progress-key}:cursor` - SCAN cursor position
- `{progress-key}:last_job` - Last processed job_id

### 3. Rate Limiting

Rate limiting prevents Redis overload:

```bash
# Process 10 jobs per second
python -m scripts.backfill_redis_keys --execute --rps 10
```

### 4. Workspace Isolation

Workspace validation enforced during migration:
- Invalid workspace IDs are skipped
- Telemetry records `skipped{reason=invalid}`
- Logs contain no secrets or PII

### 5. Safe Failure Handling

- **No deletion**: Old keys are never deleted (Phase 4 cleanup)
- **Write verification**: Each migration is verified before continuing
- **Error isolation**: One failed job doesn't stop the entire backfill
- **Retry**: Automatic retry once on write errors

## Telemetry Metrics

Monitor backfill progress via Prometheus:

```promql
# Scanned keys by workspace
relay_backfill_scanned_total{workspace_id="workspace-123"}

# Migrated keys
relay_backfill_migrated_total{workspace_id="workspace-123"}

# Skipped keys (exists, invalid, error)
relay_backfill_skipped_total{workspace_id="workspace-123",reason="exists"}

# Errors
relay_backfill_errors_total{workspace_id="workspace-123"}

# Duration histogram
relay_backfill_duration_seconds
```

### Example Grafana Queries

**Migration Progress by Workspace**:
```promql
relay_backfill_migrated_total /
  (relay_backfill_migrated_total + relay_backfill_skipped_total{reason="exists"}) * 100
```

**Error Rate**:
```promql
rate(relay_backfill_errors_total[5m])
```

## Operational Guide

### Step 1: Validate Configuration

Ensure feature flags are correct:

```bash
# Phase 2.2 must be deployed first
READ_PREFERS_NEW=on
READ_FALLBACK_OLD=on
```

### Step 2: Run Dry-Run

Test the migration without writes:

```bash
make backfill-dry-run
```

Expected output:
```
=== Backfill Summary ===
Scanned:        12345
Migrated:       12345  (counted, not written)
Skipped (exist):0
Skipped (invalid):12
Errors:         0
```

### Step 3: Execute Small Batch

Test with limited scope:

```bash
python -m scripts.backfill_redis_keys --execute --max-keys 100 --rps 10
```

### Step 4: Monitor Telemetry

Watch Grafana dashboard:
- `relay_backfill_scanned_total` increasing
- `relay_backfill_migrated_total` matching expected count
- `relay_backfill_errors_total` stable at 0

### Step 5: Full Migration

Run full backfill (can be interrupted and resumed):

```bash
make backfill-exec
# Or with higher throughput:
python -m scripts.backfill_redis_keys --execute --rps 200 --batch 1000
```

### Step 6: Verify Completion

Check read path distribution:

```promql
# Should approach 100% "new"
relay_job_read_path_total{path="new"} /
  sum(relay_job_read_path_total) * 100
```

### Step 7: Disable Fallback (Phase 4)

Once 98%+ migrated, disable old schema fallback:

```bash
# Set in environment
READ_FALLBACK_OLD=off

# Restart service
```

## Resuming After Interruption

The script automatically resumes from the last cursor position:

```bash
# Interrupted backfill
$ python -m scripts.backfill_redis_keys --execute --rps 100
^C  # SIGINT

# Resume automatically
$ python -m scripts.backfill_redis_keys --execute --rps 100
Resuming from stored cursor=12345, last_job=job-abc123
```

## Workspace Filtering

Migrate one workspace at a time for staged rollout:

```bash
# Migrate workspace-123 only
python -m scripts.backfill_redis_keys --execute \
  --workspace workspace-123 \
  --rps 50

# Migrate workspace-456
python -m scripts.backfill_redis_keys --execute \
  --workspace workspace-456 \
  --rps 50
```

## Rollback Strategy

**Backfill is non-destructive** - old keys are never deleted. To rollback:

1. **Stop backfill** (if running)
2. **Disable new schema reads**:
   ```bash
   READ_PREFERS_NEW=off
   READ_FALLBACK_OLD=on
   ```
3. **Restart service** - will read from old schema only
4. **Investigate issues** before re-running

## Performance Tuning

### Low-Impact Mode (Production)

```bash
python -m scripts.backfill_redis_keys --execute --rps 50 --batch 100
```

- **RPS: 50** - Low Redis load
- **Batch: 100** - Small SCAN chunks
- **Duration**: ~5-10 hours for 1M keys

### High-Throughput Mode (Staging)

```bash
python -m scripts.backfill_redis_keys --execute --rps 500 --batch 2000
```

- **RPS: 500** - High Redis load (monitor CPU/memory)
- **Batch: 2000** - Larger SCAN chunks
- **Duration**: ~1 hour for 1M keys

## Troubleshooting

### Issue: High Memory Usage

**Cause**: Batch size too large

**Fix**: Reduce `--batch`:
```bash
python -m scripts.backfill_redis_keys --execute --batch 100
```

### Issue: Redis Timeouts

**Cause**: RPS too high

**Fix**: Reduce `--rps`:
```bash
python -m scripts.backfill_redis_keys --execute --rps 20
```

### Issue: Stuck at Same Cursor

**Cause**: All remaining keys are invalid

**Check**: Review logs for `skipped_invalid` warnings

**Fix**: Manually inspect invalid workspace IDs:
```bash
redis-cli --scan --pattern "ai:jobs:*" | xargs redis-cli HGET workspace_id
```

### Issue: Telemetry Not Recording

**Cause**: `TELEMETRY_ENABLED=false`

**Fix**: Enable telemetry:
```bash
export TELEMETRY_ENABLED=true
python -m scripts.backfill_redis_keys --execute
```

## Testing

Comprehensive test suite with fakeredis:

```bash
# Run all backfill tests
pytest tests/test_backfill_script.py -v

# Run specific test
pytest tests/test_backfill_script.py::TestDryRunMode::test_dry_run_no_writes_but_counts_increment -v
```

Test coverage:
- ✅ Dry-run mode (no writes)
- ✅ Execute mode (writes to new schema)
- ✅ Idempotency (second run skips)
- ✅ Resumability (cursor tracking)
- ✅ Invalid workspace handling
- ✅ Telemetry recording
- ✅ Rate limiting
- ✅ Max keys limit
- ✅ Workspace filtering

## Related Documentation

- **Phase 1**: `SPRINT_60_PHASE_1_SUMMARY.md` - Dual-write implementation
- **Phase 2**: `SPRINT_60_PHASE_2_SUMMARY.md` - Workspace isolation fixes
- **Phase 2.2**: Gate 2 agent reviews (v0.1.7-phase2.2-final)
- **Patterns**: `RECOMMENDED_PATTERNS_S60_MIGRATION.md` - Migration patterns

## Exit Criteria

- [ ] All backfill tests passing (9+)
- [ ] No regressions in existing test suite
- [ ] Dry-run completes without errors
- [ ] Execute migrates keys successfully
- [ ] Telemetry metrics populate correctly
- [ ] Rate limiting enforced
- [ ] Resumability verified
- [ ] Agent reviews pass (Code, Security, Tech-Lead)
