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

### Template Registry (Sprint 32)

Template authoring and deprecation require elevated permissions:

| Operation | Required Role | Notes |
|-----------|---------------|-------|
| Register template | Author or Admin | Creates new versioned template |
| Deprecate template | Author or Admin | Marks version as deprecated |
| List templates | Any role | Read-only operation |
| Show template | Any role | Read-only operation |
| Use template in DAG | Any role | Execution with validation |

**Role hierarchy (Sprint 34A updated):**
```
Viewer (0) < Author (1) < Operator (2) < Auditor (3) < Compliance (4) < Admin (5)
```

**Environment variables:**
```bash
TEMPLATE_RBAC_ROLE=Author  # Required role for write ops (default: Author)
USER_RBAC_ROLE=Author      # User's current role
```

**Audit trail:** All template operations are logged to `templates/registry/templates.jsonl` with timestamp, owner, and operation type.

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

## Cost Governance Security (Sprint 30)

Sprint 30 introduces budget enforcement with governance event logging and RBAC controls.

### Governance Event Auditing

All budget enforcement decisions are logged to `logs/governance_events.jsonl`:

```json
{
  "event": "budget_deny",
  "tenant": "tenant-1",
  "reason": "daily_budget_exceeded",
  "daily_spend": 15.0,
  "daily_budget": 10.0,
  "timestamp": "2025-10-03T12:00:00Z"
}
```

**Event Types:**
- `budget_throttle`: Approaching budget threshold (soft limit)
- `budget_deny`: Budget exceeded (hard limit)
- `cost_anomaly`: Unusual spending detected
- `alert`: Budget-related alerts

### RBAC for Budget Configuration

Budget configuration follows strict RBAC controls:

| Resource | Viewer | Editor | Admin | Deployer |
|----------|--------|--------|-------|----------|
| View budgets | ✅ | ✅ | ✅ | ✅ |
| View governance events | ✅ | ✅ | ✅ | ✅ |
| Modify budgets (YAML) | ❌ | ❌ | ✅ | ✅ |
| Set env budgets | ❌ | ❌ | ✅ | ✅ |
| Replay DLQ jobs | ❌ | ❌ | ✅ | ✅ |

### Budget File Permissions

Secure budget configuration files:

```bash
# config/budgets.yaml - read-only for workers
chmod 644 config/budgets.yaml
chown admin:workers config/budgets.yaml

# logs/governance_events.jsonl - append-only for workers
chmod 644 logs/governance_events.jsonl
chown admin:workers logs/governance_events.jsonl
```

### Monitoring Governance Events

Watch for suspicious budget activity:

```bash
# Monitor budget denials
tail -f logs/governance_events.jsonl | grep '"event":"budget_deny"'

# Count denials per tenant
cat logs/governance_events.jsonl | jq -r 'select(.event=="budget_deny") | .tenant' | sort | uniq -c

# Detect anomalies
cat logs/governance_events.jsonl | jq -r 'select(.event=="cost_anomaly")'

# Alert on repeated denials (potential abuse)
cat logs/governance_events.jsonl | jq -r 'select(.event=="budget_deny") | .tenant' | sort | uniq -c | awk '$1 > 10 {print $2}'
```

### Budget Audit Trail

Governance events provide a complete audit trail:

1. **Who**: Tenant ID in every event
2. **What**: Event type (throttle, deny, anomaly)
3. **When**: ISO 8601 timestamp
4. **Why**: Reason (daily_budget_exceeded, anomaly_detected, etc.)
5. **Context**: Spend amounts, budget limits, thresholds

### Compliance Considerations

- **Retention**: Keep governance events for 90+ days for auditing
- **Access Control**: Restrict budget modification to admins only
- **Change Tracking**: Log all budget configuration changes
- **Alerting**: Configure alerts for repeated budget denials
- **Review**: Monthly review of governance events and budget trends

See [COSTS.md](COSTS.md) for complete budget governance documentation.

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

## Provisioning & Least Privilege

Production-ready provisioning workflows following security best practices.

### Bootstrap Process Overview

The bootstrap process establishes the initial administrative user and tenant:

```
Initial State → Bootstrap Admin → Create Tenants → Provision Teams → Assign Roles
```

**Security principles:**
1. **Single Admin Bootstrap**: Only one admin created during initial setup
2. **Explicit Tenant Assignment**: Every user belongs to a specific tenant
3. **Least Privilege by Default**: Start with minimal permissions, escalate only when needed
4. **Audit from Day One**: All bootstrap actions logged

### Admin Role Provisioning

#### Bootstrap First Admin

**One-time setup:**

```bash
# Run bootstrap script
python scripts/bootstrap.py \
  --admin-email admin@example.com \
  --tenant-id default \
  --admin-name "System Administrator"

# Expected output:
# ✓ Created tenant: default
# ✓ Created admin user: admin@example.com
# ✓ Granted Admin role
# ✓ Bootstrap complete
```

**What bootstrap creates:**
- Default tenant (`default` or custom ID)
- Admin user with full permissions
- Initial audit log entry
- Configuration validation

**Bootstrap script security:**
- Runs only once (idempotent checks)
- Requires confirmation for production environments
- Logs all actions to `audit/bootstrap.jsonl`
- Validates email format and tenant ID

#### Verify Admin Provisioning

```bash
# Check admin user exists
python -c "
from src.security.authz import Principal, Role
principal = Principal(
    user_id='admin@example.com',
    tenant_id='default',
    role=Role.ADMIN,
    email='admin@example.com'
)
print(f'Admin: {principal.user_id}, Role: {principal.role.name}')
"

# Verify admin permissions
python scripts/rbac_check.py \
  --user admin@example.com \
  --tenant default \
  --action execute \
  --resource workflow

# Expected: ✓ Permission granted
```

#### Emergency Admin Access

For disaster recovery or admin lockout:

```bash
# Create emergency admin (requires server access)
python scripts/emergency_admin.py \
  --email emergency@example.com \
  --tenant default \
  --reason "Admin account locked, ticket #12345"

# This logs to audit/emergency_access.jsonl
# Review logs monthly for unauthorized usage
```

### Least Privilege Principles

**Core principle:** Grant minimum necessary permissions for users to perform their job functions.

#### Role Hierarchy

```
Viewer (0) - Read-only access
    ↓
Author (1) - Create templates
    ↓
Operator (2) - Execute workflows, approve checkpoints
    ↓
Auditor (3) - Export data, read-only compliance
    ↓
Compliance (4) - Data lifecycle, deletions, holds
    ↓
Admin (5) - Full system access
```

