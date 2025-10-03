# Security & Access Control

Production-grade security with RBAC, multi-tenancy, and audit logging.

## Role-Based Access Control (RBAC)

### Roles

| Role | Description | Typical Users |
|------|-------------|---------------|
| **Admin** | Full access to all resources | System administrators, DevOps |
| **Editor** | Can execute workflows, approve artifacts | Content creators, analysts |
| **Viewer** | Read-only access | Stakeholders, auditors |

### Permissions Matrix

| Resource | Admin | Editor | Viewer |
|----------|-------|--------|--------|
| **Templates** | Read, Write, Delete, Execute | Read, Execute | Read |
| **Artifacts** | Read, Write, Delete, Export | Read, Export | Read |
| **Workflows** | Read, Write, Delete, Execute | Read, Execute, Approve | Read |
| **Batch Jobs** | Read, Write, Delete, Execute | Read, Execute | Read |
| **Config** | Read, Write | Read | Read |

### User Preferences

User preferences (favorites, layout, theme) follow special RBAC rules:

- **Viewers**: Can read own preferences only (read-only role)
- **Editors**: Can read and write own preferences
- **Admins**: Can read and write any user's preferences (for delegation)
- **Tenant isolation**: Preferences are isolated per tenant (cross-tenant access blocked)

Preferences are stored in the `user_prefs` table with primary key `(user_id, tenant_id, key)`.

## Multi-Tenancy

### Tenant Isolation

Every request, artifact, and audit event carries a `tenant_id`. Users can only access resources within their assigned tenant.

**Enforcement:**
- Web API: Extract `tenant_id` from `X-Tenant-ID` header
- Artifacts: Include `tenant_id` in metadata
- Audit logs: Record `tenant_id` for all actions

### Tenant Propagation

```
User Request → Principal (tenant_id) → Resource Check → Action Allowed/Denied
```

All operations validate:
1. User's `tenant_id` matches resource's `tenant_id`
2. User's role has permission for the action

## Authentication

### Headers

API requests must include:

```http
X-User-ID: user@example.com
X-Tenant-ID: tenant-abc-123
X-User-Role: editor
X-User-Email: user@example.com (optional)
```

### Feature Flags

```bash
# Enable RBAC enforcement (default: false in dev)
FEATURE_RBAC_ENFORCE=true

# Default tenant for anonymous users
DEFAULT_TENANT_ID=default
```

## Authorization Enforcement Points

### Web API (`src/webapi.py`)

```python
from src.security.authz import create_principal_from_headers, require_permission

# Extract principal from headers
principal = create_principal_from_headers(request.headers)

# Check permission
resource = Resource(
    resource_type=ResourceType.TEMPLATE,
    resource_id=template_name,
    tenant_id=principal.tenant_id
)

require_permission(principal, Action.EXECUTE, resource)
```

### Webhooks (`src/webhooks.py`)

```python
# Extract principal and validate approval permission
principal = create_principal_from_headers(request.headers)
resource = Resource(
    resource_type=ResourceType.WORKFLOW,
    resource_id=artifact_id,
    tenant_id=principal.tenant_id
)

require_permission(principal, Action.APPROVE, resource)
```

### Templates Tab

Template operations check permissions before execution:
- **Clone**: Requires WRITE on templates
- **Execute**: Requires EXECUTE on workflows
- **Approve**: Requires APPROVE on workflows
- **Delete**: Requires DELETE on templates

## Audit Logging

### Event Types

| Action | When Logged | Fields |
|--------|-------------|--------|
| `run_workflow` | DJP workflow execution | task, cost, duration |
| `approve_artifact` | Artifact approved | artifact_id, reviewer |
| `reject_artifact` | Artifact rejected | artifact_id, reason |
| `create_template` | Template created | template_name |
| `delete_template` | Template deleted | template_name |
| `export_artifact` | Artifact exported | artifact_id, format |
| `auth_failure` | Authorization denied | attempted_action, reason |

### Log Format

Audit logs stored as JSON Lines (`.jsonl`):

```json
{
  "timestamp": "2025-10-01T12:00:00.000Z",
  "tenant_id": "tenant-abc-123",
  "user_id": "user@example.com",
  "action": "run_workflow",
  "resource_type": "workflow",
  "resource_id": "wf-12345",
  "result": "success",
  "metadata": {"cost_usd": 0.05, "duration_s": 3.2},
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0..."
}
```

### Querying Audit Logs

```python
from src.security.audit import get_audit_logger, AuditAction, AuditResult

logger = get_audit_logger()

# Query denied actions for a tenant
events = logger.query(
    tenant_id="tenant-abc-123",
    result=AuditResult.DENIED,
    limit=100
)

# Query approval actions
events = logger.query(
    action=AuditAction.APPROVE_ARTIFACT,
    limit=50
)
```

### Retention

- Audit logs stored in `audit/` directory (configurable via `AUDIT_LOG_DIR`)
- Daily log files: `audit-YYYY-MM-DD.jsonl`
- Recommended retention: 90 days minimum (compliance)
- Archive to S3/GCS for long-term storage

## Security Best Practices

### 1. Enable RBAC in Production

```bash
export FEATURE_RBAC_ENFORCE=true
```

### 2. Use Least Privilege

- Assign **Viewer** role by default
- Grant **Editor** only when needed
- Restrict **Admin** to ops team

### 3. Monitor Audit Logs

```bash
# Watch for authorization failures
tail -f audit/audit-$(date +%Y-%m-%d).jsonl | grep '"result":"denied"'

# Count actions per tenant
cat audit/audit-*.jsonl | jq -r .tenant_id | sort | uniq -c
```

### 4. Tenant Isolation

- Never share tenant IDs across organizations
- Use UUIDs for tenant IDs (not sequential integers)
- Validate tenant ID in every request

### 5. Rotate Credentials

- Rotate API keys every 90 days
- Use secrets manager (AWS Secrets Manager, GCP Secret Manager)
- Never commit credentials to git

## Compliance

### SOC 2 / ISO 27001

- **Access Control**: RBAC with principle of least privilege
- **Audit Logging**: All actions logged with user/tenant/timestamp
- **Data Isolation**: Multi-tenant with strict boundaries
- **Encryption**: TLS in transit, at-rest encryption for artifacts

