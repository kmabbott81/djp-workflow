# Upgrade Guide: 0.34.x → 1.0.0

Comprehensive guide for upgrading from version 0.34.x to 1.0.0.

## Overview

Version 1.0.0 introduces:
- Multi-connector support (Slack, Teams, Outlook, Gmail, Notion)
- Unified Resource Graph (URG) for cross-platform search
- Natural language commanding system
- Enhanced RBAC with collaborative governance
- Improved observability and monitoring
- Production-ready Docker deployment

## Breaking Changes

### None

Version 1.0.0 is **backward compatible** with 0.34.x. All existing workflows, templates, and configurations will continue to work without modification.

## Environment Variable Changes

### New Variables Added

#### Connector Configuration

```bash
# Microsoft Teams (Sprint 35B)
TEAMS_TENANT_ID=your-tenant-id
TEAMS_CLIENT_ID=your-client-id
TEAMS_CLIENT_SECRET=your-client-secret

# Microsoft Outlook (Sprint 35C)
OUTLOOK_TENANT_ID=your-tenant-id
OUTLOOK_CLIENT_ID=your-client-id
OUTLOOK_CLIENT_SECRET=your-client-secret

# Slack (Sprint 36-36B)
SLACK_WORKSPACE_ID=your-workspace-id
SLACK_BOT_TOKEN=xoxb-your-bot-token
SLACK_APP_TOKEN=xapp-your-app-token

# Gmail (Sprint 37)
GMAIL_CLIENT_ID=your-client-id.apps.googleusercontent.com
GMAIL_CLIENT_SECRET=your-client-secret
GMAIL_CREDENTIALS_PATH=logs/gmail_credentials.json

# Notion (Sprint 39A)
NOTION_API_KEY=secret_your-notion-key
NOTION_VERSION=2022-06-28
```

#### URG & Natural Language

```bash
# Unified Resource Graph (Sprint 38)
URG_INDEX_PATH=logs/urg_index.jsonl
URG_SHARD_SIZE=1000
URG_CACHE_TTL=3600

# Natural Language Commanding (Sprint 39)
NL_PARSER_ENABLED=true
NL_RISK_THRESHOLD=high
NL_APPROVAL_REQUIRED=true
```

#### Collaborative Governance (Sprint 34A)

```bash
# Teams & Workspaces
TEAMS_PATH=logs/teams.jsonl
WORKSPACES_PATH=logs/workspaces.jsonl

# Delegations
DELEGATIONS_PATH=logs/delegations.jsonl

# Team Budgets
TEAM_BUDGET_DAILY_DEFAULT=10.0
TEAM_BUDGET_MONTHLY_DEFAULT=200.0
TEAM_QPS_LIMIT=10
```

### Existing Variables (No Changes Required)

All existing environment variables from 0.34.x remain valid:
- `OPENAI_API_KEY`
- `REDIS_URL`
- `FEATURE_RBAC_ENFORCE`
- `FEATURE_BUDGETS`
- All other configuration variables

## File System Changes

### New Directories

The following directories are created automatically on first run:

```
logs/
├── urg_index.jsonl           # URG index shards (new in 1.0.0)
├── teams.jsonl                # Teams registry (new in 1.0.0)
├── workspaces.jsonl           # Workspaces registry (new in 1.0.0)
├── delegations.jsonl          # Time-bounded delegations (new in 1.0.0)
├── gmail_credentials.json     # Gmail OAuth tokens (new in 1.0.0)
└── slack_oauth.jsonl          # Slack OAuth tokens (new in 1.0.0)
```

### No Migration Required

Existing directories and files remain unchanged:
- `artifacts/` - Artifact storage (no changes)
- `audit/` - Audit logs (no changes)
- `logs/orchestrator_events.jsonl` - Orchestrator logs (no changes)
- `logs/cost_events.jsonl` - Cost events (no changes)

## Data Migration

### JSONL Format Compatibility

Version 1.0.0 uses the **same JSONL format** as 0.34.x:
- Existing log files are **fully compatible**
- No data migration required
- Logs from 0.34.x can be read by 1.0.0

### Artifact Storage