**Grant roles from lowest to highest as needed:**

```bash
# Start with Viewer (default)
USER_ROLE=Viewer

# Escalate to Operator only when needed
USER_ROLE=Operator

# Grant Admin only to ops team
USER_ROLE=Admin
```

#### Permission Matrix

| Operation | Viewer | Author | Operator | Auditor | Compliance | Admin |
|-----------|--------|--------|----------|---------|------------|-------|
| Read templates | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Create templates | ❌ | ✓ | ✓ | ✓ | ✓ | ✓ |
| Execute workflows | ❌ | ❌ | ✓ | ❌ | ✓ | ✓ |
| Approve checkpoints | ❌ | ❌ | ✓ | ❌ | ✓ | ✓ |
| Export data | ❌ | ❌ | ❌ | ✓ | ✓ | ✓ |
| Delete data | ❌ | ❌ | ❌ | ❌ | ✓ | ✓ |
| Modify RBAC | ❌ | ❌ | ❌ | ❌ | ❌ | ✓ |

### Team and Workspace Setup

#### Create Teams

**Engineering Team:**

```bash
# Create team
python scripts/teams.py create \
  --team-id eng-team \
  --name "Engineering Team" \
  --description "Software engineers and developers"

# Add members with appropriate roles
python scripts/teams.py add-member \
  --team-id eng-team \
  --user-id developer1@example.com \
  --role Operator

python scripts/teams.py add-member \
  --team-id eng-team \
  --user-id developer2@example.com \
  --role Author

# Set team budget
python scripts/teams.py set-budget \
  --team-id eng-team \
  --daily 10.0 \
  --monthly 200.0
```

**Operations Team:**

```bash
# Create ops team
python scripts/teams.py create \
  --team-id ops-team \
  --name "Operations Team"

# Add ops members (higher privileges)
python scripts/teams.py add-member \
  --team-id ops-team \
  --user-id ops1@example.com \
  --role Admin

python scripts/teams.py add-member \
  --team-id ops-team \
  --user-id ops2@example.com \
  --role Deployer
```

**Compliance Team:**

```bash
# Create compliance team
python scripts/teams.py create \
  --team-id compliance-team \
  --name "Compliance Team"

# Add compliance members
python scripts/teams.py add-member \
  --team-id compliance-team \
  --user-id auditor@example.com \
  --role Auditor

python scripts/teams.py add-member \
  --team-id compliance-team \
  --user-id compliance@example.com \
  --role Compliance
```

#### Create Workspaces

**Production Workspace (restricted access):**

```bash
# Create production workspace
python scripts/workspaces.py create \
  --workspace-id prod \
  --name "Production Environment" \
  --description "Production workflows and artifacts"

# Add only trusted members
python scripts/workspaces.py add-member \
  --workspace-id prod \
  --user-id ops1@example.com \
  --role Admin

python scripts/workspaces.py add-member \
  --workspace-id prod \
  --user-id senior-dev@example.com \
  --role Operator
```

**Staging Workspace (broader access):**

```bash
# Create staging workspace
python scripts/workspaces.py create \
  --workspace-id staging \
  --name "Staging Environment"

# Add all engineers
python scripts/workspaces.py add-member \
  --workspace-id staging \
  --user-id developer1@example.com \
  --role Operator
```

**Development Workspace (open access):**

```bash
# Create dev workspace
python scripts/workspaces.py create \
  --workspace-id dev \
  --name "Development Environment"

# Add all team members (relaxed permissions)
python scripts/workspaces.py add-member \
  --workspace-id dev \
  --user-id developer1@example.com \
  --role Admin  # Developers can be admins in dev

python scripts/workspaces.py add-member \
  --workspace-id dev \
  --user-id developer2@example.com \
  --role Admin
```

### RBAC Best Practices

#### 1. Start with Minimal Permissions

**New user onboarding:**

```bash
# Step 1: Create user with Viewer role
python scripts/users.py create \
  --email newuser@example.com \
  --tenant default \
  --role Viewer

# Step 2: Assign to team (inherits team permissions)
python scripts/teams.py add-member \
  --team-id eng-team \
  --user-id newuser@example.com \
  --role Viewer

# Step 3: Monitor activity for 1 week
python scripts/audit.py query \
  --user newuser@example.com \
  --since 7d

# Step 4: Escalate role if needed
python scripts/teams.py update-member \
  --team-id eng-team \
  --user-id newuser@example.com \
  --role Author
```

#### 2. Use Time-Bounded Delegations

**Temporary elevated access:**

```bash
# Grant Admin role for on-call shift (8 hours)
python scripts/delegation.py grant \
  --granter admin@example.com \
  --grantee oncall@example.com \
  --scope team \
  --scope-id eng-team \
  --role Admin \
  --duration 8h \
  --reason "On-call shift 2025-10-04 22:00-06:00"

# Delegation expires automatically
# No manual revocation needed
```

**Emergency access (expires faster):**

```bash
# Grant Compliance role for 1 hour
python scripts/delegation.py grant \
  --granter admin@example.com \
  --grantee support@example.com \
  --scope workspace \
  --scope-id prod \
  --role Compliance \
  --duration 1h \
  --reason "Emergency data export for customer #12345"
```

#### 3. Regular Access Reviews

**Quarterly access review:**

```bash
# List all team memberships
python scripts/teams.py list --show-members

# Review delegations
python scripts/delegation.py list --active

# Identify stale accounts
python scripts/users.py audit --inactive-days 90

# Revoke unnecessary permissions
python scripts/teams.py remove-member \
  --team-id eng-team \
  --user-id inactive@example.com
```

**Audit script:**

```bash
#!/bin/bash
# Quarterly access review script

echo "=== Access Review $(date +%Y-%m-%d) ==="

# 1. List all admin users
echo "Admins:"
python scripts/users.py list --role Admin

# 2. List active delegations
echo "Active delegations:"
python scripts/delegation.py list --active

# 3. Find users with no activity in 90 days
echo "Inactive users:"
python scripts/users.py audit --inactive-days 90

# 4. Review team memberships
echo "Team memberships:"
python scripts/teams.py list --show-members > access-review-$(date +%Y%m%d).txt

echo "Review complete. See access-review-$(date +%Y%m%d).txt"
```

#### 4. Separate Duties

