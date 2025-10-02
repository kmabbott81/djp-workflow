# Autoscaling Guide

Sprint 24 introduces dynamic autoscaling for the worker pool to optimize throughput, latency, and cost based on real-time workload demands.

## Table of Contents

- [Architecture Overview](#architecture-overview)
- [Environment Variables](#environment-variables)
- [Scaling Decision Logic](#scaling-decision-logic)
- [Configuration Examples](#configuration-examples)
- [Tuning Guide](#tuning-guide)
- [Integration with Worker Pool](#integration-with-worker-pool)
- [Monitoring & Observability](#monitoring--observability)
- [Troubleshooting](#troubleshooting)

## Architecture Overview

The autoscaling system consists of three core components:

### 1. Autoscaler (`src/scale/autoscaler.py`)

Pure function that analyzes engine state and returns scaling decisions:

```
EngineState → make_scale_decision() → ScaleDecision
```

Key features:
- **Stateless decision making** - No side effects, testable
- **Multi-signal analysis** - Queue depth, P95 latency, worker utilization
- **Cooldown periods** - Prevents oscillation
- **Bounded scaling** - Respects MIN_WORKERS and MAX_WORKERS

### 2. Worker Pool (`src/scale/worker_pool.py`)

Thread-based pool that executes background jobs:

- Graceful scale-up: Spawns new worker threads
- Graceful scale-down: Sends poison pills, drains in-flight jobs
- Region-aware routing: Support for multi-region deployments
- Statistics tracking: Completed/failed job counts

### 3. Queue System (`src/queue/`)

Task distribution with retry logic:

- **Exponential backoff** with jitter
- **Idempotency tracking** to prevent duplicate execution
- **Configurable retry limits**

## Environment Variables

### Core Scaling Parameters

| Variable | Default | Description |
|----------|---------|-------------|
| `MIN_WORKERS` | `1` | Minimum worker count (scale-down floor) |
| `MAX_WORKERS` | `12` | Maximum worker count (scale-up ceiling) |
| `TARGET_P95_LATENCY_MS` | `2000` | Target P95 latency in milliseconds |
| `TARGET_QUEUE_DEPTH` | `50` | Target queue depth (jobs waiting) |
| `SCALE_UP_STEP` | `2` | Workers to add per scale-up decision |
| `SCALE_DOWN_STEP` | `1` | Workers to remove per scale-down decision |
| `SCALE_DECISION_INTERVAL_MS` | `1500` | Cooldown between scaling decisions |

### Worker Pool Parameters

| Variable | Default | Description |
|----------|---------|-------------|
| `CURRENT_REGION` | `default` | Region identifier for this pool |
| `WORKER_SHUTDOWN_TIMEOUT_S` | `30` | Graceful shutdown timeout in seconds |

### Retry Parameters

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_RETRIES` | `3` | Maximum retry attempts per job |
| `RETRY_BASE_MS` | `400` | Base retry delay in milliseconds |
| `RETRY_JITTER_PCT` | `0.2` | Jitter percentage (0.0-1.0) |

### Queue Routing Parameters

| Variable | Default | Description |
|----------|---------|-------------|
| `QUEUE_BACKEND_REALTIME` | `local` | Backend for realtime tasks (local, redis) |
| `QUEUE_BACKEND_BULK` | `local` | Backend for bulk tasks (local, sqs, pubsub) |
| `QUEUE_RATE_LIMIT` | `0` | Rate limit per minute (0 = unlimited) |
| `REDIS_URL` | - | Redis connection URL |
| `SQS_QUEUE_URL` | - | AWS SQS queue URL |
| `PUBSUB_TOPIC` | - | GCP Pub/Sub topic |

## Scaling Decision Logic

The autoscaler uses a **multi-signal approach** to determine when to scale:

### Scale Up Conditions (ANY triggers scale-up)

1. **Queue depth exceeds target**
   ```python
   if queue_depth > TARGET_QUEUE_DEPTH:
       scale_up()
   ```
   Example: Queue has 100 jobs, target is 50 → Scale up

2. **P95 latency exceeds target**
   ```python
   if p95_latency_ms > TARGET_P95_LATENCY_MS:
       scale_up()
   ```
   Example: P95 is 3000ms, target is 2000ms → Scale up

3. **All workers busy with queue backlog**
   ```python
   if in_flight_jobs >= current_workers and queue_depth > 0:
       scale_up()
   ```
   Example: 5 workers, 5 in-flight jobs, 20 queued → Scale up

### Scale Down Conditions (ALL must be true)

1. **Queue depth well below target**
   ```python
   queue_depth <= TARGET_QUEUE_DEPTH * 0.3  # 30% threshold
   ```

2. **P95 latency well below target**
   ```python
   p95_latency_ms <= TARGET_P95_LATENCY_MS * 0.5  # 50% threshold
   ```

3. **Workers not fully utilized**
   ```python
   utilization = in_flight_jobs / current_workers
   utilization < 0.7  # 70% threshold
   ```

### Scale Decision Formula

```
desired_workers = current_workers
reason = ""

# Cooldown check
if time_since_last_scale < SCALE_DECISION_INTERVAL_MS:
    return HOLD

# Scale up (any condition)
if queue_depth > TARGET_QUEUE_DEPTH OR
   p95_latency_ms > TARGET_P95_LATENCY_MS OR
   (in_flight_jobs >= current_workers AND queue_depth > 0):
    desired_workers = min(current_workers + SCALE_UP_STEP, MAX_WORKERS)
    return SCALE_UP

# Scale down (all conditions)
if queue_depth <= TARGET_QUEUE_DEPTH * 0.3 AND
   p95_latency_ms <= TARGET_P95_LATENCY_MS * 0.5 AND
   (in_flight_jobs / current_workers) < 0.7:
    desired_workers = max(current_workers - SCALE_DOWN_STEP, MIN_WORKERS)
    return SCALE_DOWN

# Otherwise hold steady
return HOLD
```

### Cooldown Behavior

Scaling decisions respect a cooldown period to prevent rapid oscillation:

- After any scale action (up or down), autoscaler enters cooldown
- During cooldown, no new scaling decisions made (returns HOLD)
- Cooldown duration: `SCALE_DECISION_INTERVAL_MS` (default 1500ms)
- This stabilizes the pool and allows metrics to reflect new capacity

## Configuration Examples

### Low-Latency Realtime Workload

Optimize for speed with aggressive scaling:

```bash
export MIN_WORKERS=3                    # Keep warm for instant response
export MAX_WORKERS=20                   # Allow high burst capacity
export TARGET_P95_LATENCY_MS=500        # Strict latency SLA
export TARGET_QUEUE_DEPTH=10            # Minimal queuing
export SCALE_UP_STEP=3                  # Rapid scale-up
export SCALE_DOWN_STEP=1                # Conservative scale-down
export SCALE_DECISION_INTERVAL_MS=1000  # Quick reactions
```

**Use case:** Chat interfaces, live approvals, interactive previews

**Characteristics:**
- Keeps 3 workers warm at all times
- Scales up aggressively when latency spikes
- Maintains shallow queue for fast response

### High-Throughput Batch Workload

Optimize for cost with gradual scaling:

```bash
export MIN_WORKERS=1                    # Minimize idle cost
export MAX_WORKERS=50                   # High parallelism
export TARGET_P95_LATENCY_MS=5000       # Relaxed latency
export TARGET_QUEUE_DEPTH=200           # Allow deep queue
export SCALE_UP_STEP=5                  # Batch scale-up
export SCALE_DOWN_STEP=2                # Faster scale-down
export SCALE_DECISION_INTERVAL_MS=3000  # Slower reactions
```

**Use case:** Batch imports, bulk indexing, overnight DJP runs

**Characteristics:**
- Scales down to 1 worker when idle (cost savings)
- Tolerates longer queues before scaling
- Scales up in larger steps for efficiency

### Balanced Production Workload

Balanced approach for mixed workloads:

```bash
export MIN_WORKERS=2                    # Small warm pool
export MAX_WORKERS=12                   # Moderate ceiling
export TARGET_P95_LATENCY_MS=2000       # Reasonable latency
export TARGET_QUEUE_DEPTH=50            # Moderate queue
export SCALE_UP_STEP=2                  # Standard scale-up
export SCALE_DOWN_STEP=1                # Conservative scale-down
export SCALE_DECISION_INTERVAL_MS=1500  # Default cooldown
```

**Use case:** Mixed realtime + batch, production default

**Characteristics:**
- Handles both interactive and background tasks
- Conservative scale-down to avoid thrashing
- Default configuration (no env vars needed)

### Cost-Optimized Dev/Test

Minimal resources for development:

```bash
export MIN_WORKERS=1                    # Single worker
export MAX_WORKERS=3                    # Cap at 3
export TARGET_P95_LATENCY_MS=10000      # Lenient latency
export TARGET_QUEUE_DEPTH=100           # Large queue OK
export SCALE_UP_STEP=1                  # Slow scale-up
export SCALE_DOWN_STEP=1                # Slow scale-down
export SCALE_DECISION_INTERVAL_MS=5000  # Long cooldown
```

**Use case:** Local development, testing, CI/CD

**Characteristics:**
- Minimal resource usage
- Rarely scales beyond 1-2 workers
- Acceptable latency variance

## Tuning Guide

### When to Adjust MIN_WORKERS

**Increase MIN_WORKERS when:**
- Cold-start latency unacceptable
- Predictable baseline load exists
- Cost of idle workers acceptable

**Decrease MIN_WORKERS when:**
- Workload is bursty with long idle periods
- Cost optimization is priority
- Scale-up latency is acceptable

### When to Adjust MAX_WORKERS

**Increase MAX_WORKERS when:**
- Queue depth consistently high during peaks
- P95 latency exceeds target during load
- Downstream services can handle higher concurrency

**Decrease MAX_WORKERS when:**
- Downstream rate limits being hit
- Memory/CPU constraints on host
- Want to enforce capacity ceiling

### When to Adjust TARGET_P95_LATENCY_MS

**Decrease (stricter) when:**
- User-facing interactive workloads
- SLA requires faster response
- Want more aggressive scale-up

**Increase (lenient) when:**
- Background/batch processing
- Latency variance acceptable
- Want to reduce scaling frequency

### When to Adjust TARGET_QUEUE_DEPTH

**Decrease (shallower queue) when:**
- Want faster job pickup
- Memory constraints on queue
- Prefer horizontal scaling over queuing

**Increase (deeper queue) when:**
- Workload is bursty
- Want to buffer spikes before scaling
- Prefer queuing over scaling overhead

### When to Adjust SCALE_UP_STEP

**Increase (larger steps) when:**
- Workload spikes rapidly
- Cold-start time is low
- Want to reach capacity quickly

**Decrease (smaller steps) when:**
- Workload grows gradually
- Want fine-grained scaling
- Resources are constrained

### When to Adjust SCALE_DOWN_STEP

**Increase (faster scale-down) when:**
- Cost optimization priority
- Load drops rapidly
- Confident in scale-up speed

**Decrease (slower scale-down) when:**
- Workload is unpredictable
- Want to avoid thrashing
- Scale-up latency is high

### When to Adjust SCALE_DECISION_INTERVAL_MS

**Decrease (faster reactions) when:**
- Workload changes rapidly
- Low-latency requirements
- Confident in metric accuracy

**Increase (slower reactions) when:**
- Metrics are noisy
- Want to reduce scaling churn
- Workload changes gradually

## Integration with Worker Pool

### Basic Usage

```python
from src.scale.worker_pool import WorkerPool, Job
from src.scale.autoscaler import make_scale_decision, EngineState
from datetime import datetime

# Initialize pool
pool = WorkerPool(initial_workers=2, region="us-west-2")

# Submit jobs
job = Job(
    job_id="job-123",
    task=my_function,
    args=(arg1, arg2),
    kwargs={"key": "value"},
    region="us-west-2",
    submitted_at=datetime.utcnow(),
    retries=0
)
pool.submit_job(job)

# Get current state
stats = pool.get_stats()

# Build engine state
state = EngineState(
    current_workers=stats.total_workers,
    queue_depth=stats.queue_depth,
    p95_latency_ms=calculate_p95_latency(),  # Your metric
    in_flight_jobs=stats.active_workers,
    last_scale_time=last_scale_timestamp
)

# Make scaling decision
decision = make_scale_decision(state)

# Apply scaling
if decision.direction != ScaleDirection.HOLD:
    success = pool.scale_to(decision.desired_workers)
    print(f"Scaled to {decision.desired_workers}: {decision.reason}")
```

### Graceful Scale-Down

The worker pool ensures in-flight jobs complete before terminating:

```python
# Scale down from 10 to 6 workers
pool.scale_to(desired_workers=6)

# Worker pool will:
# 1. Send 4 poison pills to job queue
# 2. Workers receive poison pill and exit after current job
# 3. Wait up to WORKER_SHUTDOWN_TIMEOUT_S (default 30s)
# 4. Clean up terminated threads
# 5. Return True if successful, False if timeout
```

### Region-Aware Routing

For multi-region deployments:

```python
# Create regional pools
pool_west = WorkerPool(initial_workers=3, region="us-west-2")
pool_east = WorkerPool(initial_workers=3, region="us-east-1")

# Route jobs by region
job = Job(job_id="job-456", task=task_func, region="us-west-2")

if job.region == "us-west-2":
    pool_west.submit_job(job)
elif job.region == "us-east-1":
    pool_east.submit_job(job)
```

### Monitoring Worker Pool

```python
# Get statistics
stats = pool.get_stats()

print(f"Total workers: {stats.total_workers}")
print(f"Active workers: {stats.active_workers}")
print(f"Idle workers: {stats.idle_workers}")
print(f"Queue depth: {stats.queue_depth}")
print(f"Jobs completed: {stats.jobs_completed}")
print(f"Jobs failed: {stats.jobs_failed}")
```

## Monitoring & Observability

### Key Metrics to Track

1. **Worker Count**
   - Current workers vs. desired workers
   - Scale-up/down frequency
   - Time spent at MIN/MAX bounds

2. **Queue Metrics**
   - Queue depth over time
   - Queue wait time (time between submit and execution)
   - Queue drain rate

3. **Latency Metrics**
   - P50, P95, P99 job latency
   - Scale-up trigger frequency
   - Latency before vs. after scaling

4. **Utilization Metrics**
   - Worker utilization (active/total)
   - Idle worker percentage
   - Scale-down trigger frequency

5. **Cost Metrics**
   - Worker-hours per day
   - Cost per job
   - Cost during peak vs. off-peak

### Logging Scaling Decisions

Add logging to track autoscaler behavior:

```python
from src.scale.autoscaler import make_scale_decision
import logging

logger = logging.getLogger("autoscaler")

decision = make_scale_decision(state)

logger.info(
    f"Scale decision: {decision.direction.value} "
    f"(current={decision.current_workers}, desired={decision.desired_workers}) "
    f"reason: {decision.reason}"
)
```

Example log output:
```
[INFO] Scale decision: up (current=4, desired=6) reason: queue depth 100 > 50 (2.0x)
[INFO] Scale decision: hold (current=6, desired=6) reason: stable (queue=25, p95=1200ms, util=4/6)
[INFO] Scale decision: down (current=6, desired=5) reason: low load: utilization 33% < 70%
```

### Alerting Recommendations

Set up alerts for:

1. **Worker pool saturation**
   ```
   current_workers == MAX_WORKERS for > 5 minutes
   ```
   Action: Increase MAX_WORKERS or optimize job performance

2. **Queue backlog growth**
   ```
   queue_depth > TARGET_QUEUE_DEPTH * 3 for > 10 minutes
   ```
   Action: Check for downstream bottlenecks

3. **High failure rate**
   ```
   jobs_failed / jobs_completed > 0.10
   ```
   Action: Investigate job failures, check retry config

4. **Scaling thrashing**
   ```
   scale_decisions_per_minute > 5
   ```
   Action: Increase SCALE_DECISION_INTERVAL_MS

5. **High latency despite scaling**
   ```
   p95_latency > TARGET_P95_LATENCY_MS * 2 AND current_workers == MAX_WORKERS
   ```
   Action: Optimize job logic or increase MAX_WORKERS

## Troubleshooting

### Workers not scaling up

**Symptoms:** Queue depth high, latency high, but workers stay constant

**Checks:**
1. Verify MAX_WORKERS not reached: `current_workers < MAX_WORKERS`
2. Check cooldown active: Time since last scale < SCALE_DECISION_INTERVAL_MS
3. Verify metrics being collected correctly
4. Check logs for autoscaler decisions

**Solution:**
```bash
# Increase max workers
export MAX_WORKERS=20

# Reduce cooldown for faster reactions
export SCALE_DECISION_INTERVAL_MS=1000

# Check autoscaler is being called
# Add logging to your scale loop
```

### Workers not scaling down

**Symptoms:** Load drops but workers remain at peak levels

**Checks:**
1. Verify MIN_WORKERS not blocking: `current_workers > MIN_WORKERS`
2. Check scale-down conditions:
   - Queue depth > 30% of target
   - P95 latency > 50% of target
   - Utilization > 70%
3. Verify cooldown not blocking

**Solution:**
```bash
# Lower minimum if safe
export MIN_WORKERS=1

# Make scale-down more aggressive
export SCALE_DOWN_STEP=2

# Relax thresholds if too conservative
export TARGET_QUEUE_DEPTH=100
```

### Scaling thrashing

**Symptoms:** Workers rapidly scale up/down repeatedly

**Checks:**
1. Cooldown too short
2. Thresholds too sensitive
3. Metrics too noisy

**Solution:**
```bash
# Increase cooldown
export SCALE_DECISION_INTERVAL_MS=3000

# Wider thresholds
export TARGET_QUEUE_DEPTH=100
export TARGET_P95_LATENCY_MS=5000

# Smaller scaling steps
export SCALE_UP_STEP=1
export SCALE_DOWN_STEP=1
```

### Queue not draining

**Symptoms:** Queue depth grows despite available workers

**Checks:**
1. Jobs failing and retrying indefinitely
2. Downstream service down/rate-limited
3. Jobs too slow (long execution time)

**Solution:**
```bash
# Check job failure rate
# pool.get_stats().jobs_failed

# Reduce retries if jobs failing
export MAX_RETRIES=2

# Increase workers if jobs are slow
export MAX_WORKERS=30

# Check downstream service health
```

### High latency despite capacity

**Symptoms:** P95 latency high, workers idle, queue shallow

**Checks:**
1. Jobs themselves are slow (optimize job logic)
2. Downstream dependencies slow
3. Resource contention (CPU, memory, I/O)

**Solution:**
- Profile and optimize job functions
- Check downstream service latency
- Increase host resources
- Consider distributing across multiple hosts

### Workers stuck at MAX_WORKERS

**Symptoms:** Constant saturation, queue growing

**Checks:**
1. MAX_WORKERS too low for workload
2. Jobs too slow
3. Workload exceeds system capacity

**Solution:**
```bash
# Increase ceiling
export MAX_WORKERS=50

# Optimize job performance
# - Add indexes to database queries
# - Cache expensive computations
# - Use async I/O

# Consider horizontal scaling:
# - Deploy additional worker pools
# - Use regional distribution
```

## Best Practices

1. **Start conservative, tune gradually**
   - Begin with defaults
   - Monitor for 1-2 days
   - Adjust one parameter at a time

2. **Use presets for common patterns**
   - Low-latency: Higher MIN_WORKERS, lower thresholds
   - High-throughput: Lower MIN_WORKERS, higher thresholds
   - Balanced: Default configuration

3. **Monitor metrics continuously**
   - Track worker count, queue depth, latency
   - Set up alerts for anomalies
   - Review weekly for tuning opportunities

4. **Test scaling behavior**
   - Load test before production
   - Verify scale-up speed meets SLA
   - Ensure scale-down doesn't cause latency spikes

5. **Document your configuration**
   - Record why parameters were chosen
   - Note workload characteristics
   - Update when workload changes

6. **Plan for growth**
   - Set MAX_WORKERS below infrastructure limits
   - Leave headroom for unexpected spikes
   - Monitor trends to anticipate capacity needs

## References

- Implementation: `src/scale/autoscaler.py`
- Worker pool: `src/scale/worker_pool.py`
- Queue system: `src/queue/retry.py`
- Tests: `tests/test_autoscaler.py`
- Operations guide: `docs/OPERATIONS.md`
