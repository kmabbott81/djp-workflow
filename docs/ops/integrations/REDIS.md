# Redis Integration

## What this integrates

In-memory data store used for rate limiting, rollout controller circuit breaker state, and OAuth state management. Deployed as a Railway service connected to the Relay application.

## Where it's configured

- Railway Dashboard → Redis service (auto-provisioned)
- `src/rollout/controller.py` - Circuit breaker state storage
- `src/auth/oauth_state_context.py` - OAuth CSRF state with TTL
- `src/ratelimit/` (if present) - Token bucket rate limiting

## Env vars / secrets

| Name | Scope | Where set | Notes |
|------|-------|-----------|-------|
| `REDIS_URL` | Runtime | Railway Variables (auto) | Format: `redis://user:pass@host:port` |

## How to verify (60 seconds)

```bash
# 1. Test connection via redis-cli
redis-cli -u "$REDIS_URL" PING
# Returns: PONG

# 2. Check key count
redis-cli -u "$REDIS_URL" DBSIZE
# Returns: (integer) N

# 3. Inspect OAuth state keys (if any)
redis-cli -u "$REDIS_URL" --scan --pattern "oauth:state:*"
# Lists OAuth state keys with TTL

# 4. Check circuit breaker state
redis-cli -u "$REDIS_URL" --scan --pattern "rollout:circuit:*"
# Lists circuit breaker keys

# 5. Test set/get
redis-cli -u "$REDIS_URL" SET test_key "test_value" EX 10
redis-cli -u "$REDIS_URL" GET test_key
# Returns: "test_value"
```

## Common failure → quick fix

### Connection refused
**Cause:** REDIS_URL not set or incorrect format
**Fix:**
1. Check Railway → Relay service → Variables → REDIS_URL
2. Should match Railway → Redis service → Connect tab format
3. Update if mismatch: `redis://default:password@host:port`

### Timeout on connection
**Cause:** Redis service down or network issue
**Fix:**
1. Check Railway → Redis service status (should be green)
2. Restart Redis service if unhealthy
3. Check Railway → Relay logs for connection retry attempts

### OAuth state not found (user reports CSRF error)
**Cause:** State expired (TTL) or Redis flushed
**Fix:**
- OAuth states have 10-minute TTL (hardcoded)
- User must complete OAuth flow within 10 minutes
- If persistent issue, check Redis memory limits (Railway plan)

### Circuit breaker stuck open
**Cause:** Redis key not expiring or manual intervention needed
**Fix:**
```bash
# View circuit state
redis-cli -u "$REDIS_URL" GET "rollout:circuit:gmail"
# Manually reset if needed
redis-cli -u "$REDIS_URL" DEL "rollout:circuit:gmail"
```

## References

- src/rollout/controller.py - Circuit breaker uses Redis for shared state across instances
- src/auth/oauth_state_context.py - OAuth CSRF state stored with TTL
- Railway Redis Service - Managed Redis instance with automatic backups
- redis-py client - Used via `redis.from_url(os.getenv("REDIS_URL"))`