**Principle:** No single person should control all aspects of a critical process.

**Example: Production deployment**

```bash
# Developer creates template (Author role)
python -m src.run_workflow --template deploy_prod --dry-run

# Approver reviews checkpoint (Operator role)
python scripts/approvals.py approve prod_deploy_checkpoint_123

# Deployer executes (Admin role)
python scripts/deploy.py execute --workspace prod
```

**Multi-sign for high-risk operations:**

```bash
# Require 2 of 3 signatures for production deletion
python scripts/compliance.py delete \
  --tenant prod-tenant \
  --require-signatures "ops1@example.com,ops2@example.com,admin@example.com" \
  --min-signatures 2
```

#### 5. Monitor Privilege Escalation

**Alert on unexpected role changes:**

```bash
# Monitor audit logs for role changes
grep "role_change\|delegation_grant" logs/audit-*.jsonl | \
  jq -r 'select(.new_role == "Admin" or .granted_role == "Admin")'

# Alert if Admin role granted outside business hours
HOUR=$(date +%H)
if [ $HOUR -lt 8 ] || [ $HOUR -gt 18 ]; then
  ADMIN_GRANTS=$(grep "role_change.*Admin" logs/audit-$(date +%Y-%m-%d).jsonl | wc -l)
  if [ $ADMIN_GRANTS -gt 0 ]; then
    echo "ALERT: Admin role granted outside business hours"
  fi
fi
```

### Provisioning Workflows

#### New Developer Onboarding

```bash
#!/bin/bash
# Onboard new developer

USER_EMAIL=$1
TEAM_ID=${2:-eng-team}

# 1. Create user (Viewer role by default)
python scripts/users.py create \
  --email $USER_EMAIL \
  --tenant default \
  --role Viewer

# 2. Add to team (Author role for developers)
python scripts/teams.py add-member \
  --team-id $TEAM_ID \
  --user-id $USER_EMAIL \
  --role Author

# 3. Grant access to dev workspace (Admin in dev)
python scripts/workspaces.py add-member \
  --workspace-id dev \
  --user-id $USER_EMAIL \
  --role Admin

# 4. Grant access to staging workspace (Operator)
python scripts/workspaces.py add-member \
  --workspace-id staging \
  --user-id $USER_EMAIL \
  --role Operator

# 5. Log onboarding action
echo "{\"timestamp\": \"$(date -Iseconds)\", \"event\": \"user_onboarded\", \"user\": \"$USER_EMAIL\", \"team\": \"$TEAM_ID\"}" >> logs/provisioning.jsonl

echo "✓ Onboarded $USER_EMAIL to $TEAM_ID"
echo "Roles:"
echo "  - Dev workspace: Admin"
echo "  - Staging workspace: Operator"
echo "  - Team: Author"
```

#### Contractor Offboarding

```bash
#!/bin/bash
# Offboard contractor (remove all access)

USER_EMAIL=$1

# 1. List current memberships
echo "Removing access for $USER_EMAIL:"
python scripts/teams.py list-user --user-id $USER_EMAIL
python scripts/workspaces.py list-user --user-id $USER_EMAIL

# 2. Revoke all delegations
python scripts/delegation.py revoke-all --grantee $USER_EMAIL

# 3. Remove from all teams
for TEAM in $(python scripts/teams.py list-user --user-id $USER_EMAIL | jq -r '.team_id'); do
  python scripts/teams.py remove-member --team-id $TEAM --user-id $USER_EMAIL
done

# 4. Remove from all workspaces
for WORKSPACE in $(python scripts/workspaces.py list-user --user-id $USER_EMAIL | jq -r '.workspace_id'); do
  python scripts/workspaces.py remove-member --workspace-id $WORKSPACE --user-id $USER_EMAIL
done

# 5. Mark user as inactive
python scripts/users.py deactivate --user-id $USER_EMAIL

# 6. Log offboarding action
echo "{\"timestamp\": \"$(date -Iseconds)\", \"event\": \"user_offboarded\", \"user\": \"$USER_EMAIL\"}" >> logs/provisioning.jsonl

echo "✓ Offboarded $USER_EMAIL"
```

#### Role Promotion

```bash
#!/bin/bash
# Promote user to higher role

USER_EMAIL=$1
NEW_ROLE=$2
REASON=$3

# 1. Verify current role
CURRENT_ROLE=$(python scripts/users.py show --user-id $USER_EMAIL | jq -r '.role')
echo "Current role: $CURRENT_ROLE → Promoting to: $NEW_ROLE"

# 2. Update team memberships
python scripts/teams.py update-member \
  --team-id eng-team \
  --user-id $USER_EMAIL \
  --role $NEW_ROLE

# 3. Grant prod access if Operator or above
if [ "$NEW_ROLE" = "Operator" ] || [ "$NEW_ROLE" = "Admin" ]; then
  python scripts/workspaces.py add-member \
    --workspace-id prod \
    --user-id $USER_EMAIL \
    --role Operator
fi

# 4. Log promotion
echo "{\"timestamp\": \"$(date -Iseconds)\", \"event\": \"role_promoted\", \"user\": \"$USER_EMAIL\", \"old_role\": \"$CURRENT_ROLE\", \"new_role\": \"$NEW_ROLE\", \"reason\": \"$REASON\"}" >> logs/provisioning.jsonl

echo "✓ Promoted $USER_EMAIL to $NEW_ROLE"
```

### Provisioning Checklist

#### New User
- [ ] Create user with Viewer role (least privilege)
- [ ] Assign to appropriate team(s)
- [ ] Grant workspace access (dev/staging only initially)
- [ ] Document provisioning reason in audit log
- [ ] Schedule 30-day access review
- [ ] Notify user of access granted

#### Role Change
- [ ] Verify business justification
- [ ] Get manager approval
- [ ] Update team memberships
- [ ] Update workspace memberships
- [ ] Log role change with reason
- [ ] Notify user of new permissions
- [ ] Update access review schedule

#### User Offboarding
- [ ] Revoke all delegations
- [ ] Remove from all teams
- [ ] Remove from all workspaces
- [ ] Deactivate user account
- [ ] Revoke API keys/tokens
- [ ] Archive user data (if required)
- [ ] Log offboarding event
- [ ] Notify manager of completion

### Monitoring Provisioning

**Daily provisioning report:**

