# GitHub Actions Integration

## What this integrates

CI/CD automation workflows that run on push, PR, or schedule. Includes unit tests, Docker builds, database backups, and uptime checks. Some workflows are var-gated (only run if repository variable is enabled).

## Where it's configured

- `.github/workflows/ci.yml` - Main CI pipeline (tests, Docker validation)
- `.github/workflows/backup.yml` - Database backup (daily @ 09:00 UTC)
- `.github/workflows/uptime.yml` - Health check monitoring
- `.github/workflows/nightly.yml` - Extended test suite
- `.github/workflows/release.yml` - Release automation
- Repository Settings → Variables - Workflow control gates

## Env vars / secrets

| Name | Scope | Where set | Notes |
|------|-------|-----------|-------|
| `DATABASE_PUBLIC_URL` | backup.yml | Repository Secrets | For pg_dump access |
| `RAILWAY_TOKEN` | deploy.yml (if used) | Repository Secrets | Manual Railway deploys |
| `BACKUP_ENABLED` | backup.yml gate | Repository Variables | Set to "true" to enable daily backups |
| `UPTIME_ENABLED` | uptime.yml gate | Repository Variables | Set to "true" to enable monitoring |
| `GITHUB_TOKEN` | All workflows | Auto-provided | For artifact uploads, PR comments |

## How to verify (60 seconds)

```bash
# 1. View recent workflow runs
# Go to GitHub repo → Actions tab
# Should see recent runs for CI, Backup, etc.

# 2. Check workflow status badges (if in README)
# Green badge = passing, Red = failing

# 3. Trigger manual workflow
# Go to Actions → Select workflow → Run workflow button
# Select branch, click "Run workflow"

# 4. Check workflow logs
# Click on any workflow run → Expand job → View step logs

# 5. Verify var-gated workflows respect gates
# Go to Settings → Secrets and variables → Variables
# If BACKUP_ENABLED not set or "false", backup workflow should skip
```

## Common failure → quick fix

### Workflow not running after push
**Cause:** Workflow has var gate disabled or wrong branch trigger
**Fix:**
1. Check workflow file for `if:` conditions referencing vars
2. Go to Settings → Variables → Add missing var (e.g., `BACKUP_ENABLED=true`)
3. Or update workflow trigger from `main` to include your branch

### Workflow skipped (gray status)
**Cause:** Var gate evaluated to false
**Fix:**
- Check workflow file for `if: vars.SOME_VAR == 'true'`
- Go to Settings → Variables → Set `SOME_VAR` to `true`
- Re-run workflow

### Database backup failing
**Cause:** `DATABASE_PUBLIC_URL` secret missing or invalid
**Fix:**
1. Get correct DATABASE_URL from Railway → Postgres service → Connect
2. Go to GitHub Settings → Secrets → Update `DATABASE_PUBLIC_URL`
3. Manually trigger backup workflow to test

### Tests failing on CI but passing locally
**Cause:** Environment differences (Python version, missing deps, etc.)
**Fix:**
1. Check ci.yml matrix for Python version (currently 3.11)
2. Test locally with same version: `pyenv local 3.11`
3. Check for missing test dependencies in requirements.txt

## How to silence a workflow

To temporarily disable a workflow without deleting it:

**Option 1:** Add var gate to workflow file:
```yaml
if: vars.WORKFLOW_NAME_ENABLED == 'true'
```

**Option 2:** Comment out the trigger section:
```yaml
# on:
#   schedule:
#     - cron: '0 9 * * *'
```

**Option 3:** Disable workflow in GitHub UI:
- Go to Actions → Select workflow → "..." menu → "Disable workflow"

## References

- .github/workflows/ci.yml:1-12 - Main CI triggers (push/PR on main)
- .github/workflows/backup.yml:4-6 - Daily cron schedule (09:00 UTC)
- .github/workflows/backup.yml:57 - Restore drill conditional (monthly)
- .github/workflows/ci.yml:12-15 - Feature flags for CI environment
- backup.yml:38,87 - Usage of DATABASE_PUBLIC_URL secret
