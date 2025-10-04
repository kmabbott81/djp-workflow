# Changelog

All notable changes to the DJP Workflow system will be documented in this file.

## [0.34.0] - 2025-10-03 - Sprint 34A: Collaborative Governance

### Added
- **Teams & Workspaces**: Hierarchical organization model with role-based membership (Viewer, Author, Operator, Auditor, Compliance, Admin)
  - `src/security/teams.py` - Team management with JSONL registry
  - `src/security/workspaces.py` - Workspace management with team association
  - `scripts/teams.py` - CLI for team member management
  - `scripts/workspaces.py` - CLI for workspace member management

- **Time-Bounded Delegation**: Temporary authority grants with automatic expiry
  - `src/security/delegation.py` - Delegation system with expiry checking
  - `scripts/delegation.py` - CLI for grant/list/revoke operations
  - Effective role resolution (base role + active delegations)

- **Multi-Sign (M-of-N) Checkpoints**: Approval workflows requiring multiple signatures
  - Extended `src/orchestrator/checkpoints.py` with `add_signature()` and `is_satisfied()`
  - Updated `scripts/approvals.py` with `sign` and `status` commands
  - Support for 2-of-3, 3-of-5, etc. approval patterns

- **Team Budgets & Rate Limits**: Resource governance at team level
  - `src/cost/budgets.py` - `get_team_budget()` and `is_over_team_budget()`
  - `src/cost/ledger.py` - Team spend tracking via `team_id` parameter
  - `src/cost/enforcer.py` - Team budget enforcement before tenant checks
  - `src/queue/ratelimit.py` - Team-level QPS limiting

- **Observability Dashboard**: Governance metrics panel
  - `dashboards/observability_tab.py` - New governance section showing:
    - Active delegations and expiring delegations
    - Pending multi-sign checkpoints
    - Team budget utilization

### Documentation
- **NEW**: `docs/COLLABORATION.md` - Complete collaborative governance guide
- **UPDATED**: `docs/SECURITY.md` - Sprint 34A section on effective role resolution and multi-sign
- **UPDATED**: `docs/OPERATIONS.md` - Delegation and multi-sign runbooks

### Tests
- **NEW**: `tests/test_sprint34a_collab.py` - 15 comprehensive integration tests
  - Teams/workspaces creation and membership
  - Delegation grant/revoke/expiry
  - Multi-sign checkpoint workflows
  - Team budget enforcement
  - Team rate limiting

### Environment Variables
- `TEAM_BUDGET_DAILY_DEFAULT` - Default daily budget per team (default: 10.0)
- `TEAM_BUDGET_MONTHLY_DEFAULT` - Default monthly budget per team (default: 200.0)
- `TEAM_QPS_LIMIT` - Team-level queries per second limit (default: 10)
- `TEAMS_PATH` - Path to teams JSONL (default: logs/teams.jsonl)
- `WORKSPACES_PATH` - Path to workspaces JSONL (default: logs/workspaces.jsonl)
- `DELEGATIONS_PATH` - Path to delegations JSONL (default: logs/delegations.jsonl)

### Changed
- Role hierarchy extended: Viewer(0) → Author(1) → Operator(2) → Auditor(3) → Compliance(4) → Admin(5)
- Budget enforcement order: Team → Tenant → Global
- Rate limiting order: Global → Team → Tenant

### Fixed
- Pre-commit hook compliance for new CLI scripts
- Import statement formatting in delegation/teams/workspaces modules

---

## Previous Releases

See `2025.*.*.md` sprint logs for historical changes prior to centralized changelog.