### GDPR

- **Right to Access**: Audit logs queryable by user
- **Right to Deletion**: Artifacts deletable by authorized users
- **Data Minimization**: Only required fields in logs
- **Consent**: Explicit permission checks before actions

## Troubleshooting

### "Permission denied" errors

1. Check user role in `X-User-Role` header
2. Verify tenant ID matches resource tenant
3. Review permissions matrix above
4. Check `FEATURE_RBAC_ENFORCE` setting

### Audit logs not appearing

1. Check `AUDIT_LOG_DIR` path exists
2. Verify write permissions on directory
3. Check disk space
4. Review logs in stderr if file write fails

### Tenant isolation not working

1. Ensure `X-Tenant-ID` header sent with requests
2. Verify `FEATURE_RBAC_ENFORCE=true`
3. Check principal extraction in web API

## Example: Adding a New User

```python
# 1. Create principal
from src.security.authz import Principal, Role

user = Principal(
    user_id="newuser@example.com",
    tenant_id="tenant-abc-123",
    role=Role.EDITOR,
    email="newuser@example.com"
)

# 2. Client includes headers in API requests
headers = {
    "X-User-ID": "newuser@example.com",
    "X-Tenant-ID": "tenant-abc-123",
    "X-User-Role": "editor"
}

# 3. API validates permissions
# 4. Audit log records actions
```

## Testing RBAC

### Test Fixture

All tests automatically enable RBAC enforcement via `tests/conftest.py`:

```python
@pytest.fixture(autouse=True)
def _enable_rbac_and_budgets(monkeypatch):
    monkeypatch.setenv("FEATURE_RBAC_ENFORCE", "true")
    monkeypatch.setenv("FEATURE_BUDGETS", "true")
```

This ensures tests validate actual RBAC behavior rather than bypassing checks when feature flags default to `false` in development. CI also sets these environment variables to prevent false positives.

### CI Environment

GitHub Actions CI automatically sets:
- `FEATURE_RBAC_ENFORCE=true`
- `FEATURE_BUDGETS=true`

This guarantees all test runs (local and CI) validate RBAC enforcement consistently.

## Per-Tenant Concurrency & Rate Limiting

Sprint 24 introduces per-tenant concurrency controls and global rate limiting to protect against abuse, ensure fair resource allocation, and maintain system stability.

### Overview

Multi-tenant systems require safeguards to prevent:
- **Resource monopolization** - One tenant consuming all workers
- **Denial of service** - Excessive requests overwhelming the system
- **Cost overruns** - Runaway jobs draining budget
- **Noisy neighbor** - One tenant degrading performance for others

### Per-Tenant Concurrency Limits

#### Environment Variable

| Variable | Default | Description |
|----------|---------|-------------|
| `PER_TENANT_MAX_CONCURRENCY` | `unlimited` | Max concurrent jobs per tenant |

#### Configuration

```bash
# Limit each tenant to 5 concurrent jobs
export PER_TENANT_MAX_CONCURRENCY=5

# Unlimited (default)
export PER_TENANT_MAX_CONCURRENCY=0
```

#### How It Works

The worker pool tracks active jobs per tenant:

```python
# Pseudo-code implementation
active_jobs_by_tenant = {
    "tenant-abc": 3,  # 3 jobs in-flight
    "tenant-xyz": 5,  # 5 jobs in-flight (at limit)
}

def submit_job(job):
    tenant_id = job.tenant_id
    max_concurrency = int(os.getenv("PER_TENANT_MAX_CONCURRENCY", "0"))

    if max_concurrency > 0:
        current = active_jobs_by_tenant.get(tenant_id, 0)
        if current >= max_concurrency:
            # Reject or queue the job
            raise ConcurrencyLimitExceeded(
                f"Tenant {tenant_id} at limit: {current}/{max_concurrency}"
            )

    # Accept job
    active_jobs_by_tenant[tenant_id] += 1
    execute_job(job)
```

#### Use Cases

**High-concurrency tenant:**
```bash
# Premium tier with higher limit
export PER_TENANT_MAX_CONCURRENCY=20
```

**Trial/Free tier tenant:**
```bash
# Restrict free tier to 2 concurrent jobs
export PER_TENANT_MAX_CONCURRENCY=2
```

**Multi-tenancy with fairness:**
```bash
# Ensure no tenant monopolizes workers
# If MAX_WORKERS=12 and 4 tenants, limit each to 3
export PER_TENANT_MAX_CONCURRENCY=3
```

#### Enforcement Points

1. **Job submission** (`src/scale/worker_pool.py`)
   - Check tenant's current concurrency before accepting job
   - Return 429 Too Many Requests if limit exceeded

2. **Queue routing** (`src/queue_strategy.py`)
   - Hybrid queue router enforces tenant limits
   - Tasks from over-limit tenants stay queued

3. **API endpoints** (`src/webapi.py`)
   - Web API rejects requests if tenant at limit
   - Returns error with retry-after header

### Global QPS Limits

#### Environment Variable

| Variable | Default | Description |
|----------|---------|-------------|
| `GLOBAL_QPS_LIMIT` | `unlimited` | Global queries per second limit |

#### Configuration

```bash
# Limit system to 100 requests/second
export GLOBAL_QPS_LIMIT=100

# Unlimited (default)
export GLOBAL_QPS_LIMIT=0
```

#### How It Works

Token bucket algorithm for global rate limiting:

```python
# Pseudo-code implementation
class GlobalRateLimiter:
    def __init__(self, qps_limit):
        self.qps_limit = qps_limit
        self.tokens = qps_limit
        self.last_refill = time.time()

    def allow_request(self):
        if self.qps_limit == 0:
            return True  # Unlimited

        # Refill tokens
        now = time.time()
        elapsed = now - self.last_refill
        self.tokens = min(
            self.qps_limit,
            self.tokens + (elapsed * self.qps_limit)
        )
        self.last_refill = now

        # Check if tokens available
        if self.tokens >= 1.0:
            self.tokens -= 1.0
            return True

        return False  # Rate limited
```

#### Abuse Prevention

Global QPS limits protect against:

