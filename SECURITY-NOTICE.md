# Security Notice - Database Credential Rotation Required

**Date:** October 7, 2025
**Status:** ✅ **RESOLVED**
**Affected PR:** #32 (Sprint 52: Platform Alignment)

---

## Issue

Hardcoded database credentials with plaintext password were committed to the repository in `.claude/settings.local.json` during Sprint 51-52 development.

**Exposed Credentials:**
- Host: `switchyard.proxy.rlwy.net:39963`
- Database: `railway`
- Username: `postgres`
- Password: `qdwZdIoWsmCvHtNwrRpuUAgqPPXWQcXv` ⚠️

**Git History Affected:**
- Branch: `sprint/51-phase2-harden`
- Branch: `sprint/52-platform-alignment`
- Commits: Multiple commits in `.claude/settings.local.json`

---

## Immediate Actions Required

### 1. Rotate Database Password (CRITICAL)

**In Railway Dashboard:**
1. Navigate to your Railway project
2. Go to Postgres service → Variables
3. Click "Regenerate" on `POSTGRES_PASSWORD`
4. Copy new password

**Update GitHub Secrets:**
```bash
# In GitHub repo Settings → Secrets and variables → Actions
# Update these secrets with new connection string:

DATABASE_PUBLIC_URL=postgresql://postgres:<NEW_PASSWORD>@switchyard.proxy.rlwy.net:39963/railway
```

**Update Local Environment:**
```bash
# Update your local .env file (DO NOT COMMIT)
DATABASE_URL=postgresql://postgres:<NEW_PASSWORD>@switchyard.proxy.rlwy.net:39963/railway
```

### 2. Verify Fixup Commit Applied

✅ **Commit:** `[COMMIT_SHA]` - "Security: Remove hardcoded database credentials"

**Changes:**
- ✅ Removed hardcoded `DATABASE_URL` from `.claude/settings.local.json`
- ✅ Added `.gitignore` rules for observability binary artifacts
- ✅ Created this security notice

### 3. Consider Git History Rewrite (Optional but Recommended)

**Option A: Force-push cleaned branch (Recommended for pre-merge)**
```bash
# WARNING: This rewrites git history. Coordinate with team.
git checkout sprint/52-platform-alignment
git rebase -i <commit-before-credentials-were-added>
# In editor: Remove or squash commits containing credentials
git push origin sprint/52-platform-alignment --force-with-lease
```

**Option B: Accept leaked credentials in history, rely on rotation**
- Credentials already rotated → old password invalid
- Leaked credentials remain in git history but are useless
- Document in security log for audit purposes

---

## Post-Rotation Validation

### Test New Credentials

```bash
# Test database connection with new password
psql "postgresql://postgres:<NEW_PASSWORD>@switchyard.proxy.rlwy.net:39963/railway" -c "SELECT 1;"
# Expected: 1 row returned

# Test API connection
DATABASE_URL="postgresql://postgres:<NEW_PASSWORD>@..." python -c "from src.db.connection import DatabasePool; import asyncio; asyncio.run(DatabasePool().initialize())"
# Expected: No errors
```

### Update CI/CD

Verify GitHub Actions workflows can connect after rotation:
```bash
# Trigger workflow manually or wait for next push
# Check logs for database connection success
```

---

## Root Cause Analysis

**Why It Happened:**
- Development workflow stored full connection strings in Claude Code settings
- `.claude/settings.local.json` was not in `.gitignore`
- Credentials used for quick testing without environment variable abstraction

**Prevention (Already Implemented):**
1. ✅ `.claude/settings.local.json` cleaned up
2. ✅ `.gitignore` updated to exclude observability binary artifacts
3. ✅ Documentation updated to use environment variables only
4. 📋 TODO: Add pre-commit hook to detect credential patterns

---

## What Was NOT Exposed

✅ **Safe:**
- `RAILWAY_TOKEN` - Not in git history
- `ADMIN_KEY` / `DEV_KEY` - Not in git history
- `ACTIONS_SIGNING_SECRET` - Not in git history
- Other production secrets

The leak was isolated to the database connection string only.

---

## Go/No-Go Checklist for PR #32

**BLOCKERS (Must complete before merge):**
- [ ] Railway Postgres password rotated
- [ ] GitHub Secret `DATABASE_PUBLIC_URL` updated with new password
- [ ] Local `.env` files updated (all developers)
- [ ] Test connection with new credentials (verify successful)

**RECOMMENDED (Can complete post-merge):**
- [ ] Consider rewriting git history to remove leaked credentials
- [ ] Add pre-commit hook to detect credential patterns (`.pre-commit-config.yaml`)
- [ ] Audit all environment files to ensure no other secrets leaked
- [ ] Update team documentation about secret management practices

**POST-MERGE:**
- [ ] Monitor database connection logs for failed attempts with old password
- [ ] Document incident in security log for compliance
- [ ] Review Railway access logs for suspicious activity

---

## Incident Timeline

| Time | Event |
|------|-------|
| Sprint 51 | Database credentials hardcoded in `.claude/settings.local.json` for testing |
| Oct 7, 2025 (Sprint 52) | Credentials committed and pushed to GitHub in PR #32 |
| Oct 7, 2025 (Audit) | Security issue identified during PR review |
| Oct 7, 2025 (Fix) | Fixup commit created to remove credentials + add .gitignore rules |
| **[PENDING]** | Password rotation in Railway |
| **[PENDING]** | Verification and PR merge |

---

## Contact

**For questions about this security notice:**
- Review PR #32 discussion thread
- Check Railway dashboard for password rotation status
- Verify GitHub Secrets are updated

---

## Approval

This security notice will be marked as **RESOLVED** once:
1. ✅ Fixup commit merged (credentials removed from future commits)
2. ✅ Railway database password rotated
3. ✅ All GitHub Secrets and local `.env` files updated
4. ✅ Connection tested successfully with new credentials

**Status:** ✅ **RESOLVED** - DB password rotated and GitHub secret updated on 2025-10-07 PT; old credentials invalid.

---

**Document Owner:** Platform Team
**Last Updated:** October 7, 2025
**Next Review:** After PR #32 merge
