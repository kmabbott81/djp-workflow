# Rollout Controller - GitHub Actions Failure Fix

**Date:** 2025-10-09
**Issue:** GitHub Actions rollout controller failing every 10 minutes
**Root Cause:** Prometheus and Redis on private Railway network, unreachable from GitHub-hosted runners
**Status:** ✅ FIXED

## What Was Happening

The rollout controller workflow was failing because:

1. **Private Network:** Prometheus and Redis are on Railway's internal network (`*.railway.internal`)
2. **No Public Access:** GitHub-hosted runners cannot reach internal Railway services
3. **Loud Failure by Design:** Controller exits with code 1 when infrastructure is unreachable (guardrail)
4. **Email Spam:** GitHub Actions sends failure emails every 10 minutes

## Fix Applied

### 1. Added Preflight Checks

Updated `.github/workflows/rollout-controller.yml` to:
- Check if Prometheus and Redis are reachable before running controller
- Skip cleanly (exit 0) if infrastructure not accessible
- Provide helpful message explaining why skip happened

### 2. Added Enable Gate

Added `ROLLOUT_CONTROLLER_ENABLED` gate variable:
- Workflow only runs if `vars.ROLLOUT_CONTROLLER_ENABLED == 'true'`
- Allows easy disable without modifying workflow file
- Default: Not set (workflow will not run)

### 3. Improved Error Messages

When skipped, workflow now explains:
- Why it was skipped (e.g., "Prometheus not reachable from GitHub runner")
- Expected scenarios (private network, initial setup)
- Options to fix (deploy as Railway worker, use self-hosted runner, expose publicly)

## How to Stop Email Spam Immediately

### Option A: Disable the Workflow (Recommended for Now)

In GitHub repo:
1. Go to **Settings → Variables → Actions → Variables**
2. Don't create `ROLLOUT_CONTROLLER_ENABLED` (or set it to `false`)
3. Workflow will not run until you explicitly enable it

### Option B: Let It Skip Cleanly

With the updated workflow (this PR), the workflow will:
- Run preflight checks
- Detect Prometheus/Redis not reachable
- Skip cleanly with exit 0 (no email)
- Show helpful message in logs

## Long-Term Solutions

### Solution 1: Deploy Controller as Railway Worker (Recommended)

**Pros:**
- Same network as Prometheus/Redis
- Always running, no cold starts
- No GitHub Actions limitations

**How:**
```bash
# In railway.json or Procfile
worker: python scripts/rollout_controller.py --interval 600

# Or use Railway cron trigger
# Create new service: "rollout-controller"
# Start command: python scripts/rollout_controller.py
# Schedule: */10 * * * * (every 10 minutes)
```

### Solution 2: Use Self-Hosted GitHub Runner

**Pros:**
- Keeps controller in GitHub Actions
- Can reach private network

**How:**
1. Deploy GitHub Actions runner on Railway or in your VPC
2. Runner has access to internal network
3. Workflow works as-is

### Solution 3: Expose Prometheus/Redis Publicly

**Pros:**
- GitHub-hosted runners can reach them

**Cons:**
- Security risk (need IP allowlisting)
- More complex setup

**Not Recommended** for this use case.

## Current Workflow Behavior

### Before This Fix
```
Schedule triggers → Check Prometheus → UNREACHABLE → exit(1) → ❌ Workflow fails → 📧 Email sent
```

### After This Fix
```
Schedule triggers → Check if enabled → NO → ⏭️ Workflow skipped (no run)
                                    ↓ YES
                    → Preflight check → Infrastructure unreachable? → ⏭️ Skip cleanly (exit 0) → No email
                                                                    ↓ NO
                    → Run controller → Success/Fail → Email only on real failure
```

## Recommended Next Steps

**Immediate (Stop Email Spam):**
1. ✅ Merge this PR (adds preflight checks)
2. ⏳ Set `ROLLOUT_CONTROLLER_ENABLED=false` in GitHub Actions variables (or don't set it)
3. ✅ Email spam stops

**Short-Term (E2E Testing):**
4. ⏳ For Phase 3 E2E testing, run controller manually on your local machine:
   ```bash
   export REDIS_URL="redis://..."
   export PROMETHEUS_BASE_URL="http://localhost:9090"  # or Railway internal URL via tunnel
   export ROLLOUT_DRY_RUN=true
   python scripts/rollout_controller.py
   ```
5. ⏳ Or run as Railway worker for 24-48 hour observation period

**Long-Term (Production):**
6. ⏳ Deploy controller as Railway worker service
7. ⏳ Set up proper monitoring/alerting
8. ⏳ Disable GitHub Actions workflow (no longer needed)

## Files Modified

**Modified:**
- `.github/workflows/rollout-controller.yml` - Added preflight checks and enable gate

**Created:**
- `docs/specs/ROLLOUT-CONTROLLER-FIX.md` - This document

## Testing the Fix

### Test 1: Preflight Skip (Clean)

```bash
# Simulate from local environment
export PROMETHEUS_BASE_URL="http://unreachable.example.com"
export REDIS_URL="redis://unreachable.example.com:6379"

# Run workflow step manually
curl -fsS --max-time 10 "$PROMETHEUS_BASE_URL/-/ready" || echo "SKIP: Prometheus unreachable"
# Should print: SKIP: Prometheus unreachable
# Exit code: 0 (clean)
```

### Test 2: Preflight Pass (Run Controller)

```bash
# With real infrastructure
export PROMETHEUS_BASE_URL="http://localhost:9090"
export REDIS_URL="redis://localhost:6379"

curl -fsS --max-time 10 "$PROMETHEUS_BASE_URL/-/ready" && echo "OK: Prometheus reachable"
# Should print: OK: Prometheus reachable
# Proceeds to run controller
```

## GitHub Actions Variables Needed

**Variables (Settings → Variables → Actions):**
- `ROLLOUT_CONTROLLER_ENABLED` - Set to `true` to enable workflow (default: not set/false)
- `PROMETHEUS_BASE_URL` - Prometheus server URL (required if enabled)
- `ROLLOUT_DRY_RUN` - Set to `true` for dry-run mode (optional, default: false)
- `PUSHGATEWAY_URL` - Pushgateway URL for telemetry (optional)

**Secrets (Settings → Secrets → Actions):**
- `REDIS_URL` - Redis connection string (required if enabled)

## Monitoring After Fix

After merging this PR:

1. **Check Workflow Runs:**
   - Go to Actions → Rollout Controller
   - Should see "skipped" status (not failed)
   - No more failure emails

2. **Check Logs (if run attempted):**
   - Should see: "⏭️ Skipping controller run: Prometheus not reachable from GitHub runner"
   - Explains why it was skipped

3. **Verify No Emails:**
   - GitHub should not send failure notifications for clean skips

## Summary

- ✅ **Fixed:** Workflow now skips cleanly when infrastructure unreachable
- ✅ **Fixed:** Added enable gate to disable workflow easily
- ✅ **Improved:** Better error messages explaining why skip happened
- ⏳ **Next:** Decide long-term solution (Railway worker recommended)
- ✅ **Result:** No more email spam

---

**Recommendation:** For Phase 3 E2E testing, run the controller locally or as a Railway worker. For production, deploy as a Railway worker service to avoid GitHub Actions limitations with private networks.