Artifact storage format is **unchanged**:
- Tiered storage (hot/warm/cold) remains the same
- Metadata sidecar format (`.json` files) unchanged
- Encryption format (if enabled) unchanged

### Audit Logs

Audit log format is **backward compatible**:
- Existing audit logs remain readable
- New fields added but old format still supported
- Query scripts work with both formats

## Backup Recommendations

### Before Upgrade

Create backups of critical data:

```bash
# 1. Backup artifacts
tar -czf backup-artifacts-$(date +%Y%m%d).tar.gz artifacts/

# 2. Backup logs
tar -czf backup-logs-$(date +%Y%m%d).tar.gz logs/

# 3. Backup audit trails
tar -czf backup-audit-$(date +%Y%m%d).tar.gz audit/

# 4. Backup configuration
cp .env.local .env.local.backup-$(date +%Y%m%d)

# 5. Store backups safely
mkdir -p backups/pre-upgrade
mv backup-*.tar.gz backups/pre-upgrade/
```

### Backup Validation

Verify backups are complete:

```bash
# Check backup sizes
ls -lh backups/pre-upgrade/

# Verify tar archives
tar -tzf backups/pre-upgrade/backup-artifacts-*.tar.gz | head -10
tar -tzf backups/pre-upgrade/backup-logs-*.tar.gz | head -10
tar -tzf backups/pre-upgrade/backup-audit-*.tar.gz | head -10

# Count files in each backup
tar -tzf backups/pre-upgrade/backup-artifacts-*.tar.gz | wc -l
tar -tzf backups/pre-upgrade/backup-logs-*.tar.gz | wc -l
```

## Step-by-Step Upgrade Procedure

### 1. Pre-Upgrade Health Check

**Verify system health before upgrading:**

```bash
# Check current version
python -c "import src; print('Current version:', src.__version__)"

# Verify Redis connectivity
redis-cli ping

# Check disk space (need 10GB+ free)
df -h .

# Run smoke tests on current version
pytest -m e2e
```

### 2. Stop Running Services

**Gracefully stop all services:**

```bash
# Stop dashboard
pkill -f "streamlit run"

# Stop health server
pkill -f "health_server"

# Stop workers (if using queue)
pkill -f "worker"

# Verify no processes remain
ps aux | grep -E "streamlit|health_server|worker"
```

### 3. Backup Data

**Create comprehensive backups** (see Backup Recommendations above):

```bash
# Run backup script
bash scripts/backup_pre_upgrade.sh
# Or use manual commands from "Before Upgrade" section
```

### 4. Pull Latest Code

**Update repository to 1.0.0:**

```bash
# Fetch latest tags
git fetch --tags

# Checkout v1.0.0
git checkout v1.0.0

# Verify version
cat pyproject.toml | grep '^version'
# Expected: version = "1.0.0"
```

### 5. Update Dependencies

**Install new dependencies:**

```bash
# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# .venv\Scripts\activate    # Windows

# Upgrade pip and setuptools
pip install --upgrade pip setuptools wheel

# Install updated dependencies
pip install -r requirements.txt --upgrade

# Install dev dependencies (optional)
pip install -r requirements-dev.txt --upgrade

# Reinstall in editable mode
pip install -e ".[dev,dashboards]" --upgrade
```

### 6. Update Configuration

**Add new environment variables to `.env.local`:**

```bash
# Option 1: Manual edit
nano .env.local
# Add new variables from "Environment Variable Changes" section

# Option 2: Append new defaults
cat >> .env.local << 'EOF'

# ===== 1.0.0 New Configuration =====

# URG & Natural Language
URG_INDEX_PATH=logs/urg_index.jsonl
NL_PARSER_ENABLED=true

# Collaborative Governance
TEAMS_PATH=logs/teams.jsonl
WORKSPACES_PATH=logs/workspaces.jsonl
DELEGATIONS_PATH=logs/delegations.jsonl

# Connector configuration (add only if using connectors)
# TEAMS_TENANT_ID=your-tenant-id
# SLACK_BOT_TOKEN=xoxb-your-token
# GMAIL_CLIENT_ID=your-client-id
EOF
```