1. **DDoS attacks**
   ```bash
   # Limit to reasonable throughput
   export GLOBAL_QPS_LIMIT=200
   ```

2. **Accidental loops**
   ```bash
   # Prevent runaway scripts
   export GLOBAL_QPS_LIMIT=50
   ```

3. **Resource exhaustion**
   ```bash
   # Cap total system load
   export GLOBAL_QPS_LIMIT=100
   ```

### How Concurrency Limits Protect Against Abuse

#### Scenario 1: Malicious Tenant Flood

**Attack:**
Tenant submits 1000 jobs simultaneously to monopolize resources.

**Protection:**
```bash
export PER_TENANT_MAX_CONCURRENCY=5
```

**Result:**
- First 5 jobs accepted and execute
- Remaining 995 jobs queued or rejected
- Other tenants unaffected

#### Scenario 2: Accidental Infinite Loop

**Attack:**
Buggy script submits jobs in tight loop.

**Protection:**
```bash
export GLOBAL_QPS_LIMIT=50
export PER_TENANT_MAX_CONCURRENCY=3
```

**Result:**
- Global rate limiter blocks excessive requests (429 errors)
- Tenant concurrency cap prevents resource drain
- Alert triggered for investigation

#### Scenario 3: Credential Compromise

**Attack:**
Stolen API key used to launch expensive workflows.

**Protection:**
```bash
export PER_TENANT_MAX_CONCURRENCY=10
export BUDGET_USD_PER_TENANT=100
```

**Result:**
- Concurrency limit caps parallel execution
- Budget limit stops runaway costs
- Audit logs show suspicious activity

#### Scenario 4: Multi-Tenant Noisy Neighbor

**Attack:**
One tenant's heavy load degrades performance for all.

**Protection:**
```bash
export PER_TENANT_MAX_CONCURRENCY=3
export MAX_WORKERS=12  # 4 tenants x 3 = fair distribution
```

**Result:**
- Each tenant limited to fair share of workers
- Performance isolation maintained
- No single tenant dominates

### Monitoring for Limit Violations

#### Metrics to Track

1. **Concurrency limit hits**
   ```python
   # Count how often tenants hit their limit
   tenant_limit_hits_counter.labels(tenant_id=tenant_id).inc()
   ```

2. **Queue depth by tenant**
   ```python
   # Track queued jobs per tenant
   tenant_queue_depth_gauge.labels(tenant_id=tenant_id).set(depth)
   ```

3. **Rate limit rejections**
   ```python
   # Count 429 responses
   rate_limit_rejections_counter.labels(endpoint="/api/run").inc()
   ```

4. **Concurrency by tenant**
   ```python
   # Current in-flight jobs per tenant
   tenant_concurrency_gauge.labels(tenant_id=tenant_id).set(count)
   ```

#### Querying Audit Logs

```python
from src.security.audit import get_audit_logger, AuditResult

logger = get_audit_logger()

# Find tenants hitting concurrency limits
events = logger.query(
    result=AuditResult.DENIED,
    reason_contains="ConcurrencyLimitExceeded",
    limit=100
)

for event in events:
    print(f"Tenant {event.tenant_id} hit limit at {event.timestamp}")
```

#### Alerting on Violations

**Alert 1: Tenant Repeatedly Hitting Limit**
```bash
# Alert if tenant hits limit >100 times in 5 minutes
SELECT COUNT(*) FROM audit_logs
WHERE result = 'denied'
  AND reason LIKE '%ConcurrencyLimitExceeded%'
  AND timestamp > NOW() - INTERVAL '5 minutes'
GROUP BY tenant_id
HAVING COUNT(*) > 100
```

**Alert 2: Global Rate Limit Saturation**
```bash
# Alert if >50% of requests rate-limited
SELECT
  (COUNT(*) FILTER (WHERE status = 429)) * 100.0 / COUNT(*) as rate_limit_pct
FROM api_requests
WHERE timestamp > NOW() - INTERVAL '1 minute'
HAVING rate_limit_pct > 50
```

**Alert 3: Sudden Concurrency Spike**
```bash
# Alert if tenant jumps from 0 to max concurrency in <1 minute
SELECT tenant_id, MAX(concurrency) as peak
FROM metrics
WHERE timestamp > NOW() - INTERVAL '1 minute'
GROUP BY tenant_id
HAVING peak >= PER_TENANT_MAX_CONCURRENCY
  AND MIN(concurrency) = 0
```

### Configuration Matrix

| Tenant Tier | Max Concurrency | QPS Limit | Budget |
|-------------|-----------------|-----------|--------|
| **Free** | 2 | 10/min | $1/day |
| **Basic** | 5 | 50/min | $10/day |
| **Pro** | 20 | 200/min | $100/day |
| **Enterprise** | 100 | 1000/min | Custom |

Example configuration for Basic tier:

```bash
export PER_TENANT_MAX_CONCURRENCY=5
export QUEUE_RATE_LIMIT=50  # Per minute
export BUDGET_USD=10
export BUDGET_WINDOW=86400  # 24 hours
```

### Integration with Worker Pool

The autoscaler respects per-tenant limits when scaling:

```python
from src.scale.autoscaler import make_scale_decision, EngineState

# Build state with tenant-aware metrics
state = EngineState(
    current_workers=stats.total_workers,
    queue_depth=stats.queue_depth,
    p95_latency_ms=get_p95_latency(),
    in_flight_jobs=stats.active_workers,
)

decision = make_scale_decision(state)

# Scale up respects tenant distribution
if decision.direction == ScaleDirection.UP:
    # Ensure new workers can serve waiting tenants
    # without violating per-tenant limits
    pool.scale_to(decision.desired_workers)
```

### Best Practices

1. **Set Conservative Defaults**
   ```bash
   # Start restrictive, relax based on monitoring
   export PER_TENANT_MAX_CONCURRENCY=3
   export GLOBAL_QPS_LIMIT=100
   ```

2. **Monitor Before Enforcing**
   ```bash
   # Track metrics for 1 week before enabling limits
   # Determine appropriate thresholds from P95 usage
   ```

3. **Gradual Rollout**
   ```bash
   # Enable for one tenant tier at a time
   # Free tier → Basic → Pro → Enterprise
   ```

