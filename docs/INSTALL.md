# Installation & Quickstart Guide

Production-ready installation guide for DJP Workflow Platform v1.0+.

## Prerequisites

### Required
- **Python**: 3.9 or higher (3.11+ recommended)
- **Redis**: 6.2+ for queue backend
- **Git**: For repository cloning

### Optional
- **Docker & Docker Compose**: For containerized deployment
- **PostgreSQL**: For metadata storage (future)

### System Requirements
- **RAM**: Minimum 2GB, 4GB+ recommended for production
- **Disk**: 10GB+ free space for artifacts and logs
- **OS**: Windows 10/11, macOS 10.15+, Linux (Ubuntu 20.04+, Debian 11+, RHEL 8+)

## Quick Install (5 Minutes)

### 1. Clone Repository

```bash
git clone https://github.com/kmabbott81/djp-workflow.git
cd djp-workflow
```

### 2. Validate Configuration

Before installing dependencies, validate your environment:

```bash
python -m src.config.validate
```

This checks for:
- Required Python version
- Environment variable configuration
- File system permissions
- Network connectivity (if applicable)

### 3. Install Dependencies

**Create virtual environment:**

```bash
# Windows PowerShell
python -m venv .venv
.venv\Scripts\activate

# macOS/Linux
python3 -m venv .venv
source .venv/bin/activate
```

**Install packages:**

```bash
# Core dependencies
pip install -r requirements.txt

# Development tools (optional)
pip install -r requirements-dev.txt

# Install in editable mode
pip install -e ".[dev,dashboards]"
```

### 4. Configure Environment

**Create `.env.local` file** (git-ignored):

```bash
# Windows PowerShell
Copy-Item .env .env.local

# macOS/Linux
cp .env .env.local
```

**Edit `.env.local` with your API keys:**

```bash
# Required: OpenAI API key
OPENAI_API_KEY=sk-proj-YOUR-KEY-HERE

# Optional: Anthropic for Claude models
ANTHROPIC_API_KEY=sk-ant-YOUR-KEY-HERE

# Optional: Google for Gemini support
GOOGLE_API_KEY=AIza-YOUR-KEY-HERE

# Redis connection
REDIS_URL=redis://localhost:6379/0
QUEUE_BACKEND=redis

# Feature flags (production)
FEATURE_RBAC_ENFORCE=true
FEATURE_BUDGETS=true
```

**Important**: Never commit `.env.local` to version control.

### 5. Start Redis

**Using Docker:**
```bash
docker run -d --name redis -p 6379:6379 redis:7-alpine
```

**Using native install:**
```bash
# Windows (with Chocolatey)
choco install redis-64
redis-server

# macOS (with Homebrew)
brew install redis
brew services start redis

# Linux (Ubuntu/Debian)
sudo apt update && sudo apt install redis-server
sudo systemctl start redis-server
```

**Verify Redis:**
```bash
redis-cli ping
# Expected output: PONG
```

### 6. First Run

**Run a simple workflow:**

```bash
python -m src.run_workflow --task "Explain the benefits of type hints in Python"
```

**Expected output:**
- Workflow execution logs
- Cost tracking
- Artifact saved to `artifacts/hot/default/`

### 7. Verify Health Checks

**Start health server:**

```bash
python src/health_server.py
```

**Check endpoints:**

```bash
# Health check
curl http://localhost:8080/health
# Expected: {"status": "healthy", "version": "1.0.0"}

# Readiness check
curl http://localhost:8080/ready
# Expected: {"status": "ready", "redis": "connected"}
```

### 8. Launch Dashboard

**Start Streamlit dashboard:**

```bash
streamlit run dashboards/app.py
```

**Access at:** http://localhost:8501

**Dashboard features:**
- Cost metrics and budget tracking
- Workflow execution history
- Connector health monitoring
- Checkpoint approval interface

### 9. Run Smoke Tests

**Execute end-to-end smoke tests:**

```bash
pytest -m e2e
```

**Expected:**
- All tests pass (green)
- Offline tests (no live API calls)
- Tests validate configuration, schema, and core workflows