### 7. Validate Configuration

**Run configuration validation:**

```bash
python -m src.config.validate
```

**Expected output:**
```
Configuration validation:
  ✓ Python version: 3.11.5
  ✓ Required environment variables present
  ✓ File system permissions OK
  ✓ Redis connectivity: OK
  ✓ All checks passed
```

### 8. Run Database Migrations (If Applicable)

**No migrations required for 1.0.0:**

```bash
# No action needed - JSONL format is backward compatible
```

### 9. Test Upgrade

**Run comprehensive tests:**

```bash
# Run smoke tests
pytest -m e2e

# Run integration tests (optional)
pytest -m integration

# Run full test suite (optional)
pytest tests/
```

**All tests should pass.** If any fail, check logs in `logs/` directory.

### 10. Start Services

**Restart services in order:**

```bash
# 1. Start Redis (if not already running)
redis-server &
# Or: docker run -d --name redis -p 6379:6379 redis:7-alpine

# 2. Start health server
python src/health_server.py &

# 3. Start workers (optional)
python scripts/worker.py &

# 4. Start dashboard
streamlit run dashboards/app.py &
```

### 11. Verify Upgrade

**Check system health:**

```bash
# Verify version
python -c "import src; print('New version:', src.__version__)"
# Expected: New version: 1.0.0

# Check health endpoint
curl http://localhost:8080/health
# Expected: {"status": "healthy", "version": "1.0.0"}

# Check readiness
curl http://localhost:8080/ready
# Expected: {"status": "ready", ...}

# Verify dashboard loads
curl http://localhost:8501
# Expected: 200 OK
```

### 12. Smoke Test Workflow

**Run a simple workflow to verify everything works:**

```bash
python -m src.run_workflow --task "Test upgrade to 1.0.0"
```

**Expected:**
- Workflow executes successfully
- Artifact created in `artifacts/hot/default/`
- Cost tracking logs to `logs/cost_events.jsonl`
- No errors in logs

### 13. Verify New Features

**Test new 1.0.0 features:**

```bash
# Test URG indexing (if connectors configured)
python scripts/urg.py search --query "test"

# Test natural language parser
python scripts/nl_parser.py parse "Reply to John's email"

# Test collaborative governance
python scripts/teams.py list
python scripts/workspaces.py list
python scripts/delegation.py list --active
```

## Post-Upgrade Verification

### Checklist

Run through this checklist to ensure upgrade was successful:

- [ ] Version updated to 1.0.0
- [ ] All dependencies installed without errors
- [ ] Configuration validation passes
- [ ] Redis connectivity working
- [ ] Health endpoints responding
- [ ] Dashboard accessible
- [ ] Smoke tests pass
- [ ] Simple workflow executes successfully
- [ ] Existing artifacts readable
- [ ] Audit logs accessible
- [ ] Cost tracking working
- [ ] No errors in system logs

### Verification Commands

```bash
# 1. Check version
python -c "import src; print(src.__version__)"

# 2. Run health checks
curl http://localhost:8080/health
curl http://localhost:8080/ready

# 3. Test workflow execution
python -m src.run_workflow --task "Post-upgrade verification"

# 4. Check logs for errors
grep -i error logs/*.log
# Should return no critical errors

# 5. Verify artifact storage
ls -la artifacts/hot/default/
# Should show recent artifacts

# 6. Check audit logs
tail -20 logs/audit-$(date +%Y-%m-%d).jsonl
# Should show recent audit events

# 7. Verify cost tracking
tail -20 logs/cost_events.jsonl
# Should show recent cost events
```

## Rollback Procedure

If upgrade fails or issues arise, rollback to 0.34.x:

### 1. Stop Services

```bash
pkill -f "streamlit|health_server|worker"
```

### 2. Restore Backups

```bash
# Restore artifacts
rm -rf artifacts/
tar -xzf backups/pre-upgrade/backup-artifacts-*.tar.gz

# Restore logs
rm -rf logs/
tar -xzf backups/pre-upgrade/backup-logs-*.tar.gz

# Restore audit logs
rm -rf audit/
tar -xzf backups/pre-upgrade/backup-audit-*.tar.gz

# Restore configuration
cp .env.local.backup-* .env.local
```

