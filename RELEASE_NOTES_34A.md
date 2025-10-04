# Release Notes: Sprint 34A - Collaborative Governance

**Version:** 0.34.0
**Date:** 2025-10-03
**Focus:** Teams, delegation, multi-sign approvals, and team-level resource governance

---

## Features

### Teams & Workspaces
Hierarchical organization model enabling multi-user collaboration with role-based access control.

- **Roles:** Viewer(0) → Author(1) → Operator(2) → Auditor(3) → Compliance(4) → Admin(5)
- **CLI:** `scripts/teams.py` and `scripts/workspaces.py` for member management
- **Storage:** JSONL append-only logs with last-wins semantics

```bash
python scripts/teams.py add-member --team-id eng --user alice --role Admin
python scripts/workspaces.py add-member --workspace-id proj-x --user bob --role Author
```

### Time-Bounded Delegation
Temporary authority grants with automatic expiry checking.

```bash
python scripts/delegation.py grant --user charlie --role Operator --expires-at 2025-10-10T12:00:00
python scripts/delegation.py list --user charlie
python scripts/delegation.py revoke --delegation-id <id>
```

- **Effective Role:** Base role + active delegations (highest wins)
- **Expiry:** Automatic filtering of expired delegations at check time

### Multi-Sign (M-of-N) Checkpoints
Approval workflows requiring multiple signatures (e.g., 2-of-3, 3-of-5).

```bash
python scripts/approvals.py list-pending
python scripts/approvals.py sign --checkpoint-id <id> --user alice
python scripts/approvals.py status --checkpoint-id <id>
```

- **Threshold Satisfaction:** Checkpoint publishes only after M signatures collected
- **Integration:** Extended `src/orchestrator/checkpoints.py` with `add_signature()` and `is_satisfied()`

### Team Budgets & Rate Limits
Resource governance at team level, enforced before tenant-level checks.

- **Budget Enforcement Order:** Team → Tenant → Global
- **Rate Limiting Order:** Global → Team → Tenant
- **Tracking:** Team spend logged via `team_id` parameter in cost ledger

### Observability Dashboard
New governance metrics panel in `dashboards/observability_tab.py`:

- Active and expiring delegations
- Pending multi-sign checkpoints
- Team budget utilization

---

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `TEAM_BUDGET_DAILY_DEFAULT` | `10.0` | Default daily budget per team |
| `TEAM_BUDGET_MONTHLY_DEFAULT` | `200.0` | Default monthly budget per team |
| `TEAM_QPS_LIMIT` | `10` | Team-level queries per second limit |
| `TEAMS_PATH` | `logs/teams.jsonl` | Path to teams JSONL registry |
| `WORKSPACES_PATH` | `logs/workspaces.jsonl` | Path to workspaces JSONL registry |
| `DELEGATIONS_PATH` | `logs/delegations.jsonl` | Path to delegations JSONL log |

---

## Documentation

- **NEW:** `docs/COLLABORATION.md` - Complete collaborative governance guide with examples
- **UPDATED:** `docs/SECURITY.md` - Sprint 34A section on effective role resolution and multi-sign
- **UPDATED:** `docs/OPERATIONS.md` - Delegation and multi-sign runbooks

---

## Testing

All 15 Sprint 34A integration tests passing (`tests/test_sprint34a_collab.py`):

- Teams/workspaces creation and membership
- Delegation grant/revoke/expiry
- Multi-sign checkpoint workflows
- Team budget enforcement
- Team rate limiting
- End-to-end integration scenario

**Run Sprint 34A tests:**
```bash
pytest tests/test_sprint34a_collab.py -v
```

---

## Upgrade Notes

- No breaking changes to existing APIs
- New role level (Compliance=4) shifts Admin to level 5
- Team-level budget/rate-limit checks run before tenant checks
- JSONL logs handle missing files gracefully (no migration required)

---

## Next Sprint

**Sprint 34B - Connector Framework v1:** External system integration SDK (Salesforce, Slack, email, webhooks).
