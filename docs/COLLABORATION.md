# Collaborative Governance (Sprint 34A)

**Teams, Workspaces, Delegations, and Multi-Sign Approvals**

## Overview

Sprint 34A introduces collaborative governance features that enable teams to work together with structured roles, time-bounded authority delegation, and multi-signature approval workflows.

### Key Features

1. **Teams & Workspaces**: Hierarchical organization with role-based access
2. **Time-Bounded Delegation**: Temporary authority grants with automatic expiry
3. **Multi-Sign Approvals**: M-of-N signature requirements for critical decisions
4. **Team Budgets & Rate Limits**: Resource governance at team level
5. **Audit Trail**: Complete governance event logging

---

## Teams & Workspaces

### Hierarchy

```
Organization
  └── Teams (e.g., team-eng, team-ops)
        └── Workspaces (e.g., ws-project-a, ws-project-b)
              └── Members with roles
```

### Roles

Six-tier hierarchy (lowest to highest):

| Role | Level | Typical Permissions |
|------|-------|-------------------|
| **Viewer** | 0 | Read-only access |
| **Author** | 1 | Create/edit content |
| **Operator** | 2 | Execute workflows, approve standard checkpoints |
| **Auditor** | 3 | Review audit logs, compliance reports |
| **Compliance** | 4 | Policy enforcement, data classification |
| **Admin** | 5 | Full control, member management |

### Team Management

#### Create Team and Add Members

```bash
# Add first member (creates team)
python scripts/teams.py add-member \
  --team-id team-eng \
  --user alice \
  --role Admin \
  --team-name "Engineering Team"

# Add more members
python scripts/teams.py add-member \
  --team-id team-eng \
  --user bob \
  --role Operator
```

#### List Team Members

```bash
python scripts/teams.py list-members --team-id team-eng
```

Output:
```
Team team-eng members:
  • alice                  — Admin
  • bob                    — Operator

Total: 2 members
```

#### Check User Role

```bash
python scripts/teams.py get-role --team-id team-eng --user bob
```

### Workspace Management

#### Create Workspace and Add Members

```bash
# Create workspace under team
python scripts/workspaces.py add-member \
  --workspace-id ws-project-a \
  --user bob \
  --role Operator \
  --workspace-name "Project A" \
  --team-id team-eng
```

#### List Workspace Members

```bash
python scripts/workspaces.py list-members --workspace-id ws-project-a
```

---

## Time-Bounded Delegation

Delegation allows temporary authority grants with automatic expiry. Useful for:
- On-call coverage
- Temporary elevated privileges
- Cross-team collaboration
- Time-limited approvals

### Grant Delegation

```bash
python scripts/delegation.py grant \
  --granter alice \
  --grantee bob \
  --scope team \
  --scope-id team-eng \
  --role Operator \
  --hours 24 \
  --reason "On-call coverage for weekend"
```

Output:
```
✅ Delegation granted:
   ID: abc-123-def-456
   Grantee: bob
   Scope: team/team-eng
   Role: Operator
   Duration: 24 hours
   Expires: 2025-10-04T12:00:00Z
   Reason: On-call coverage for weekend
```

### List Active Delegations

```bash
python scripts/delegation.py list --scope team --scope-id team-eng
```

Output:
```
Active delegations for team/team-eng:

  ID: abc-123-def-456
    Granter: alice → Grantee: bob
    Role: Operator
    Expires: 2025-10-04T12:00:00Z (23.5h remaining)
    Reason: On-call coverage for weekend

Total: 1 active delegations
```

### Revoke Delegation

```bash
python scripts/delegation.py revoke --delegation-id abc-123-def-456
```

### Effective Role Resolution

When checking permissions, the system calculates the **effective role** as the maximum of:
- Base role (team/workspace membership)
- Active delegations

Example:
```python
from src.security.delegation import active_role_for

# Bob is normally a Viewer, but has an active Operator delegation
role = active_role_for("bob", "team", "team-eng")
print(role)  # "Operator" (elevated via delegation)
```

---

## Multi-Sign Approvals

Multi-signature checkpoints require M-of-N signatures from designated signers before proceeding.

### Use Cases

- Critical deployments (2 of 3 SREs must approve)
- Budget overrides (CFO + 1 director)
- Data exports (Compliance + Data owner)
- Production changes (On-call + Manager)

### Create Multi-Sign Checkpoint

```python
from src.orchestrator.checkpoints import create_checkpoint

checkpoint = create_checkpoint(
    checkpoint_id="chk-deploy-001",
    dag_run_id="run-456",
    task_id="deploy_prod",
    tenant="acme-corp",
    prompt="Approve production deployment v2.5.0",
    required_signers=["alice", "bob", "charlie"],  # 3 signers
    min_signatures=2,  # Need 2 of 3
)
```

### Add Signatures