4. **Provide Clear Error Messages**
   ```python
   # When rejecting due to limits
   raise ConcurrencyLimitExceeded(
       f"Tenant {tenant_id} has {current} jobs in-flight. "
       f"Limit: {max_concurrency}. Please wait for jobs to complete."
   )
   ```

5. **Document Limits in API**
   ```
   Rate Limits:
   - Per-tenant concurrency: 5 concurrent jobs
   - Global rate limit: 100 requests/second
   - Retry-After header provided on 429 responses
   ```

6. **Allow Override for Support**
   ```bash
   # Temporary override for tenant (audit logged)
   export TENANT_abc123_MAX_CONCURRENCY=50
   ```

### Troubleshooting

#### Issue: Legitimate tenant hitting limits

**Symptoms:**
- Frequent 429 responses
- Jobs queued for long periods
- User complaints about slowness

**Resolution:**
```bash
# 1. Verify tenant's usage pattern
python scripts/analyze_tenant_usage.py --tenant-id tenant-abc

# 2. Check if limit is too restrictive
# Compare to tenant's tier allocation

# 3. Temporarily increase limit
export PER_TENANT_MAX_CONCURRENCY=10

# 4. Consider tier upgrade if justified
```

#### Issue: Limits not being enforced

**Symptoms:**
- Tenant exceeding documented limits
- No 429 responses in logs
- Resource monopolization

**Resolution:**
```bash
# 1. Verify environment variables set
echo $PER_TENANT_MAX_CONCURRENCY
echo $GLOBAL_QPS_LIMIT

# 2. Check enforcement is enabled
export FEATURE_RATE_LIMITING=true

# 3. Restart services to apply
systemctl restart worker-pool webapi

# 4. Verify in logs
tail -f logs/webapi.log | grep "ConcurrencyLimitExceeded"
```

#### Issue: False positive rate limiting

**Symptoms:**
- Legitimate requests rejected
- Rate limit hit during normal usage
- No actual abuse

**Resolution:**
```bash
# 1. Analyze request patterns
python scripts/analyze_rate_limits.py --since 24h

# 2. Increase limits if too strict
export GLOBAL_QPS_LIMIT=200

# 3. Consider per-endpoint limits
export API_RUN_QPS_LIMIT=100
export API_STATUS_QPS_LIMIT=500

# 4. Implement backoff/retry in clients
```

### Testing Concurrency Limits

```python
import pytest
from src.scale.worker_pool import WorkerPool, Job, ConcurrencyLimitExceeded

def test_per_tenant_concurrency_limit(monkeypatch):
    """Test that per-tenant concurrency limit is enforced."""
    monkeypatch.setenv("PER_TENANT_MAX_CONCURRENCY", "3")

    pool = WorkerPool(initial_workers=10)
    tenant_id = "test-tenant"

    # Submit 3 jobs (should succeed)
    for i in range(3):
        job = Job(
            job_id=f"job-{i}",
            task=lambda: time.sleep(5),
            tenant_id=tenant_id
        )
        pool.submit_job(job)

    # 4th job should be rejected
    with pytest.raises(ConcurrencyLimitExceeded):
        job = Job(
            job_id="job-4",
            task=lambda: time.sleep(5),
            tenant_id=tenant_id
        )
        pool.submit_job(job)

def test_global_qps_limit(monkeypatch):
    """Test that global QPS limit is enforced."""
    monkeypatch.setenv("GLOBAL_QPS_LIMIT", "10")

    limiter = GlobalRateLimiter(qps_limit=10)

    # First 10 requests in same second should succeed
    for i in range(10):
        assert limiter.allow_request() is True

    # 11th request should be rate limited
    assert limiter.allow_request() is False

    # After 1 second, tokens refilled
    time.sleep(1.1)
    assert limiter.allow_request() is True
```

## Secrets Management

Proper secrets management is critical for security. This section covers best practices for handling API keys, credentials, and sensitive configuration.

### No Secrets in Repository Policy

**NEVER commit secrets to version control.**

Enforce this policy with these measures:

#### 1. Git Ignore Configuration

The `.gitignore` file already includes:
```gitignore
# Environment files with secrets
.env.local
.env.*.local
*.env

# Credentials files
*_credentials
*_key
*.pem
*.key

# Cloud provider credentials
.aws/
.gcp/
.azure/
```

**Verify:**
```bash
# Check if .env.local is ignored
git check-ignore .env.local
# Output: .env.local (if properly ignored)

# Ensure no secrets in git history
git log --all --full-history --source --extra=all -- .env.local
# Should return nothing
```

#### 2. Pre-commit Hooks

Install pre-commit hooks to block secret commits:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Hooks automatically run on git commit
```

**Pre-commit checks:**
- Detect hardcoded API keys (patterns: `sk-`, `AKIA`, etc.)
- Scan for common credential patterns
- Block commits containing secrets
- Warn about suspicious file additions

#### 3. Secret Scanning

Use GitHub's secret scanning (automatically enabled for public repos):

- Scans commits for known secret patterns
- Alerts on exposed credentials
- Provides remediation guidance
- Supports custom patterns

**Manual scanning:**
```bash
# Install gitleaks
# Windows: choco install gitleaks
# macOS: brew install gitleaks
# Linux: Download from https://github.com/gitleaks/gitleaks

# Scan repository
gitleaks detect --source . --verbose

# Scan specific files
gitleaks detect --source .env.local --verbose
```

### Using .env.local for Secrets

Store secrets in `.env.local` file (git-ignored):

#### Creating .env.local

```bash
# Windows PowerShell
Copy-Item .env .env.local

# macOS/Linux
cp .env .env.local

# Edit with your secrets
# Windows: notepad .env.local
# macOS/Linux: nano .env.local
```

#### .env.local Structure

```bash
# .env.local - NEVER commit this file!

# OpenAI API Key (required)
OPENAI_API_KEY=sk-proj-abc123def456...

# Anthropic API Key (optional, for Claude models)
ANTHROPIC_API_KEY=sk-ant-xyz789...

# Database credentials (if applicable)
DATABASE_URL=postgresql://user:password@localhost:5432/djp_db

