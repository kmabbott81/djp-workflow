# Changelog

All notable changes to the DJP Workflow system will be documented in this file.

## [Unreleased] - v1.0.2-dev

### Added
- TBD

### Changed
- TBD

### Fixed
- TBD

### Security
- TBD

### Documentation
- TBD

---

## [1.0.1] - 2025-10-04 - 2025-10-04 - Post-GA DX & Hardening Release Candidate

### Added
- **CI/CD Improvements**: Nightly workflow for full test suite across Python 3.9-3.12
- **Dependency Security**: Dependabot configuration for pip, GitHub Actions, and Docker
- **Developer Experience**: Root Makefile with convenience targets (test, lint, format, docker)
- **Documentation**: DEVELOPMENT.md (local dev quickstart), SUPPORT.md (support policy), PR template
- **Test Infrastructure**: pytest.ini with markers (slow, smoke, integration, live, e2e)

### Changed
- **CI Optimization**: PR workflow uses Python 3.11 only with pip/pytest caching (target: ≤90s)
- **Dependency Audits**: pip-audit runs on PRs (non-blocking warning) and nightly (blocking)

### Fixed
- **CI Dependencies**: Package now installs with [dev] extras to ensure all test dependencies available

### Security
- **Dependency Policy**: Documented in SECURITY.md with pip-audit integration and CVE response procedures

### Documentation
- **OPERATIONS.md**: Added "First 10 Minutes On-Call" rapid triage checklist
- **OPERATIONS.md**: Added "Backup & Restore Dry-Run" procedures with quarterly drill schedule
- **SECURITY.md**: Added dependency management policy, override guidelines, and CVE handling
- **DEVELOPMENT.md**: Complete local development guide with common issues and IDE setup
- **SUPPORT.md**: Support windows, version policy, and community resources

---


### Documentation
- **OPERATIONS.md**: Added "First 10 Minutes On-Call" rapid triage checklist
- **OPERATIONS.md**: Added "Backup & Restore Dry-Run" procedures with quarterly drill schedule
- **SECURITY.md**: Added dependency management policy, override guidelines, and CVE handling
- **DEVELOPMENT.md**: Complete local development guide with common issues and IDE setup
- **SUPPORT.md**: Support windows, version policy, and community resources

---

## [Unreleased] - v1.0.1-dev

### Added
- TBD

### Changed
- TBD

### Fixed
- TBD

### Security
- TBD

### Documentation
- TBD

---

## [1.0.0] - 2025-10-04 - Enterprise Readiness Release

### Major Milestone: Production-Ready Platform

This release marks the completion of Sprints 34B–39B, delivering a fully-featured, enterprise-grade workflow orchestration platform with multi-connector support, natural language commanding, unified resource indexing, and comprehensive security controls.

### Connectors & Resilience (Sprints 34B–36B)
- **Microsoft Teams Connector** (Sprint 35B): Channel and message operations via Graph API
- **Microsoft Outlook Connector** (Sprint 35C): Email, contacts, calendar events with OAuth2
- **Slack Connector** (Sprint 36–36B): Workspace, channel, and message APIs with circuit breaker and exponential backoff
- **Cross-Platform Connector Abstraction Layer (CP-CAL)**: Unified schema normalization across all platforms
- **Resilience Patterns**: Retry logic, circuit breaker, rate limit handling (429), exponential backoff
- **OAuth2 Token Store**: Multi-tenant token management with secure storage
- **DRY_RUN Mode**: Offline testing with deterministic mock responses

### Gmail Integration (Sprint 37)
- **Gmail Connector**: Message, thread, and label operations using Google API client
- **OAuth2 Flow**: Secure authentication with refresh token support
- **CP-CAL Integration**: Schema normalization for Gmail messages and threads

### Unified Resource Graph (URG) & Actions (Sprints 38–38B)
- **URG Index**: In-memory inverted index with JSONL shard persistence across all connectors
- **Cross-Connector Search**: Unified search API with filters (type, source, tenant, timestamp, labels)
- **Action Router**: Execute operations (reply, forward, delete, email) across any connector
- **RBAC Enforcement**: Admin role required for all actions with audit logging
- **Tenant Isolation**: Complete data separation enforced at index and action levels
- **Graph IDs**: Canonical URN format (`urn:{source}:{type}:{id}`)

### Notion Integration (Sprint 39A)
- **Notion Connector**: Page, database, and block operations via Notion API
- **Search & Query**: Database queries with filters and sorts
- **CP-CAL Support**: Schema normalization for Notion pages and databases
- **URG Integration**: Notion resources indexed and searchable alongside other connectors

### Natural Language Commanding (Sprints 39–39B)
- **Intent Parser**: Deterministic regex-based NL → structured intent (NO LLM)
- **URG Grounding**: Resolve NL targets to specific resources via URG search
- **Action Planner**: Convert intents → executable action plans with RBAC validation
- **Risk Assessment**: Low/medium/high risk scoring based on operation and target analysis
- **Approval Gating**: High-risk operations require checkpoint approval before execution
- **Parser Hardening**: Verb disambiguation, target extraction, case preservation, constraint parsing

### Security & Governance
- **RBAC**: Role-based access control enforced across all operations
- **Tenant Isolation**: Complete data and operation separation
- **Audit Logging**: All actions logged with timestamp, user, result, and metadata
- **Team Budgets**: Resource governance at team level
- **Multi-Sign Checkpoints**: M-of-N approval workflows for sensitive operations

### Infrastructure
- **Health Monitoring**: `/health` and `/ready` endpoints with circuit breaker status
- **Metrics & Logging**: JSONL-based metrics collection and structured logging
- **Configuration Validation**: Environment variable validation with clear error messages
- **Test Coverage**: 98/98 NL tests, comprehensive connector and URG test suites

### Environment Variables Added
- `TEAMS_*`: Microsoft Teams API configuration
- `OUTLOOK_*`: Outlook/Graph API configuration
- `SLACK_*`: Slack workspace and OAuth configuration
- `GMAIL_*`: Gmail API OAuth configuration
- `NOTION_*`: Notion API configuration
- `URG_*`: URG index and search configuration
- `NL_*`: Natural language parser configuration

### Changed
- Version bumped to 1.0.0
- All connector tests isolated and passing
- CP-CAL schema normalization across 5 platforms
- URG search now supports all connector types
- Natural language parser stabilized with 98/98 tests passing

### Fixed
- Slack circuit breaker state persistence
- URG test isolation (global index singleton reset)
- NL verb disambiguation (email vs message vs forward)
- NL target extraction for person names
- External email risk assessment in planner

---

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
