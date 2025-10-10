# Redis Setup Instructions - Railway Production

**Sprint 53 - Infrastructure Foundation**
**Date:** October 8, 2025

---

## Manual Setup via Railway Dashboard

Railway CLI `add` command is interactive and doesn't work well in automated scripts. Follow these steps in the Railway dashboard:

### Step 1: Add Redis Service

1. Go to https://railway.app/project/[your-project-id]
2. Click "**+ New**" button in the top right
3. Select "**Database**"
4. Choose "**Redis**"
5. Railway will provision a managed Redis instance (usually takes 1-2 minutes)

### Step 2: Get Connection Details

Once Redis is provisioned:

1. Click on the Redis service in your Railway project
2. Go to "**Variables**" tab
3. Copy the following automatically-generated variables:
   - `REDIS_URL` - Full connection string
   - `REDIS_PRIVATE_URL` - Internal network URL (use this if both services in same project)

**Format:** `redis://default:<password>@<host>:<port>`

### Step 3: Add REDIS_URL to Backend Service

1. Click on your "**Relay**" backend service
2. Go to "**Variables**" tab
3. Click "**+ New Variable**"
4. Add:
   ```
   Variable: REDIS_URL
   Value: redis://default:<password>@<host>:<port>
   ```

   **Option A:** Use `REDIS_PRIVATE_URL` from Redis service (recommended - internal network)
   **Option B:** Use `REDIS_URL` if external connection needed

4. Click "**Add**"
5. Railway will automatically redeploy the backend with new environment variable

### Step 4: Verify Connection

After backend redeploys (usually 2-3 minutes):

1. Check backend logs:
   ```bash
   railway logs --service Relay
   ```

2. Look for log line: `Redis connected: <host>:<port>`

3. Test via API:
   ```bash
   curl https://relay-production-f2a6.up.railway.app/ready
   ```

   Should return:
   ```json
   {
     "ready": true,
     "checks": {
       "telemetry": true,
       "templates": true,
       "filesystem": true,
       "redis": true
     }
   }
   ```

---

## Expected Configuration

**Redis Version:** 7.x (Railway managed)

**Configuration:**
- Max memory: 512MB (Railway default)
- Eviction policy: `allkeys-lru` (recommended for cache)
- Persistence: Enabled (AOF)
- Network: Private within Railway project

**Environment Variables (Backend):**
```bash
REDIS_URL=redis://default:<password>@redis.railway.internal:6379
REDIS_ENABLED=true
RATE_LIMIT_ENABLED=true
```

---

## Verification Checklist

After setup, verify:

- [ ] Redis service shows "Active" status in Railway dashboard
- [ ] Backend service has `REDIS_URL` environment variable set
- [ ] Backend redeploy completed successfully
- [ ] Backend logs show "Redis connected" message
- [ ] `/ready` endpoint includes `"redis": true` in checks
- [ ] Rate limit headers (`X-RateLimit-*`) present in API responses

---

## Troubleshooting

### Issue: Backend can't connect to Redis

**Symptoms:** Logs show "Redis connection failed" or "Using in-process rate limiter"

**Solutions:**
1. Verify `REDIS_URL` format is correct (redis://...)
2. Check Redis service is "Active" in Railway
3. Ensure both services are in same Railway project (for private networking)
4. Try using `REDIS_PRIVATE_URL` instead of `REDIS_URL`

### Issue: Rate limiting not working

**Symptoms:** No `X-RateLimit-*` headers in responses

**Check:**
1. `RATE_LIMIT_ENABLED=true` is set
2. Redis connection is successful
3. Backend logs show "Rate limiter mode: redis"

### Issue: Redis connection timeout

**Solutions:**
1. Increase connection timeout in backend (currently 5s)
2. Check Railway network status
3. Verify firewall rules if using external URL

---

## Security Notes

**DO NOT:**
- ❌ Commit `REDIS_URL` to git
- ❌ Share Redis password in public docs
- ❌ Use Redis public URL if private URL works

**DO:**
- ✅ Use Railway's private networking (`REDIS_PRIVATE_URL`)
- ✅ Set reasonable connection timeouts
- ✅ Monitor Redis memory usage
- ✅ Enable Redis AUTH (automatic in Railway)

---

## Next Steps

After Redis is connected:

1. Run backend verification: `railway run python scripts/verify_redis.py`
2. Check Prometheus metrics: `redis_connected{instance="..."}`
3. Test rate limiting with multiple requests
4. Document results in `REDIS-CONNECT.txt`

---

**Setup Time:** ~5-10 minutes
**Status:** Pending Kyle's action
**Blocker:** None (manual setup straightforward)