# Cloud storage credentials (if applicable)
AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE
AWS_SECRET_ACCESS_KEY=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
AWS_DEFAULT_REGION=us-west-2

# Webhook secrets (if applicable)
WEBHOOK_SECRET=your-webhook-secret-here

# Session secrets (if applicable)
SESSION_SECRET=your-random-session-secret
```

#### Loading .env.local

Application automatically loads `.env.local` on startup:

```python
# src/__init__.py or src/config.py
from dotenv import load_dotenv
import os

# Load .env.local if exists, otherwise .env
load_dotenv('.env.local', override=True)
load_dotenv('.env', override=False)

# Access secrets
api_key = os.getenv('OPENAI_API_KEY')
```

**Verify loading:**
```bash
python -c "import os; from dotenv import load_dotenv; load_dotenv('.env.local'); print('Key loaded:', bool(os.getenv('OPENAI_API_KEY')))"
```

### Environment Variable Security

Best practices for handling environment variables:

#### Windows (PowerShell)

```powershell
# Temporary (current session only) - SAFE
$env:OPENAI_API_KEY = "sk-proj-..."

# User-level persistent - LESS SAFE (stored in registry)
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'sk-proj-...', 'User')

# System-level persistent - UNSAFE (shared across users)
# DO NOT USE for secrets

# Best practice: Use .env.local file
```

#### Windows (Command Prompt)

```cmd
REM Temporary (current session only) - SAFE
set OPENAI_API_KEY=sk-proj-...

REM Best practice: Use .env.local file
```

#### macOS/Linux

```bash
# Temporary (current session only) - SAFE
export OPENAI_API_KEY="sk-proj-..."

# User-level persistent - LESS SAFE (stored in shell config)
echo 'export OPENAI_API_KEY="sk-proj-..."' >> ~/.bashrc
source ~/.bashrc

# System-level persistent - UNSAFE
# DO NOT store secrets in /etc/environment

# Best practice: Use .env.local file
```

#### Cloud Deployment

For production deployments, use secrets management services:

**AWS:**
```bash
# Store in AWS Secrets Manager
aws secretsmanager create-secret \
  --name djp-workflow/openai-api-key \
  --secret-string "sk-proj-..."

# Retrieve at runtime
OPENAI_API_KEY=$(aws secretsmanager get-secret-value \
  --secret-id djp-workflow/openai-api-key \
  --query SecretString \
  --output text)
```

**GCP:**
```bash
# Store in Secret Manager
echo -n "sk-proj-..." | gcloud secrets create openai-api-key --data-file=-

# Retrieve at runtime
OPENAI_API_KEY=$(gcloud secrets versions access latest --secret="openai-api-key")
```

**Azure:**
```bash
# Store in Key Vault
az keyvault secret set \
  --vault-name djp-workflow-vault \
  --name openai-api-key \
  --value "sk-proj-..."

# Retrieve at runtime
OPENAI_API_KEY=$(az keyvault secret show \
  --vault-name djp-workflow-vault \
  --name openai-api-key \
  --query value \
  --output tsv)
```

### API Key Rotation Procedures

Rotate API keys regularly to minimize risk:

#### Rotation Schedule

- **Development keys:** Every 30 days
- **Staging keys:** Every 60 days
- **Production keys:** Every 90 days
- **After breach:** Immediately

#### Rotation Process

**1. Generate new key:**
```bash
# Visit https://platform.openai.com/api-keys
# Click "Create new secret key"
# Copy new key: sk-proj-new-key-here
```

**2. Update configuration:**
```bash
# Update .env.local
OLD_KEY=sk-proj-old-key-here
NEW_KEY=sk-proj-new-key-here

# Windows PowerShell
(Get-Content .env.local) -replace $OLD_KEY, $NEW_KEY | Set-Content .env.local

# macOS/Linux
sed -i "s/$OLD_KEY/$NEW_KEY/" .env.local
```

**3. Test new key:**
```bash
# Verify new key works
python -m src.run_workflow --task "Test" --dry-run

# Expected: No authentication errors
```

**4. Update production:**
```bash
# Update secrets manager
aws secretsmanager update-secret \
  --secret-id djp-workflow/openai-api-key \
  --secret-string "$NEW_KEY"

# Restart services to pick up new key
kubectl rollout restart deployment/djp-workflow
```

**5. Revoke old key:**
```bash
# Visit https://platform.openai.com/api-keys
# Click "Revoke" on old key
# Confirm revocation
```

**6. Verify no disruption:**
```bash
# Check logs for authentication errors
# Windows: findstr /I "401" logs\*.log
# macOS/Linux: grep -i "401" logs/*.log

# Check dashboard for failed workflows
```

#### Automated Rotation

Automate rotation with scripts:

```python
# scripts/rotate_api_key.py
import os
import openai
from datetime import datetime

def rotate_openai_key():
    """Rotate OpenAI API key."""
    old_key = os.getenv('OPENAI_API_KEY')

    # Generate new key (requires API access)
    # This is a placeholder - OpenAI doesn't support programmatic key generation yet
    # You must manually create keys in dashboard

    print("Manual steps required:")
    print("1. Visit https://platform.openai.com/api-keys")
    print("2. Create new key")
    print("3. Update .env.local")
    print("4. Restart services")
    print("5. Revoke old key")

    # Log rotation event
    with open('logs/key_rotation.log', 'a') as f:
        f.write(f"{datetime.now()}: Key rotation required for {old_key[:10]}...\n")

if __name__ == "__main__":
    rotate_openai_key()
```

**Schedule rotation reminders:**
```bash
# Windows Task Scheduler
schtasks /create /tn "API Key Rotation Reminder" /tr "python scripts/rotate_api_key.py" /sc monthly

# macOS/Linux cron
echo "0 0 1 * * python /path/to/scripts/rotate_api_key.py" | crontab -
```

### Audit Logging for Configuration Access

Track who accesses secrets and configuration:

#### Enable Audit Logging

```bash
# In .env.local
AUDIT_LOG_DIR=audit/
AUDIT_CONFIG_ACCESS=true
```

#### Configuration Access Events

```python
# src/security/audit.py
from src.security.audit import get_audit_logger, AuditAction

logger = get_audit_logger()