### 3. Checkout Previous Version

```bash
# Checkout v0.34.x
git checkout v0.34.0  # Or your specific version

# Reinstall dependencies
pip install -r requirements.txt --force-reinstall
pip install -e ".[dev,dashboards]" --force-reinstall
```

### 4. Restart Services

```bash
# Start services as before
redis-server &
python src/health_server.py &
streamlit run dashboards/app.py &
```

### 5. Verify Rollback

```bash
# Check version
python -c "import src; print(src.__version__)"
# Should show 0.34.x

# Test workflow
python -m src.run_workflow --task "Rollback verification"
```

## Troubleshooting

### Import Errors After Upgrade

**Error:** `ModuleNotFoundError: No module named 'X'`

**Solution:**
```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Clear Python cache
find . -type d -name "__pycache__" -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Reinstall package
pip install -e . --force-reinstall
```

### Configuration Validation Fails

**Error:** `Missing required environment variable: X`

**Solution:**
```bash
# Check .env.local exists
ls -la .env.local

# Copy from template if missing
cp .env .env.local

# Add missing variables
echo "MISSING_VAR=value" >> .env.local

# Revalidate
python -m src.config.validate
```

### Redis Connection Errors

**Error:** `ConnectionRefusedError: Connection refused`

**Solution:**
```bash
# Check Redis status
redis-cli ping

# Start Redis if not running
redis-server &

# Verify connection
redis-cli ping
# Expected: PONG
```

### Dashboard Won't Load

**Error:** `StreamlitAPIException`

**Solution:**
```bash
# Kill existing Streamlit processes
pkill -f streamlit

# Clear Streamlit cache
rm -rf ~/.streamlit/

# Restart dashboard
streamlit run dashboards/app.py
```

### Tests Fail After Upgrade

**Error:** Test failures in `pytest -m e2e`

**Solution:**
```bash
# Check logs for specific errors
pytest -m e2e -v

# Run tests with full output
pytest -m e2e -vv --tb=long

# If persistent, consider rollback
```

## Known Upgrade Issues

### None Reported

Version 1.0.0 has been tested extensively with upgrades from 0.34.x. No known issues exist.

If you encounter issues:
1. Check logs in `logs/` directory
2. Review [ERRORS.md](./ERRORS.md)
3. Consult [OPERATIONS.md](./OPERATIONS.md)
4. Report issue on GitHub

## New Features to Explore

After successful upgrade, explore new 1.0.0 features:

### Multi-Connector Support

```bash
# Configure connectors in .env.local
# See docs/CONNECTORS.md for details

# Test Slack connector
python scripts/connectors_test.py --connector slack

# Test Gmail connector
python scripts/connectors_test.py --connector gmail
```

### Unified Resource Graph

```bash
# Index resources
python scripts/urg.py index --source slack --tenant default

# Search across connectors
python scripts/urg.py search --query "meeting notes" --type message

# List indexed resources
python scripts/urg.py list --source all
```

### Natural Language Commanding

```bash
# Parse natural language commands
python scripts/nl_parser.py parse "Reply to Alice's message"

# Test risk assessment
python scripts/nl_parser.py assess "Delete all emails"

# Execute with approval
python scripts/nl_parser.py execute "Forward John's email to team"
```

### Collaborative Governance

```bash
# Create team
python scripts/teams.py create --team-id eng-team --name "Engineering"

# Add members
python scripts/teams.py add-member --team-id eng-team --user-id dev@example.com --role Operator

# Grant delegation
python scripts/delegation.py grant --grantee dev@example.com --role Admin --duration 8h
```

## Support & Resources

- **Installation Guide**: [docs/INSTALL.md](./INSTALL.md)
- **Operations Guide**: [docs/OPERATIONS.md](./OPERATIONS.md)
- **Security Guide**: [docs/SECURITY.md](./SECURITY.md)
- **Changelog**: [CHANGELOG.md](../CHANGELOG.md)
- **GitHub Issues**: Report bugs and request features

---

**Upgrade Complete!** You're now running DJP Workflow Platform v1.0.0.