## Docker Compose Setup

For production-like deployments with minimal configuration.

### 1. Navigate to Docker Directory

```bash
cd docker
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your API keys
# Minimum required: OPENAI_API_KEY
```

### 3. Start Services

**Using helper script (PowerShell):**
```powershell
.\start-docker.ps1 -Background -Workers 2
```

**Using helper script (Bash):**
```bash
./start-docker.sh -b -w 2
```

**Using Docker Compose directly:**
```bash
docker-compose up -d --scale worker=2
```

### 4. Verify Services

**Check service status:**
```bash
docker-compose ps
```

**Check logs:**
```bash
docker-compose logs -f app
docker-compose logs -f worker
```

**Test health endpoints:**
```bash
# App health
curl http://localhost:8080/health

# Dashboard
curl http://localhost:8501
```

### 5. Access Dashboard

Open browser: http://localhost:8501

### 6. Stop Services

```bash
# Stop containers
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Admin Setup & First Login

### Bootstrap Admin Account

**1. Create admin user:**

```bash
python scripts/bootstrap.py \
  --admin-email admin@example.com \
  --tenant-id default
```

**2. Set admin role:**

```bash
export USER_RBAC_ROLE=Admin
export USER_ID=admin@example.com
export TENANT_ID=default
```

**3. Verify permissions:**

```bash
python -c "
from src.security.authz import create_principal_from_headers
principal = create_principal_from_headers({
    'X-User-ID': 'admin@example.com',
    'X-Tenant-ID': 'default',
    'X-User-Role': 'Admin'
})
print(f'Admin: {principal.user_id}, Role: {principal.role}, Tenant: {principal.tenant_id}')
"
```

### Provision Additional Users

**1. Add team member:**

```bash
python scripts/teams.py create --team-id eng-team --name "Engineering Team"
python scripts/teams.py add-member --team-id eng-team --user-id developer@example.com --role Operator
```

**2. Create workspace:**

```bash
python scripts/workspaces.py create --workspace-id prod-workspace --name "Production Workspace"
python scripts/workspaces.py add-member --workspace-id prod-workspace --user-id developer@example.com --role Operator
```

**3. Grant temporary delegation:**

```bash
python scripts/delegation.py grant \
  --granter admin@example.com \
  --grantee developer@example.com \
  --scope team \
  --scope-id eng-team \
  --role Admin \
  --duration 8h \
  --reason "On-call coverage"
```

## Verify Installation

### Run Checklist

```bash
# 1. Python version
python --version
# Expected: Python 3.9+ (3.11+ recommended)

# 2. Dependencies installed
pip list | grep djp-workflow
# Expected: djp-workflow 1.0.0 (or current version)

# 3. Redis connectivity
redis-cli ping
# Expected: PONG

# 4. Configuration validation
python -m src.config.validate
# Expected: All checks pass

# 5. Health checks
curl http://localhost:8080/health
curl http://localhost:8080/ready
# Expected: Both return 200 OK with JSON

# 6. Run smoke tests
pytest -m e2e
# Expected: All tests pass

# 7. Execute simple workflow
python -m src.run_workflow --task "Test workflow"
# Expected: Artifact created in artifacts/hot/default/

# 8. Dashboard loads
streamlit run dashboards/app.py &
sleep 5
curl http://localhost:8501
# Expected: 200 OK
```

### Post-Install Verification

**Check directory structure:**
```bash
ls -la artifacts audit logs runs config
```

**Expected directories:**
- `artifacts/hot/` - Recent workflow outputs
- `audit/` - Audit logs
- `logs/` - System logs
- `runs/` - Workflow execution metadata
- `config/` - Configuration files

**Check log files:**
```bash
tail -20 logs/audit-$(date +%Y-%m-%d).jsonl
tail -20 logs/orchestrator_events.jsonl
tail -20 logs/cost_events.jsonl
```

**Expected:**
- JSON Lines format
- Valid timestamps
- No errors or warnings

## Common Installation Issues

### Python Version Mismatch

**Error:** `requires Python 3.9 or higher`

**Solution:**
```bash
# Check version
python --version