# Log configuration access
logger.log(
    action=AuditAction.ACCESS_CONFIG,
    user_id="admin@example.com",
    tenant_id="default",
    resource_type="config",
    resource_id=".env.local",
    result="success",
    metadata={"config_keys": ["OPENAI_API_KEY", "DATABASE_URL"]}
)
```

#### Querying Configuration Access

```python
from src.security.audit import get_audit_logger, AuditAction

logger = get_audit_logger()

# Find who accessed configuration
events = logger.query(
    action=AuditAction.ACCESS_CONFIG,
    since=datetime.now() - timedelta(days=7),
    limit=100
)

for event in events:
    print(f"{event.timestamp}: {event.user_id} accessed {event.resource_id}")
```

#### Alerting on Suspicious Access

```bash
# Monitor for unauthorized config access
python -c "
from src.security.audit import get_audit_logger, AuditResult
logger = get_audit_logger()
denied = logger.query(
    action='ACCESS_CONFIG',
    result=AuditResult.DENIED,
    limit=50
)
if len(denied) > 10:
    print(f'ALERT: {len(denied)} unauthorized config access attempts')
"
```

### Per-Tenant Isolation for Workflows

Ensure secrets and data are isolated per tenant:

#### Tenant-Scoped Secrets

```bash
# In .env.local
# Global default
OPENAI_API_KEY=sk-proj-default-key

# Per-tenant overrides
TENANT_acme_OPENAI_API_KEY=sk-proj-acme-key
TENANT_globex_OPENAI_API_KEY=sk-proj-globex-key
```

**Loading tenant-specific secrets:**
```python
def get_api_key(tenant_id: str) -> str:
    """Get tenant-specific API key."""
    # Check for tenant-specific key
    tenant_key = os.getenv(f'TENANT_{tenant_id}_OPENAI_API_KEY')
    if tenant_key:
        return tenant_key

    # Fall back to default
    return os.getenv('OPENAI_API_KEY')
```

#### Tenant Data Isolation

```python
from src.security.authz import Principal, Resource, ResourceType, Action, require_permission

def run_workflow(principal: Principal, template: str, inputs: dict):
    """Run workflow with tenant isolation."""
    # Validate tenant access
    resource = Resource(
        resource_type=ResourceType.WORKFLOW,
        resource_id=template,
        tenant_id=principal.tenant_id
    )

    require_permission(principal, Action.EXECUTE, resource)

    # Use tenant-specific API key
    api_key = get_api_key(principal.tenant_id)

    # Execute workflow in tenant context
    artifact = run_djp_workflow(
        task=inputs,
        api_key=api_key,
        tenant_id=principal.tenant_id
    )

    # Store artifact with tenant_id
    artifact['tenant_id'] = principal.tenant_id
    save_artifact(artifact)
```

#### Cross-Tenant Access Prevention

```python
def enforce_tenant_isolation(principal: Principal, resource: Resource):
    """Prevent cross-tenant access."""
    if principal.tenant_id != resource.tenant_id:
        logger.log(
            action=AuditAction.ACCESS_RESOURCE,
            user_id=principal.user_id,
            tenant_id=principal.tenant_id,
            resource_type=resource.resource_type,
            resource_id=resource.resource_id,
            result=AuditResult.DENIED,
            metadata={"reason": "cross_tenant_access_blocked"}
        )
        raise PermissionError(
            f"User {principal.user_id} (tenant {principal.tenant_id}) "
            f"cannot access resource in tenant {resource.tenant_id}"
        )
```

### Cost Tracking as Security Signal

Monitor costs for anomaly detection:

#### Unusual Cost Patterns

```python
def detect_cost_anomalies(tenant_id: str, time_window: timedelta):
    """Detect unusual spending patterns."""
    from src.observability import get_cost_metrics

    # Get recent costs
    recent_cost = get_cost_metrics(tenant_id, time_window)

    # Get historical baseline
    baseline_cost = get_cost_metrics(tenant_id, time_window * 7)  # 7x window for baseline

    # Alert if cost spike
    if recent_cost > baseline_cost * 3:  # 3x normal
        send_alert(
            f"ALERT: Tenant {tenant_id} cost spike detected. "
            f"Recent: ${recent_cost:.2f}, Baseline: ${baseline_cost:.2f}"
        )
```

#### Cost-Based Threat Detection

**Indicators of compromise:**
- Sudden increase in API calls
- High-cost model usage spike
- Unusual time-of-day activity
- Cross-region API calls (if not expected)
- High failure rates (brute force attempts)

**Monitoring:**
```bash
# Check for cost anomalies
python -c "
from src.observability import get_cost_metrics
from datetime import datetime, timedelta

# Last hour vs last week average
recent = get_cost_metrics('tenant-abc', timedelta(hours=1))
baseline = get_cost_metrics('tenant-abc', timedelta(days=7)) / (7 * 24)

if recent > baseline * 5:
    print(f'ALERT: Cost spike - recent: ${recent:.4f}, baseline: ${baseline:.4f}')
"
```

#### Budget Limits as Security Control

```bash
# In .env.local
# Prevent runaway costs from compromised credentials
BUDGET_USD_PER_HOUR=1.00
BUDGET_USD_PER_DAY=10.00
BUDGET_USD_PER_MONTH=200.00
```

**Enforce limits:**
```python
def check_budget_limit(tenant_id: str, projected_cost: float):
    """Enforce tenant budget limits."""
    daily_limit = float(os.getenv('BUDGET_USD_PER_DAY', '10.00'))
    daily_spent = get_daily_spending(tenant_id)

    if daily_spent + projected_cost > daily_limit:
        logger.log(
            action=AuditAction.RUN_WORKFLOW,
            user_id="system",
            tenant_id=tenant_id,
            result=AuditResult.DENIED,
            metadata={
                "reason": "daily_budget_exceeded",
                "daily_limit": daily_limit,
                "daily_spent": daily_spent,
                "projected_cost": projected_cost
            }
        )
        raise BudgetExceededError(
            f"Tenant {tenant_id} daily budget limit exceeded. "
            f"Spent: ${daily_spent:.2f}, Limit: ${daily_limit:.2f}"
        )
