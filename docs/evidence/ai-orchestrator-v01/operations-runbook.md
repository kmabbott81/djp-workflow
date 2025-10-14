# Operations Runbook - AI Orchestrator v0.1

**Sprint 55 Week 3**

## Deployment

### Prerequisites
- Redis instance (6.x or later) with persistence enabled
- PostgreSQL database (for audit logs)
- Environment variables configured (see below)

### Environment Variables

```bash
# Required
REDIS_URL=redis://default:password@host:6379
ACTIONS_ENABLED=true
ALLOW_ACTIONS_DEFAULT=gmail.send,outlook.send,task.create

# Optional (defaults shown)
AI_MODEL=gpt-4o-mini
AI_MAX_OUTPUT_TOKENS=800
```

### Deployment Steps

1. **Verify Redis connectivity:**
   ```bash
   redis-cli -u $REDIS_URL ping
   # Expected: PONG
   ```

2. **Run database migrations:**
   ```bash
   alembic upgrade head
   ```

3. **Start application:**
   ```bash
   uvicorn src.webapi:app --port 8000 --workers 4
   ```

4. **Health check:**
   ```bash
   curl http://localhost:8000/ready
   # Expected: {"ready": true, "checks": {...}}
   ```

## Monitoring

### Key Metrics

**Queue Health:**
- `ai_queue_depth_total` - Pending jobs (alert if > 1000)
- `ai_queue_enqueue_total` - Jobs submitted per second
- `ai_queue_dequeue_total` - Jobs processed per second

**API Health:**
- `http_requests_total{path="/ai/jobs"}` - Request count
- `http_request_duration_seconds{path="/ai/jobs"}` - Latency (p95 < 200ms)
- `http_requests_total{status="5xx"}` - Error rate (alert if > 1%)

### Prometheus Alerts

```yaml
# Alert if queue depth exceeds capacity
- alert: AIQueueDepthHigh
  expr: ai_queue_depth_total > 1000
  for: 5m
  annotations:
    summary: "AI job queue depth high ({{ $value }} jobs pending)"

# Alert if job processing stalls
- alert: AIJobProcessingStalled
  expr: rate(ai_queue_dequeue_total[5m]) == 0 AND ai_queue_depth_total > 0
  for: 10m
  annotations:
    summary: "AI job processing stalled ({{ $value }} jobs stuck)"
```

## Troubleshooting

### Issue: Jobs stuck in pending state

**Symptoms:** `ai_queue_depth_total` increasing, `ai_queue_dequeue_total` zero

**Diagnosis:**
```bash
# Check Redis connection
redis-cli -u $REDIS_URL LLEN ai:queue:pending

# Check worker status
curl http://localhost:8000/metrics | grep ai_queue_workers
```

**Resolution:**
1. Verify Redis is reachable: `redis-cli -u $REDIS_URL ping`
2. Check worker logs for exceptions
3. Restart application if workers are deadlocked

### Issue: High error rate on /ai/jobs

**Symptoms:** `http_requests_total{status="500"}` spiking

**Diagnosis:**
```bash
# Check application logs
tail -f logs/app.log | grep ERROR

# Check Redis memory usage
redis-cli -u $REDIS_URL INFO memory
```

**Resolution:**
1. If Redis OOM: Increase maxmemory or enable eviction policy
2. If auth failures: Verify API keys in database
3. If workspace isolation broken: Check `require_scopes` decorator

### Issue: Duplicate job execution despite idempotency

**Symptoms:** Same `client_request_id` processed twice

**Diagnosis:**
```bash
# Check idempotency key TTL
redis-cli -u $REDIS_URL TTL ai:idempotency:ws-123:req-456
```

**Resolution:**
1. Verify client is sending unique `client_request_id` per logical request
2. Check Redis SET NX command is atomic
3. Increase TTL if clients retry slowly (current: 24 hours)

## Maintenance

### Regular Tasks

**Daily:**
- Review error logs for patterns
- Check queue depth trends (should stay under 100)

**Weekly:**
- Review audit logs for anomalous activity
- Verify Redis persistence (check last save time)

**Monthly:**
- Rotate Redis password (update REDIS_URL and restart)
- Archive old audit logs (> 90 days)

### Backup & Recovery

**Redis Backup:**
```bash
# Manual snapshot
redis-cli -u $REDIS_URL BGSAVE

# Verify snapshot
redis-cli -u $REDIS_URL LASTSAVE
```

**Database Backup:**
```bash
# Backup audit logs
pg_dump -t action_audit -U postgres dbname > audit_backup.sql
```

## Performance Tuning

### Redis Optimization
- **Persistence:** Use AOF with `appendfsync everysec` for balance
- **Memory:** Set `maxmemory-policy allkeys-lru` to auto-evict old jobs
- **Connection Pool:** Use 10 connections per worker process

### Application Optimization
- **Workers:** Scale to 4 workers per CPU core
- **Timeouts:** Set Redis command timeout to 5s
- **Rate Limits:** Enable per-workspace limits (100 req/min default)

---

*Operations runbook tested in staging. All scenarios validated with chaos testing.*