```bash
# Count provisioning events
echo "Provisioning activity (last 24 hours):"
echo "Users created: $(grep "user_created" logs/provisioning.jsonl | grep $(date +%Y-%m-%d) | wc -l)"
echo "Users offboarded: $(grep "user_offboarded" logs/provisioning.jsonl | grep $(date +%Y-%m-%d) | wc -l)"
echo "Role changes: $(grep "role_promoted" logs/provisioning.jsonl | grep $(date +%Y-%m-%d) | wc -l)"
echo "Delegations granted: $(grep "delegation_grant" logs/delegations.jsonl | grep $(date +%Y-%m-%d) | wc -l)"
```

**Alert on suspicious activity:**

```bash
# Alert if >10 users created in 1 hour
RECENT_USERS=$(grep "user_created" logs/provisioning.jsonl | grep $(date -d "1 hour ago" +%Y-%m-%d) | wc -l)
if [ $RECENT_USERS -gt 10 ]; then
  echo "ALERT: Unusual provisioning activity - $RECENT_USERS users created in 1 hour"
fi

# Alert if Admin role granted to more than 1 user per day
ADMIN_GRANTS=$(grep "role_promoted.*Admin" logs/provisioning.jsonl | grep $(date +%Y-%m-%d) | wc -l)
if [ $ADMIN_GRANTS -gt 1 ]; then
  echo "ALERT: Multiple Admin promotions today - $ADMIN_GRANTS"
fi
```

### Related Documentation

- [AUTH.md](./AUTH.md) - Authentication and authorization
- [COLLABORATION.md](./COLLABORATION.md) - Teams and workspaces
- [OPERATIONS.md](./OPERATIONS.md) - Operational procedures
- [ONBOARDING.md](./ONBOARDING.md) - User onboarding guide

## Connector Security (Sprint 37+)

### Gmail Connector Token Handling

Gmail connector uses OAuth2 with the following security measures:

**Token Storage:**
- Tokens stored in unified OAuth2 token store
- Multi-tenant isolation via `gmail:{tenant_id}` key format
- Examples: `gmail:acme-corp`, `gmail:beta-test`
- Never logged or exposed in error messages

**OAuth2 Scopes:**
- Minimal scopes principle
- Read-only: `https://www.googleapis.com/auth/gmail.readonly`
- Full access: `gmail.readonly`, `gmail.modify`, `gmail.labels`
- Document required scopes in connector registration

**RBAC Enforcement:**
| Operation | Minimum Role |
|-----------|--------------|
| list_resources | Operator |
| get_resource | Operator |
| create_resource | Admin |
| update_resource | Admin |
| delete_resource | Admin |

**Token Refresh:**
- Automatic refresh when tokens expire (when implemented)
- Refresh tokens stored securely
- No token reuse across tenants

**Security Best Practices:**
1. Use service accounts for production
2. Enable Google Cloud audit logs
3. Monitor Gmail API quota usage
4. Implement rate limiting at application level
5. Review OAuth2 consent screen regularly
6. Revoke unused tokens via Google Account settings

### Other Connectors (Teams, Outlook, Slack)

Similar security patterns apply:
- See [CONNECTORS_TEAMS.md](./CONNECTORS_TEAMS.md) for Microsoft Graph security
- See [CONNECTORS_OUTLOOK.md](./CONNECTORS_OUTLOOK.md) for Outlook-specific guidance
- See [CONNECTORS_SLACK.md](./CONNECTORS_SLACK.md) for Slack bot token handling

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

## Checkpoint Approvals & RBAC (Sprint 31)

Sprint 31 introduces human-in-the-loop approvals with role-based access control for checkpoint tasks in DAG workflows.

### RBAC Role Hierarchy

Checkpoint approvals use a hierarchical role system:

| Role | Level | Permissions | Can Approve |
|------|-------|-------------|-------------|
| **Viewer** | 0 | Read-only access | None |
| **Operator** | 1 | Can approve Operator checkpoints | Operator, Viewer |
| **Admin** | 2 | Can approve any checkpoint | All roles |

**Permission model:**
- A role can approve checkpoints at its own level or below
- Higher-level roles inherit lower-level permissions
- Checkpoints specify `required_role` (minimum role needed to approve)

**Example scenarios:**

```python
# Operator checkpoint
checkpoint = {
    "required_role": "Operator",
    "prompt": "Approve weekly report?"
}

# Viewer CANNOT approve (level 0 < 1)
can_approve("Viewer", "Operator")  # → False

# Operator CAN approve (level 1 >= 1)
can_approve("Operator", "Operator")  # → True

# Admin CAN approve (level 2 >= 1)
can_approve("Admin", "Operator")  # → True

# Admin checkpoint
checkpoint = {
    "required_role": "Admin",
    "prompt": "Approve production deployment?"
}

# Operator CANNOT approve (level 1 < 2)
can_approve("Operator", "Admin")  # → False

# Admin CAN approve (level 2 >= 2)
can_approve("Admin", "Admin")  # → True
```

### Environment Variables

Configure checkpoint RBAC via environment variables:

```bash
# User's role for approvals (default: Viewer)
export USER_RBAC_ROLE=Operator

# Approver role for automated systems (optional)
export APPROVER_RBAC_ROLE=Admin

# Checkpoint expiration (default: 72 hours)
export APPROVAL_EXPIRES_H=72
```

**Role assignment:**
- Set `USER_RBAC_ROLE` before running approval commands
- Role persists for the session/process lifetime
- Different users can have different roles
- No role = defaults to Viewer (cannot approve anything)

**Usage:**

```bash
# Set role
export USER_RBAC_ROLE=Operator

# Approve checkpoint
python scripts/approvals.py approve abc123_checkpoint

# Verify role
echo $USER_RBAC_ROLE
```

### Audit Surfaces

Checkpoint approval decisions are logged to multiple audit surfaces:

#### 1. Checkpoints Log (`logs/checkpoints.jsonl`)

All checkpoint lifecycle events:

```json
{
  "timestamp": "2025-10-03T14:30:00Z",
  "event": "checkpoint_created",
  "checkpoint_id": "abc123_approval",
  "dag_run_id": "abc123",
  "task_id": "approval",
  "tenant": "tenant-a",
  "prompt": "Approve weekly report?",
  "required_role": "Operator"
}

{
  "timestamp": "2025-10-03T14:35:00Z",
  "event": "checkpoint_approved",
  "checkpoint_id": "abc123_approval",
  "approved_by": "Admin",
  "approval_data": {"signoff": "Approved by manager"},
  "approved_at": "2025-10-03T14:35:00Z"
}

{
  "timestamp": "2025-10-03T14:36:00Z",
  "event": "checkpoint_rejected",
  "checkpoint_id": "def456_approval",
  "rejected_by": "Operator",
  "reject_reason": "Budget concerns",
  "rejected_at": "2025-10-03T14:36:00Z"
}

{
  "timestamp": "2025-10-06T14:30:00Z",
  "event": "checkpoint_expired",
  "checkpoint_id": "ghi789_approval",
  "expired_at": "2025-10-06T14:30:00Z",
  "age_hours": 72
}
```

**Event types:**
- `checkpoint_created` - Checkpoint created and awaiting approval
- `checkpoint_approved` - Approved by user with role
- `checkpoint_rejected` - Rejected with reason
- `checkpoint_expired` - Automatically expired after timeout

#### 2. State Store (`logs/orchestrator_state.jsonl`)

DAG resumption and scheduler events:

```json
{
  "timestamp": "2025-10-03T14:30:00Z",
  "event": "resume_token",
  "dag_run_id": "abc123",
  "next_task_id": "weekly_report",
  "tenant": "tenant-a"
}

{
  "timestamp": "2025-10-06T02:00:00Z",
  "event": "checkpoint_expired",
  "checkpoint_id": "abc123_approval",
  "dag_run_id": "abc123",
  "task_id": "approval"
}
```

**Event types:**
- `resume_token` - Token written when DAG pauses at checkpoint
- `checkpoint_expired` - Scheduler-emitted expiration event

#### 3. Orchestrator Events (`logs/orchestrator_events.jsonl`)

Task-level DAG execution events:

```json
{
  "timestamp": "2025-10-03T14:30:00Z",
  "event": "checkpoint_pending",
  "dag_run_id": "abc123",
  "task_id": "approval",
  "checkpoint_id": "abc123_approval"
}

{
  "timestamp": "2025-10-03T14:35:00Z",
  "event": "checkpoint_approved",
  "dag_run_id": "abc123",
  "task_id": "approval",
  "checkpoint_id": "abc123_approval"
}

{
  "timestamp": "2025-10-03T14:36:00Z",
  "event": "dag_done",
  "dag_run_id": "abc123",
  "status": "success"
}
```

### Querying Audit Logs

**All approvals by role:**

```bash
grep "checkpoint_approved" logs/checkpoints.jsonl | jq -r '.approved_by' | sort | uniq -c
```

**Rejections with reasons:**

```bash
grep "checkpoint_rejected" logs/checkpoints.jsonl | jq -r '[.checkpoint_id, .rejected_by, .reject_reason] | @tsv'
```

**Expired checkpoints:**

```bash
grep "checkpoint_expired" logs/checkpoints.jsonl | tail -20
```

**RBAC violations (insufficient role):**

```bash
# Check for approval attempts that failed due to role
# (These would appear in application logs, not checkpoint logs)
grep "cannot approve" logs/approvals.log
```

**Approvals for specific tenant:**

```bash
grep "checkpoint_approved" logs/checkpoints.jsonl | jq -r 'select(.tenant == "tenant-a")'
```

**Approval timeline for compliance:**

```bash
CHECKPOINT_ID="abc123_approval"
grep "$CHECKPOINT_ID" logs/checkpoints.jsonl | jq -r '[.timestamp, .event, .approved_by // .rejected_by // "system"] | @tsv'
```

### Retention Policy

**Recommended retention for checkpoint audit logs:**

- **Hot logs (current)**: 90 days minimum
- **Archived logs**: 2 years for compliance
- **Critical checkpoints**: 7 years (e.g., financial approvals, production deployments)

**Archive old logs:**

```bash
# Archive logs older than 90 days
python -c "
import json, gzip
from datetime import datetime, timedelta

cutoff = (datetime.now() - timedelta(days=90)).isoformat()

# Read all events
with open('logs/checkpoints.jsonl', 'r') as f:
    events = [json.loads(line) for line in f]

# Separate old and recent
old = [e for e in events if e['timestamp'] < cutoff]
recent = [e for e in events if e['timestamp'] >= cutoff]

# Archive old events
with gzip.open(f'logs/archives/checkpoints_{datetime.now().strftime(\"%Y%m%d\")}.jsonl.gz', 'wt') as f:
    for event in old:
        f.write(json.dumps(event) + '\n')

# Keep only recent in active log
with open('logs/checkpoints.jsonl', 'w') as f:
    for event in recent:
        f.write(json.dumps(event) + '\n')

print(f'Archived {len(old)} events, retained {len(recent)}')
"
```

### Security Best Practices

#### 1. Principle of Least Privilege

Assign minimum necessary role:

```bash
# Default: Viewer (read-only, no approvals)
export USER_RBAC_ROLE=Viewer

# Grant Operator only when needed
export USER_RBAC_ROLE=Operator

# Restrict Admin to ops team
export USER_RBAC_ROLE=Admin
```

#### 2. Audit All Approval Actions

Monitor for suspicious approval patterns:

```bash
# Alert on excessive rejections
REJECT_COUNT=$(grep "checkpoint_rejected" logs/checkpoints.jsonl | wc -l)
if [ "$REJECT_COUNT" -gt 50 ]; then
    echo "ALERT: High rejection rate - possible workflow issues"
fi

# Alert on Admin overrides for Operator checkpoints
grep "checkpoint_approved" logs/checkpoints.jsonl | \
  jq -r 'select(.required_role == "Operator" and .approved_by == "Admin")' | \
  wc -l
```

#### 3. Expiration as Security Control

Expired checkpoints cannot be approved:

```bash
# Set stricter expiration for sensitive checkpoints
export APPROVAL_EXPIRES_H=24  # 1 day for critical approvals

# Monitor for expired checkpoints
grep "checkpoint_expired" logs/checkpoints.jsonl | tail -10
```

#### 4. Role Segregation

Separate approval roles by environment:

```bash
# Development: Relaxed
export USER_RBAC_ROLE=Admin

# Staging: Moderate
export USER_RBAC_ROLE=Operator

# Production: Strict
export USER_RBAC_ROLE=Operator  # Only Admins can override
```

#### 5. Dashboard Monitoring

Use observability dashboard to monitor checkpoint health:

```bash
streamlit run dashboards/app.py
```