# Install correct version (Ubuntu/Debian)
sudo apt install python3.11 python3.11-venv

# Use specific version
python3.11 -m venv .venv
```

### Redis Connection Failed

**Error:** `ConnectionRefusedError: [Errno 61] Connection refused`

**Solution:**
```bash
# Check Redis status
redis-cli ping

# Start Redis (Docker)
docker run -d --name redis -p 6379:6379 redis:7-alpine

# Start Redis (native)
redis-server

# Check Redis logs
redis-cli INFO | grep uptime
```

### Missing API Key

**Error:** `OPENAI_API_KEY environment variable not found`

**Solution:**
```bash
# Create .env.local
cp .env .env.local

# Add API key
echo "OPENAI_API_KEY=sk-proj-YOUR-KEY-HERE" >> .env.local

# Verify
python -c "import os; from dotenv import load_dotenv; load_dotenv('.env.local'); print('Key loaded:', bool(os.getenv('OPENAI_API_KEY')))"
```

### Permission Denied

**Error:** `PermissionError: [Errno 13] Permission denied: 'logs/'`

**Solution:**
```bash
# Create directories with proper permissions
mkdir -p logs artifacts audit runs
chmod 755 logs artifacts audit runs

# Fix ownership (Linux/macOS)
sudo chown -R $(whoami):$(whoami) logs artifacts audit runs
```

### Port Already in Use

**Error:** `OSError: [Errno 48] Address already in use: 8501`

**Solution:**
```bash
# Find process using port (Windows)
netstat -ano | findstr :8501

# Find process using port (macOS/Linux)
lsof -i :8501

# Kill process
kill -9 <PID>

# Or use different port
streamlit run dashboards/app.py --server.port 8502
```

### Docker Build Fails

**Error:** `Error response from daemon: failed to build`

**Solution:**
```bash
# Clean Docker cache
docker system prune -a

# Rebuild with no cache
docker-compose build --no-cache

# Check disk space
docker system df

# Free space if needed
docker system prune -a --volumes
```

## Next Steps

After successful installation:

1. **Read Documentation**: Review [OPERATIONS.md](./OPERATIONS.md) for operational guidance
2. **Configure RBAC**: Set up role-based access control (see [SECURITY.md](./SECURITY.md))
3. **Set Budgets**: Configure team and tenant budgets (see [COSTS.md](./COSTS.md))
4. **Create Templates**: Build workflow templates (see [TEMPLATES.md](./TEMPLATES.md))
5. **Enable Connectors**: Configure Gmail, Slack, Teams, etc. (see [CONNECTORS.md](./CONNECTORS.md))
6. **Monitor**: Set up observability dashboards and alerts (see [OPERATIONS.md](./OPERATIONS.md))

## Production Deployment Checklist

Before deploying to production:

- [ ] Configure secrets management (AWS Secrets Manager, GCP Secret Manager, or Azure Key Vault)
- [ ] Enable RBAC enforcement: `FEATURE_RBAC_ENFORCE=true`
- [ ] Set production budgets per tenant/team
- [ ] Configure backup strategy for artifacts and logs
- [ ] Set up monitoring and alerting
- [ ] Enable audit logging with appropriate retention
- [ ] Configure SSL/TLS for web endpoints
- [ ] Review and harden security settings
- [ ] Set up multi-region deployment (if applicable)
- [ ] Test disaster recovery procedures

## Support & Resources

- **Documentation**: [docs/](../docs/)
- **Operations Guide**: [docs/OPERATIONS.md](./OPERATIONS.md)
- **Security Guide**: [docs/SECURITY.md](./SECURITY.md)
- **GitHub Issues**: Report bugs and request features
- **GitHub Discussions**: Ask questions and share ideas

## Troubleshooting

For additional troubleshooting:
- Check logs in `logs/` directory
- Review [ERRORS.md](./ERRORS.md) for common error patterns
- Consult [OPERATIONS.md](./OPERATIONS.md) for operational guidance
- Visit GitHub Issues for known issues and solutions

---

**Installation Complete!** You're ready to run production workflows.
