# GitHub Integration

## What this integrates

Source control and collaboration hub for the repository. Connected to Railway for automatic deployments on push to `main`. Hosts GitHub Actions workflows for CI/CD, backups, and uptime monitoring.

## Where it's configured

- `.github/workflows/*.yml` - CI/CD automation workflows
- Repository Settings → Branches - Branch protection rules
- Repository Settings → Webhooks - Railway deployment webhook
- Pull request templates (if present)

## Env vars / secrets

| Name | Scope | Where set | Notes |
|------|-------|-----------|-------|
| `GITHUB_TOKEN` | GitHub Actions | Auto-provided by GitHub | Read-only access to repo |
| `DATABASE_PUBLIC_URL` | GitHub Actions | Repository Secrets | For backup workflow |
| `RAILWAY_TOKEN` | GitHub Actions | Repository Secrets | For manual Railway operations (if needed) |

## How to verify (60 seconds)

```bash
# 1. Check Railway webhook connection
# Go to Railway dashboard → Relay service → Settings → Source
# Should show: Connected to GitHub, tracking main branch

# 2. Verify recent deploys triggered by pushes
# Go to Railway → Deployments tab
# Recent deployments should have "Triggered by GitHub push" messages

# 3. Check GitHub Actions are enabled
# Go to GitHub repo → Actions tab
# Should see workflow runs (CI, Backup, etc.)

# 4. Test push triggers deployment
git commit --allow-empty -m "test: trigger deployment"
git push origin main
# Watch Railway Deployments tab - new build should start within 30s
```

## Common failure → quick fix

### Push to main but no Railway deployment
**Cause:** Railway GitHub connection disconnected
**Fix:**
1. Go to Railway → Relay service → Settings → Source
2. Click "Disconnect" then "Connect to GitHub"
3. Select repository and `main` branch
4. Verify connection shows green check

### Cannot push to main (protected branch)
**Cause:** Branch protection rules require PR or checks
**Fix:**
- Create feature branch: `git checkout -b feat/my-feature`
- Push feature branch: `git push origin feat/my-feature`
- Create PR via GitHub UI

### PR status checks failing
**Cause:** CI workflow found test failures or linting issues
**Fix:**
1. Go to PR → Checks tab
2. Expand failing check to see error logs
3. Fix issues locally, push to PR branch
4. Checks will re-run automatically

### Webhook delivery failing (Railway)
**Cause:** Railway service unreachable or webhook secret mismatch
**Fix:**
1. Go to Railway → Service logs
2. Check for incoming webhook requests
3. If missing, re-connect GitHub in Railway settings

## References

- .github/workflows/ci.yml:1-129 - Main CI/CD pipeline
- .github/workflows/backup.yml:1-106 - Database backup automation
- Repository → Settings → Branches - Branch protection configured for `main`
- Railway Relay Settings → Source - GitHub connection configuration