```

### Security Checklist

#### Development

- [ ] Use `.env.local` for secrets
- [ ] Never commit `.env.local` to git
- [ ] Use different API keys for dev/staging/prod
- [ ] Enable pre-commit hooks
- [ ] Scan for secrets before commits

#### Production

- [ ] Use secrets manager (AWS/GCP/Azure)
- [ ] Enable RBAC enforcement: `FEATURE_RBAC_ENFORCE=true`
- [ ] Configure tenant isolation
- [ ] Set up audit logging
- [ ] Enable cost tracking and alerts
- [ ] Rotate API keys every 90 days
- [ ] Monitor for anomalies
- [ ] Set budget limits per tenant

#### Incident Response

- [ ] Document key rotation procedures
- [ ] Create runbook for credential compromise
- [ ] Set up alerts for suspicious activity
- [ ] Test incident response procedures quarterly
- [ ] Maintain audit log retention (90+ days)

### Related Documentation

- [ONBOARDING.md](ONBOARDING.md) - Setting environment variables safely
- [ERRORS.md](ERRORS.md) - Troubleshooting API key errors
- [OPERATIONS.md](OPERATIONS.md) - Cost monitoring and budgeting
- [STORAGE.md](STORAGE.md) - Storage system architecture and usage

## Storage Security

### Tenant-Scoped Storage Paths

The storage system enforces strict tenant isolation through directory-based separation:

```
artifacts/
├── hot/
│   ├── tenant_a/     ← Tenant A's artifacts
│   ├── tenant_b/     ← Tenant B's artifacts
│   └── tenant_c/     ← Tenant C's artifacts
├── warm/
│   └── tenant_a/
└── cold/
    └── tenant_a/
```

### Path Traversal Prevention

All storage operations validate identifiers to prevent path traversal attacks:

```python
# BLOCKED: Path traversal attempts
tenant_id = "../../../etc"        # ✗ Raises InvalidTenantPathError
workflow_id = "/tmp/exploit"      # ✗ Raises InvalidTenantPathError
artifact_id = "../../passwd"      # ✗ Raises InvalidTenantPathError

# BLOCKED: Invalid characters
tenant_id = "acme:corp"           # ✗ Characters :*?"<>| are blocked
workflow_id = "workflow*"         # ✗ Wildcards are blocked

# ALLOWED: Valid identifiers
tenant_id = "acme_corp"           # ✓ Alphanumeric with underscores
workflow_id = "weekly_report"     # ✓ Valid identifier
artifact_id = "report_2024.pdf"   # ✓ Valid with extension
```

### Validation Rules

The storage system implements these validation checks:

1. **No parent directory references**: `..` is blocked
2. **No absolute paths**: Paths starting with `/` or `\` are rejected
3. **No path separators**: Forward and backslashes are blocked in identifiers
4. **No wildcard characters**: `*`, `?` are forbidden
5. **No special characters**: `:`, `"`, `<`, `>`, `|` are blocked
6. **Non-empty identifiers**: Empty strings are rejected

### Cross-Tenant Prevention

Tenants cannot access each other's artifacts:

```python
# Tenant A writes artifact
write_artifact(
    tier="hot",
    tenant_id="tenant_a",
    workflow_id="secrets",
    artifact_id="api_key.txt",
    content=b"secret_key_123"
)

# Tenant B CANNOT read Tenant A's artifact
try:
    read_artifact(
        tier="hot",
        tenant_id="tenant_b",
        workflow_id="secrets",
        artifact_id="api_key.txt"  # Different tenant path
    )
except ArtifactNotFoundError:
    print("Cross-tenant access blocked")
```

### Audit Events for All Operations

All storage operations emit audit events to `logs/lifecycle_events.jsonl`:

**Write Operation:**
```json
{
  "timestamp": "2024-01-15T10:30:00Z",
  "event_type": "artifact_written",
  "tenant_id": "acme_corp",
  "workflow_id": "weekly_report",
  "artifact_id": "report.pdf",
  "tier": "hot",
  "size_bytes": 51200,
  "user_id": "alice@acme.com"
}
```

**Promotion:**
```json
{
  "timestamp": "2024-01-22T02:00:00Z",
  "event_type": "promoted_to_warm",
  "tenant_id": "acme_corp",
  "workflow_id": "weekly_report",
  "artifact_id": "report.pdf",
  "age_days": 8.2,
  "from_tier": "hot",
  "to_tier": "warm",
  "dry_run": false
}
```

**Purge:**
```json
{
  "timestamp": "2024-04-15T02:00:00Z",
  "event_type": "purged_from_cold",
  "tenant_id": "acme_corp",
  "workflow_id": "weekly_report",
  "artifact_id": "report.pdf",
  "age_days": 95.3,
  "size_bytes": 51200,
  "dry_run": false
}
```

**Restoration:**
```json
{
  "timestamp": "2024-01-25T14:30:00Z",
  "event_type": "artifact_restored",
  "tenant_id": "acme_corp",
  "workflow_id": "weekly_report",
  "artifact_id": "report.pdf",
  "from_tier": "warm",
  "to_tier": "hot",
  "user_id": "bob@acme.com",
  "reason": "customer_request"
}
```

### Audit Log Access Control

Audit logs contain sensitive information and should be access-controlled:

```bash
# Restrict audit log permissions (Unix/Linux)
chmod 640 logs/lifecycle_events.jsonl
chown app_user:app_group logs/lifecycle_events.jsonl

# Or use ACLs for fine-grained control
setfacl -m u:audit_viewer:r logs/lifecycle_events.jsonl
```

### Monitoring Suspicious Activity

Set up alerts for suspicious storage operations:

```python
# Example: Monitor for excessive purge operations
import json
from datetime import datetime, timedelta

def check_purge_anomalies():
    """Alert if purge rate exceeds threshold."""
    recent_purges = []

    with open("logs/lifecycle_events.jsonl") as f:
        for line in f:
            event = json.loads(line)
            if event.get("event_type") == "purged_from_cold":
                recent_purges.append(event)

    # Check last hour
    one_hour_ago = datetime.utcnow() - timedelta(hours=1)
    recent = [
        e for e in recent_purges
        if datetime.fromisoformat(e["timestamp"]) > one_hour_ago
    ]

    if len(recent) > 100:  # Alert if >100 purges/hour
        send_alert(f"Anomalous purge rate: {len(recent)} purges in last hour")
```

