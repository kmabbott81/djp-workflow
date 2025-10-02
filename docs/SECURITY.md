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

## Next Steps

1. Enable RBAC enforcement: `FEATURE_RBAC_ENFORCE=true`
2. Configure tenant isolation in deployment
3. Set up audit log monitoring and alerts
4. Review and assign roles to existing users
5. Document tenant onboarding process
