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

## Next Steps

1. Enable RBAC enforcement: `FEATURE_RBAC_ENFORCE=true`
2. Configure tenant isolation in deployment
3. Set up audit log monitoring and alerts
4. Review and assign roles to existing users
5. Document tenant onboarding process
6. Configure per-tenant concurrency limits based on tier
7. Enable global rate limiting: `GLOBAL_QPS_LIMIT=100`
8. Set up monitoring for limit violations