Navigate to **Observability** → **✅ Checkpoint Approvals** to view:
- Pending checkpoints (alert if > 5)
- Recent approvals/rejections
- Expired checkpoints
- Approval rate by role

### Compliance Considerations

#### SOC 2 / ISO 27001

- **Access Control**: Role-based approval hierarchy enforces separation of duties
- **Audit Logging**: All approval decisions logged with timestamp, user, and role
- **Non-repudiation**: Approval events include approved_by field (immutable)
- **Traceability**: Complete audit trail from checkpoint creation to approval/rejection

#### GDPR

- **Right to Access**: Users can query their approval history
- **Data Minimization**: Audit logs contain only necessary fields
- **Retention**: Configurable retention policies (default 90 days)

#### HIPAA (Healthcare)

- **Access Controls**: Role hierarchy prevents unauthorized access
- **Audit Trails**: Complete audit of all approval decisions
- **Integrity**: Append-only JSONL prevents log tampering
- **Retention**: 7-year retention for compliance

### Testing RBAC

Test role hierarchy enforcement:

```python
import pytest
from src.security.rbac_check import can_approve

def test_viewer_cannot_approve_operator():
    """Test that Viewer role cannot approve Operator checkpoints."""
    assert not can_approve("Viewer", "Operator")

def test_operator_can_approve_operator():
    """Test that Operator can approve Operator checkpoints."""
    assert can_approve("Operator", "Operator")

def test_admin_can_approve_any():
    """Test that Admin can approve any checkpoint."""
    assert can_approve("Admin", "Operator")
    assert can_approve("Admin", "Admin")

def test_operator_cannot_approve_admin():
    """Test that Operator cannot approve Admin checkpoints."""
    assert not can_approve("Operator", "Admin")
```

### Incident Response

If unauthorized approval detected:

1. **Immediate**: Review audit logs to identify user and checkpoint
2. **Investigate**: Check if role was escalated or credentials compromised
3. **Contain**: Revoke user's role or rotate credentials
4. **Remediate**: Reject unauthorized approvals, re-run DAG if needed
5. **Document**: Record incident in security log
6. **Review**: Update RBAC policies to prevent recurrence

**Query unauthorized approvals:**

```bash
# Find approvals by Viewer (should be none)
grep "checkpoint_approved" logs/checkpoints.jsonl | jq -r 'select(.approved_by == "Viewer")'

# Find approvals where approved_by < required_role (should be none)
# (Requires manual inspection of role levels)
grep "checkpoint_approved" logs/checkpoints.jsonl | \
  jq -r 'select(.required_role == "Admin" and .approved_by != "Admin")'
```

### Related Documentation

- [ORCHESTRATION.md](./ORCHESTRATION.md) - Complete checkpoint documentation
- [OPERATIONS.md](./OPERATIONS.md) - Operational runbooks for checkpoint management

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
18. Set up checkpoint approval role hierarchy (Sprint 31)
19. Configure checkpoint expiration policies (default: 72h)
20. Monitor checkpoint audit logs for suspicious patterns
21. Test RBAC enforcement for checkpoint approvals

## Compliance Roles (Sprint 33A)

Sprint 33A introduces dedicated compliance roles for data lifecycle management operations including export, deletion, legal holds, and retention enforcement.

### Compliance Role Hierarchy

Extended role hierarchy with compliance operations:

| Role | Level | Export | Delete | Legal Hold | Retention |
|------|-------|--------|--------|------------|-----------|
| Viewer | 0 | ❌ | ❌ | ❌ | ❌ |
| Author | 1 | ❌ | ❌ | ❌ | ❌ |
| Operator | 2 | ❌ | ❌ | ❌ | ❌ |
| Auditor | 3 | ✅ | ❌ | ❌ (read-only) | ❌ |
| Compliance | 4 | ✅ | ✅ | ✅ | ✅ |
| Admin | 5 | ✅ | ✅ | ✅ | ✅ |

**Key principles:**
- **Auditor role**: Read-only access for compliance monitoring
- **Compliance role**: Full access to data lifecycle operations
- **Admin role**: Inherits all compliance permissions
- **Separation of duties**: Auditor can export but not delete

### Environment Variables

```bash
# Compliance RBAC
COMPLIANCE_RBAC_ROLE=Compliance  # Required role for mutating operations
USER_RBAC_ROLE=Auditor           # Current user's role

# Compliance paths
LOGS_LEGAL_HOLDS_PATH=logs/legal_holds.jsonl
EXPORT_ROOT=exports

# Retention policies (days)
RETAIN_ORCH_EVENTS_DAYS=90
RETAIN_QUEUE_EVENTS_DAYS=60
RETAIN_DLQ_DAYS=30
RETAIN_CHECKPOINTS_DAYS=90
RETAIN_COST_EVENTS_DAYS=180
RETAIN_GOV_EVENTS_DAYS=365
```

### Audit Guarantees

All compliance operations are fully audited with:

1. **Legal holds** logged to `logs/legal_holds.jsonl`:
   ```json
   {"timestamp": "...", "event": "hold_applied", "tenant": "...", "reason": "..."}
   ```

2. **Data export** operations logged to governance events
3. **Data deletion** operations logged to governance events
4. **Retention enforcement** runs logged with purge counts

### Compliance CLI Operations

**Export (Auditor+):**
```bash
python scripts/compliance.py export --tenant acme-corp --out ./exports
```

**Delete (Compliance+):**
```bash
python scripts/compliance.py delete --tenant acme-corp --dry-run
python scripts/compliance.py delete --tenant acme-corp
```

**Legal holds (Compliance+):**
```bash
python scripts/compliance.py hold --tenant acme-corp --reason "Litigation"
python scripts/compliance.py release --tenant acme-corp
python scripts/compliance.py holds --list
```

**Retention (Compliance+):**
```bash
python scripts/compliance.py retention
```

### Protection Mechanisms

1. **Legal hold blocks deletion**: Active legal holds prevent tenant deletion by default
2. **Dry-run mode**: Test deletion scope before executing
3. **RBAC enforcement**: All operations check user role before proceeding
4. **Audit trail**: Complete history of all compliance operations
5. **Safe JSONL pruning**: Retention uses temp file + atomic swap

### Exit Codes

Compliance CLI uses specific exit codes:
- `0` - Success
- `2` - RBAC denied (insufficient role)
- `3` - Legal hold active (blocks deletion)
- `1` - Other error

### Monitoring

Monitor compliance operations:

```bash
# Recent legal holds
tail -20 logs/legal_holds.jsonl

# Deletion operations
grep "delete" logs/governance_events.jsonl | tail -10

# Retention runs
grep "retention_enforced" logs/governance_events.jsonl
```

### Related Documentation

See [COMPLIANCE.md](./COMPLIANCE.md) for complete compliance documentation including workflows, examples, and troubleshooting.

## Clearance & Labels (Sprint 33B)

### Classification Hierarchy

Data classification labels follow a total order from least to most sensitive:

```
Public < Internal < Confidential < Restricted
```

### Clearance Model

User clearances follow the same hierarchy. Access is granted when:

```
user_clearance >= artifact_label
```

**Example**:
- User with `Confidential` clearance can access: Public, Internal, Confidential
- User with `Confidential` clearance **cannot** access: Restricted

### Configuration

```bash
# Classification labels (ordered, comma-separated)
CLASS_LABELS=Public,Internal,Confidential,Restricted

# Default label for unlabeled artifacts
DEFAULT_LABEL=Internal

# User's clearance level
USER_CLEARANCE=Operator  # Maps to Internal by default

# Require labels for export
REQUIRE_LABELS_FOR_EXPORT=true

# Export policy for insufficient clearance
EXPORT_POLICY=deny  # deny | redact
```

### Labeling Artifacts

#### Via CLI

```bash
# Set label
python scripts/classification.py set-label \
  --path artifacts/hot/tenant-a/report.md \
  --label Confidential

# View metadata
python scripts/classification.py show \
  --path artifacts/hot/tenant-a/report.md
```

#### Programmatically

```python
from src.storage.secure_io import write_encrypted

write_encrypted(
    path=Path("artifact.md"),
    data=b"content",
    label="Confidential",
    tenant="acme-corp"
)
```

### Access Enforcement

Read access checks clearance automatically:

```python
from src.storage.secure_io import read_encrypted

try:
    data = read_encrypted(
        Path("artifact.md"),
        user_clearance="Internal"
    )
except PermissionError:
    # Insufficient clearance
    pass
```

Export access enforced via compliance API:
- Unlabeled artifacts: Denied if `REQUIRE_LABELS_FOR_EXPORT=true`
- Insufficient clearance: Denied (or redacted) based on `EXPORT_POLICY`

### Audit Trail

All access denials logged to `logs/governance_events.jsonl`:

```json
{
  "timestamp": "2025-10-03T12:00:00Z",
  "event": "export_denied",
  "tenant": "acme-corp",
  "artifact": "artifacts/hot/acme-corp/report.md",
  "label": "Restricted",
  "user_clearance": "Confidential",
  "reason": "insufficient_clearance",
  "policy": "deny"
}
```

## Key Management & Rotation (Sprint 33B)

### Envelope Encryption

Artifacts encrypted with AES-256-GCM envelope encryption:

```
Plaintext → AES-256-GCM → Envelope {key_id, nonce, ciphertext, tag}
```

### Keyring Structure

Keys stored in `logs/keyring.jsonl` (append-only JSONL):

```jsonl
{"key_id": "key-001", "alg": "AES256-GCM", "status": "active", "created_at": "...", "key_material_base64": "..."}
{"key_id": "key-001", "alg": "AES256-GCM", "status": "retired", "retired_at": "..."}
{"key_id": "key-002", "alg": "AES256-GCM", "status": "active", "created_at": "...", "key_material_base64": "..."}
```

Last-wins semantics: Most recent entry for a `key_id` determines its status.

### Key Operations

```bash
# List keys (masks key material)
python scripts/keyring.py list

# Show active key
python scripts/keyring.py active

# Rotate key
python scripts/keyring.py rotate
```

Via compliance CLI:

```bash
python scripts/compliance.py list-keys
python scripts/compliance.py rotate-key
```

### Key Rotation

Rotation creates new active key and retires previous:

1. Current active key → status: `retired`
2. Generate new key with incremented ID
3. New key → status: `active`

**Historical data remains accessible**: Retired keys can still decrypt old artifacts.

### Rotation Policy

```bash
# Rotation interval (days)
KEY_ROTATION_DAYS=90
```

Dashboard shows warnings when key age exceeds policy.

### Encrypted Storage

Each artifact has two files:

```
artifact.md.enc     # Encrypted envelope (JSON)
artifact.md.json    # Metadata sidecar
```

**Sidecar metadata**:
```json
{
  "label": "Confidential",
  "tenant": "acme-corp",
  "key_id": "key-002",
  "created_at": "2025-10-03T12:00:00Z",
  "size": 1024,
  "encrypted": true
}
```

### Configuration

```bash
# Enable encryption
ENCRYPTION_ENABLED=true

# Keyring path
KEYRING_PATH=logs/keyring.jsonl

# Rotation policy
KEY_ROTATION_DAYS=90
```

### Security Guarantees

1. **AES-256-GCM**: Industry-standard authenticated encryption
2. **Unique nonces**: Random 96-bit nonce per encryption
3. **Tamper detection**: GCM tag verifies integrity
4. **Key isolation**: Key material never logged or exported
5. **Audit trail**: All key operations logged

### Backward Compatibility

If `ENCRYPTION_ENABLED=false`:
- Artifacts written as plaintext
- Plaintext artifacts remain readable
- Sidecar metadata still created with `encrypted: false`

### Key Recovery

**Prevention**: Back up `logs/keyring.jsonl` regularly

**Recovery**: Restore keyring from backup. Without backup, encrypted artifacts are unrecoverable.

### Related Documentation

- [ENCRYPTION.md](./ENCRYPTION.md) - Complete encryption guide
- [CLASSIFICATION.md](./CLASSIFICATION.md) - Classification labels guide
- [OPERATIONS.md](./OPERATIONS.md) - Key rotation runbook

## Collaborative Governance (Sprint 34A)

Sprint 34A introduces collaborative governance with teams, workspaces, delegations, and multi-sign approvals.

### Effective Role Resolution

User permissions are calculated as the **maximum** of:
1. Base role (team/workspace membership)
2. Active delegations (time-bounded grants)

```python
from src.security.delegation import active_role_for

# Get effective role considering delegations
role = active_role_for(user="bob", scope="team", scope_id="team-eng")
# Returns highest role from base + active delegations
```

### Multi-Sign Checkpoints

M-of-N approval pattern for critical decisions:

```python
from src.orchestrator.checkpoints import create_checkpoint, add_signature, is_satisfied

# Create checkpoint requiring 2 of 3 signatures
checkpoint = create_checkpoint(
    checkpoint_id="chk-deploy-001",
    dag_run_id="run-456",
    task_id="deploy_prod",
    tenant="acme-corp",
    prompt="Approve production deployment",
    required_signers=["alice", "bob", "charlie"],
    min_signatures=2
)

# Add signatures
add_signature("chk-deploy-001", "alice", {"comment": "LGTM"})
add_signature("chk-deploy-001", "bob", {"comment": "Approved"})

# Check if satisfied
if is_satisfied(checkpoint):
    print("Ready to proceed")
```

### Team & Workspace Budgets

Team-level budget enforcement checked **before** tenant budgets:

```python
from src.cost.budgets import get_team_budget, is_over_team_budget
from src.cost.ledger import window_sum, load_cost_events

# Get team budget
budget = get_team_budget("team-eng")
# {"daily": 10.0, "monthly": 200.0}

# Check team spend
events = load_cost_events()
daily_spend = window_sum(events, team_id="team-eng", days=1)
monthly_spend = window_sum(events, team_id="team-eng", days=30)

status = is_over_team_budget("team-eng", daily_spend, monthly_spend)
if status["daily"] or status["monthly"]:
    raise BudgetExceededError("Team budget exceeded")
```

**Environment variables:**
```bash
TEAM_BUDGET_DAILY_DEFAULT=10.0
TEAM_BUDGET_MONTHLY_DEFAULT=200.0
TEAM_QPS_LIMIT=10
```

### Delegation Audit Trail

All delegations logged to `logs/delegations.jsonl`:

```json
{
  "delegation_id": "abc-123",
  "granter": "alice",
  "grantee": "bob",
  "scope": "team",
  "scope_id": "team-eng",
  "role": "Operator",
  "starts_at": "2025-10-03T12:00:00Z",
  "expires_at": "2025-10-04T12:00:00Z",
  "reason": "On-call coverage"
}
```

**Monitoring:**
```bash
# Active delegations expiring soon
python -c "
from src.security.delegation import list_active_delegations
from datetime import datetime, timedelta

delegations = list_active_delegations('team', 'team-eng')
now = datetime.now(datetime.now().astimezone().tzinfo)

for d in delegations:
    expires_at = datetime.fromisoformat(d['expires_at'].rstrip('Z'))
    hours = (expires_at - now).total_seconds() / 3600
    if hours < 24:
        print(f'ALERT: Delegation {d[\"delegation_id\"]} expires in {hours:.1f}h')
"
```

### Security Best Practices

1. **Least Privilege Delegation**: Grant minimum necessary role and duration
2. **Delegation Review**: Monitor active delegations via dashboard
3. **Multi-Sign for Critical Ops**: Require 2+ signatures for production changes
4. **Team Budget Limits**: Set conservative team budgets to prevent overruns
5. **Audit All Governance**: Monitor `logs/delegations.jsonl`, `logs/checkpoints.jsonl`

### Connector RBAC (Sprint 35A)

**Health CLI Access Control:**

The `scripts/connectors_health.py` CLI enforces RBAC for operations monitoring:

| Command | Required Role | Description |
|---------|---------------|-------------|
| `list` | Operator+ | List all connectors with health status |
| `drill <ID>` | Operator+ | Detailed metrics and failures for connector |

**Role Check:**
```bash
# Set user role
export USER_ROLE=Operator

# Verify access
python scripts/connectors_health.py list
```

**Exit Code 2:** Insufficient permissions (requires Operator, Deployer, or Admin role)

**Environment Variables:**
- `CONNECTOR_RBAC_ROLE` - Minimum role required (default: `Operator`)
- `USER_ROLE` - Current user's role

**Role Hierarchy:**
```
Viewer < Author < Operator < Deployer < Auditor < Compliance < Admin
```

**Rationale:** Connector health monitoring is an operational task requiring Operator-level access to prevent unauthorized system introspection.

### Related Documentation

- [COLLABORATION.md](./COLLABORATION.md) - Complete collaborative governance guide
- [OPERATIONS.md](./OPERATIONS.md) - Delegation and multi-sign runbooks
- [CONNECTOR_OBSERVABILITY.md](./CONNECTOR_OBSERVABILITY.md) - Connector health monitoring

---

## Dependency Management & Security Updates

### Dependency Policy

We maintain strict dependency security practices to protect against known vulnerabilities:

**Automated Monitoring:**
- Dependabot enabled for weekly dependency updates (pip, GitHub Actions, Docker)
- `pip-audit` runs on every nightly CI build (blocking)
- `pip-audit` runs on PRs (non-blocking, warning only)

**Update Schedule:**
- **Security patches**: Applied within 7 days of disclosure
- **Non-security updates**: Reviewed weekly, applied in batches
- **Major version updates**: Evaluated quarterly with compatibility testing

### Running Dependency Audits

```bash
# Install pip-audit
pip install pip-audit

# Run audit
pip-audit

# Audit with JSON output
pip-audit --format json --output audit-report.json

# Fix vulnerabilities automatically (where possible)
pip-audit --fix
```

### Overriding Dependency Versions

If you need to override a dependency version due to compatibility issues:

1. **Document the reason** in a comment in `pyproject.toml` or `requirements.txt`
2. **Create a tracking issue** for the override
3. **Set a review date** (max 90 days)
4. **Test thoroughly** before deploying

Example:
```toml
# pyproject.toml
dependencies = [
    "vulnerable-package==1.2.3",  # TODO(#123): Pin due to breaking changes in 1.3.x, review by 2026-01-15
]
```

### Reporting Dependency Vulnerabilities

If you discover a vulnerability in a dependency:

1. Check if it's already tracked in Dependabot alerts
2. If not, create a **security advisory** (not a public issue)
3. Follow the process in the [Security Policy](#reporting-vulnerabilities) section

### Best Practices

- **Pin versions** in production deployments
- **Use lock files** (`requirements.txt` with hashes) for reproducible builds
- **Review changelogs** before updating dependencies
- **Test upgrades** in staging environments first
- **Monitor CVE databases** for your tech stack

### Dependency Review Process

For Dependabot PRs:

1. **Automated**: CI tests run automatically
2. **Review**: Check changelog for breaking changes
3. **Security**: Verify CVE fix details if applicable
4. **Approve**: Merge if tests pass and no breaking changes
5. **Monitor**: Watch for issues post-merge