### Data Retention Compliance

Configure retention policies to meet compliance requirements:

```bash
# GDPR/CCPA: 90 days for user data
export HOT_RETENTION_DAYS=7
export WARM_RETENTION_DAYS=30
export COLD_RETENTION_DAYS=90

# Healthcare: 7 years for medical records
export HOT_RETENTION_DAYS=30
export WARM_RETENTION_DAYS=365
export COLD_RETENTION_DAYS=2555  # ~7 years

# Financial: 10 years for transaction records
export COLD_RETENTION_DAYS=3650  # 10 years
```

### Encryption at Rest

For production deployments, enable filesystem encryption:

**Linux (LUKS):**
```bash
# Encrypt storage partition
cryptsetup luksFormat /dev/sdb1
cryptsetup open /dev/sdb1 artifacts_encrypted
mkfs.ext4 /dev/mapper/artifacts_encrypted
mount /dev/mapper/artifacts_encrypted /mnt/artifacts
```

**AWS (S3 with KMS):**
```python
import boto3

s3 = boto3.client('s3')

# Enable default encryption for bucket
s3.put_bucket_encryption(
    Bucket='artifacts-bucket',
    ServerSideEncryptionConfiguration={
        'Rules': [{
            'ApplyServerSideEncryptionByDefault': {
                'SSEAlgorithm': 'aws:kms',
                'KMSMasterKeyID': 'arn:aws:kms:region:account:key/id'
            }
        }]
    }
)
```

### Secure Deletion

For sensitive artifacts, use secure deletion:

```python
import os
import secrets

def secure_delete(file_path):
    """
    Securely delete file by overwriting with random data.

    WARNING: This is only effective on traditional filesystems,
    not SSD, cloud storage, or copy-on-write filesystems.
    """
    if not os.path.exists(file_path):
        return

    file_size = os.path.getsize(file_path)

    # Overwrite with random data 3 times
    for _ in range(3):
        with open(file_path, 'wb') as f:
            f.write(secrets.token_bytes(file_size))
        os.fsync(f.fileno())

    # Finally delete
    os.unlink(file_path)
```

### Backup Security

Protect backups with encryption:

```bash
# Encrypted backup with GPG
tar -czf - artifacts/ | \
  gpg --encrypt --recipient backup@company.com \
  > backups/artifacts_$(date +%Y%m%d).tar.gz.gpg

# Restore encrypted backup
gpg --decrypt backups/artifacts_20240115.tar.gz.gpg | \
  tar -xzf - -C /restore/location/
```

### Access Logging

Log all artifact access for audit trail:

```python
from src.storage.lifecycle import log_lifecycle_event

def log_artifact_access(tenant_id, workflow_id, artifact_id, user_id):
    """Log artifact access event."""
    log_lifecycle_event({
        "event_type": "artifact_accessed",
        "tenant_id": tenant_id,
        "workflow_id": workflow_id,
        "artifact_id": artifact_id,
        "user_id": user_id,
        "ip_address": request.remote_addr,
        "user_agent": request.headers.get("User-Agent")
    })
```

### Security Best Practices

1. **Principle of Least Privilege**: Grant minimum necessary permissions
2. **Defense in Depth**: Layer multiple security controls (path validation + ACLs + audit)
3. **Regular Audits**: Review audit logs for suspicious patterns
4. **Secure Defaults**: Restrictive permissions by default
5. **Fail Securely**: Deny access on errors rather than allowing
6. **Validate Input**: Never trust tenant/workflow/artifact IDs from external sources
7. **Monitor Anomalies**: Alert on unusual access patterns or purge rates
8. **Encrypt Sensitive Data**: Use encryption at rest for compliance
9. **Rotate Keys**: Regularly rotate encryption keys
10. **Test Security**: Include security tests in CI/CD pipeline

### Security Testing

Test path traversal prevention:

```python
# tests/test_storage_security.py
import pytest
from src.storage.tiered_store import write_artifact, InvalidTenantPathError

def test_path_traversal_blocked():
    """Test that path traversal attempts are blocked."""
    with pytest.raises(InvalidTenantPathError):
        write_artifact(
            tier="hot",
            tenant_id="../../../etc",
            workflow_id="passwd",
            artifact_id="shadow",
            content=b"hacker"
        )

def test_cross_tenant_access_blocked():
    """Test that tenants cannot access each other's artifacts."""
    # Tenant A writes artifact
    write_artifact("hot", "tenant_a", "wf", "secret.txt", b"secret")

    # Tenant B cannot read it (different path)
    with pytest.raises(ArtifactNotFoundError):
        read_artifact("hot", "tenant_b", "wf", "secret.txt")
```

### Incident Response

If security breach detected:

1. **Isolate**: Immediately revoke access credentials
2. **Investigate**: Review audit logs for scope of breach
3. **Contain**: Block affected tenant/user accounts
4. **Remediate**: Patch vulnerabilities, rotate keys
5. **Notify**: Inform affected parties per compliance requirements
6. **Document**: Record incident details and response actions
7. **Review**: Update security procedures to prevent recurrence

### See Also

- [STORAGE.md](./STORAGE.md) - Complete storage documentation
- [OPERATIONS.md](./OPERATIONS.md) - Operational procedures including lifecycle management

## Next Steps

1. Enable RBAC enforcement: `FEATURE_RBAC_ENFORCE=true`
2. Configure tenant isolation in deployment
3. Set up audit log monitoring and alerts
4. Review and assign roles to existing users
5. Document tenant onboarding process
6. Configure per-tenant concurrency limits based on tier
7. Enable global rate limiting: `GLOBAL_QPS_LIMIT=100`
8. Set up monitoring for limit violations
9. Create `.env.local` with production secrets
10. Configure secrets manager for cloud deployments
11. Schedule API key rotation reminders
12. Test cost anomaly detection
13. Document incident response procedures
14. Configure storage encryption at rest
15. Set up lifecycle audit log monitoring
16. Test path traversal prevention in CI/CD
17. Configure retention policies for compliance