```bash
# First signature
python scripts/approvals.py sign chk-deploy-001 \
  --user alice \
  --kv comment="LGTM, tests passed"

# Output
✍️ Signature added by alice
Task: deploy_prod
DAG Run: run-456
Signatures: 1/2
⏳ Waiting for 1 more signature(s)

# Second signature
python scripts/approvals.py sign chk-deploy-001 \
  --user bob \
  --kv comment="Approved"

# Output
✍️ Signature added by bob
Task: deploy_prod
DAG Run: run-456
Signatures: 2/2
✅ Checkpoint now has sufficient signatures (2/2)
```

### Check Status

```bash
python scripts/approvals.py status chk-deploy-001
```

Output:
```
Checkpoint: chk-deploy-001
Status: pending
Task: deploy_prod
DAG Run: run-456
Prompt: Approve production deployment v2.5.0

Multi-sign checkpoint:
  Required signers: alice, bob, charlie
  Minimum signatures: 2
  Current signatures: 2

Signatures:
  • alice at 2025-10-03T10:00:00 — LGTM, tests passed
  • bob at 2025-10-03T10:05:00 — Approved

✅ Checkpoint has sufficient signatures
```

### Integration with DAG Runner

The orchestrator automatically checks `is_satisfied()` and proceeds when threshold is met:

```python
from src.orchestrator.checkpoints import get_checkpoint, is_satisfied

checkpoint = get_checkpoint("chk-deploy-001")

if is_satisfied(checkpoint):
    # Proceed with task execution
    print("Checkpoint satisfied, continuing DAG")
else:
    # Wait for more signatures
    print(f"Waiting for {checkpoint['min_signatures'] - len(checkpoint['approvals'])} more signatures")
```

---

## Team Budgets & Rate Limits

### Budget Enforcement

Team budgets are checked **before** tenant budgets, providing an additional governance layer.

#### Environment Configuration

```bash
# Default team budgets (if not in YAML)
export TEAM_BUDGET_DAILY_DEFAULT=10.0
export TEAM_BUDGET_MONTHLY_DEFAULT=200.0

# Team rate limits
export TEAM_QPS_LIMIT=10
```

#### YAML Configuration

`config/budgets.yaml`:
```yaml
global:
  daily: 25.0
  monthly: 500.0

teams:
  team-eng:
    daily: 15.0
    monthly: 300.0
  team-ops:
    daily: 10.0
    monthly: 150.0

tenants:
  acme-corp:
    daily: 5.0
    monthly: 100.0
```

### Budget Checking

```python
from src.cost.budgets import get_team_budget, is_over_team_budget
from src.cost.ledger import load_cost_events, window_sum

# Get team budget
budget = get_team_budget("team-eng")
print(f"Daily: ${budget['daily']}, Monthly: ${budget['monthly']}")

# Check team spend
events = load_cost_events()
daily_spend = window_sum(events, team_id="team-eng", days=1)
monthly_spend = window_sum(events, team_id="team-eng", days=30)

status = is_over_team_budget("team-eng", daily_spend, monthly_spend)
if status["daily"] or status["monthly"]:
    print(f"Team over budget! Daily: {status['daily']}, Monthly: {status['monthly']}")
```

### Rate Limiting

```python
from src.queue.ratelimit import get_rate_limiter

limiter = get_rate_limiter()

# Check rate limit with team_id
allowed = limiter.allow(
    tenant_id="acme-corp",
    tokens=1.0,
    team_id="team-eng"  # Sprint 34A: team-level rate limiting
)

if not allowed:
    print("Rate limit exceeded (global, team, or tenant)")
```

---

## Observability

### Dashboard Governance Section

The observability dashboard includes a **Collaborative Governance** section showing:

1. **Active Delegations**
   - Total count across sample teams/workspaces
   - Count expiring within 24 hours

2. **Multi-Sign Checkpoints**
   - Pending multi-sign checkpoints
   - Total signatures needed
   - Per-checkpoint progress

3. **Team Budgets**
   - Last 24h spend per team
   - Budget utilization %
   - Remaining budget

Access: `streamlit run dashboards/main.py` → Observability tab

### Logs

All governance events are logged to:

- **Teams**: `logs/teams.jsonl`
- **Workspaces**: `logs/workspaces.jsonl`
- **Delegations**: `logs/delegations.jsonl`
- **Checkpoints**: `logs/checkpoints.jsonl` (multi-sign events)
- **Governance Events**: `logs/governance_events.jsonl` (budget denials, etc.)

---

## Example Workflows

### 1. On-Call Handoff

```bash
# Alice delegates Operator role to Bob for 24 hours
python scripts/delegation.py grant \
  --granter alice \
  --grantee bob \
  --scope team \
  --scope-id team-ops \
  --role Operator \
  --hours 24 \
  --reason "Weekend on-call coverage"

# Bob can now approve checkpoints requiring Operator role
python scripts/approvals.py approve chk-incident-001 \
  --kv signoff="Incident resolved, deploying hotfix"
```

### 2. Critical Deployment Approval

```bash
# Create multi-sign checkpoint requiring 2 of 3 SREs
# (Done in DAG execution code)

# SRE 1 signs
python scripts/approvals.py sign chk-prod-deploy \
  --user alice \
  --kv comment="Tests passed, metrics look good"

# SRE 2 signs
python scripts/approvals.py sign chk-prod-deploy \
  --user bob \
  --kv comment="Approved, rollback plan ready"

# Deployment proceeds automatically once satisfied
```

### 3. Cross-Team Collaboration

```bash
# Add external user to workspace with limited duration delegation
python scripts/workspaces.py add-member \
  --workspace-id ws-integration \
  --user external-contractor \
  --role Viewer

# Grant temporary elevated access
python scripts/delegation.py grant \
  --granter alice \
  --grantee external-contractor \
  --scope workspace \
  --scope-id ws-integration \
  --role Author \
  --hours 72 \
  --reason "Integration testing phase"
```

---

## Security Considerations

### Audit Trail

All governance actions are logged with:
- Timestamp (UTC)
- Actor (granter, grantee, approver, etc.)
- Scope and scope ID
- Reason/justification

### Least Privilege

- Start with minimum role (Viewer)
- Use delegation for temporary elevation
- Revoke delegations when no longer needed
- Monitor delegation usage via observability dashboard

### Multi-Sign Best Practices

- Use multi-sign for high-impact operations
- Require 2+ signatures for production changes
- Include diverse roles (e.g., Engineer + Manager)
- Document signature requirements in OPERATIONS.md

### Budget Governance

- Team budgets override individual behavior
- Budget denials logged to `governance_events.jsonl`
- Monitor team utilization in dashboard
- Adjust budgets based on actual usage patterns

---

## Troubleshooting

### Delegation Not Taking Effect

```python
from src.security.delegation import active_role_for

# Check effective role
role = active_role_for("bob", "team", "team-eng")
print(role)  # Should show delegated role if active

# List active delegations
from src.security.delegation import list_active_delegations
delegations = list_active_delegations("team", "team-eng")
print(delegations)
```

### Multi-Sign Checkpoint Stuck

```bash
# Check status
python scripts/approvals.py status chk-id

# View pending signatures
# Manually add signatures if signers are unavailable
python scripts/approvals.py sign chk-id --user backup-approver
```

### Budget Denial

Check logs:
```bash
cat logs/governance_events.jsonl | grep budget_deny
```

Review team spend:
```bash
# View team budget utilization in dashboard
streamlit run dashboards/main.py
```

---

## API Reference

### Security Module

#### Teams
- `get_team_role(user, team_id) -> str | None`
- `list_team_members(team_id) -> list[dict]`
- `upsert_team_member(team_id, user, role, team_name) -> dict`
- `require_team_role(user, team_id, required_role) -> None` (raises PermissionError)

#### Workspaces
- `get_workspace_role(user, workspace_id) -> str | None`
- `list_workspace_members(workspace_id) -> list[dict]`
- `upsert_workspace_member(workspace_id, user, role, workspace_name, team_id) -> dict`
- `require_workspace_role(user, workspace_id, required_role) -> None` (raises PermissionError)

#### Delegation
- `grant_delegation(granter, grantee, scope, scope_id, role, hours, reason) -> dict`
- `revoke_delegation(delegation_id) -> bool`
- `list_active_delegations(scope, scope_id, now) -> list[dict]`
- `active_role_for(user, scope, scope_id, now) -> str | None`

#### Checkpoints
- `create_checkpoint(..., required_signers, min_signatures) -> dict` (Sprint 34A)
- `add_signature(checkpoint_id, user, approval_data) -> dict` (Sprint 34A)
- `is_satisfied(checkpoint, effective_role_fn) -> bool` (Sprint 34A)

### Cost Module

#### Budgets
- `get_team_budget(team_id) -> dict[str, float]` (Sprint 34A)
- `is_over_team_budget(team_id, daily_spend, monthly_spend) -> dict` (Sprint 34A)

#### Ledger
- `window_sum(events, tenant, team_id, days) -> float` (Sprint 34A: added team_id)

#### Enforcer
- `should_deny(tenant, check_global, team_id) -> tuple[bool, str | None]` (Sprint 34A: added team_id)

### Queue Module

#### Rate Limiting
- `RateLimiter.allow(tenant_id, tokens, team_id) -> bool` (Sprint 34A: added team_id)

---

## Next Steps

- **Sprint 35**: Policy-as-code (OPA integration)
- **Sprint 36**: Workflow templates with approval patterns
- **Sprint 37**: Integration with external identity providers (SSO, LDAP)

---

**Sprint 34A Complete** ✅
Generated: 2025-10-03
