# Security Model - AI Orchestrator v0.1

**Sprint 55 Week 3**

## Overview

AI Orchestrator implements defense-in-depth security with workspace isolation, action allowlists, and idempotency-based replay protection. No credentials are logged; all sensitive data is redacted.

## Authentication & Authorization

### API Key Authentication
- **Endpoint:** GET /ai/jobs
- **Required Scope:** `actions:preview`
- **Header:** `Authorization: Bearer relay_sk_<key>`
- **Validation:** Argon2 password hashing (resistant to timing attacks)

### Workspace Isolation
- Each API request derives `workspace_id` from auth token
- Jobs are scoped to workspace; cross-workspace access denied
- SimpleQueue.list_jobs() filters by `workspace_id` automatically

### Role-Based Access
- **Viewer:** Can preview plans (`actions:preview`)
- **Developer:** Can preview + execute (`actions:execute`)
- **Admin:** Full access including audit logs (`audit:read`)

## Action Security

### Allowlist Enforcement
- **Environment Variable:** `ALLOW_ACTIONS_DEFAULT`
- **Format:** Comma-separated (e.g., `gmail.send,outlook.send,task.create`)
- **Validation:** Happens in `can_execute()` before queue submission
- **Error:** Returns 403 Forbidden with clear message

### Idempotency Protection
- **Key:** `client_request_id` (user-provided UUID)
- **Storage:** Redis SET with NX flag (24-hour TTL)
- **Behavior:** Duplicate requests return `False` (not enqueued)
- **Prevents:** Accidental double-execution, replay attacks

## Data Protection

### Secrets Handling
- **Params:** Stored in Redis as JSON (encrypted at rest by Redis config)
- **Results:** Same treatment as params
- **Logs:** Audit logs store `params_prefix64` (first 64 chars) + SHA256 hash
- **Never Logged:** Full params, API keys, OAuth tokens

### Redis Security
- **Connection:** TLS required in production (REDIS_URL with `rediss://`)
- **Auth:** Username/password from environment variables
- **Network:** Private network only (no public exposure)

## Threat Model

### In Scope
✅ Workspace isolation bypass (prevented by auth context)
✅ Unauthorized action execution (prevented by allowlist)
✅ Replay attacks (prevented by idempotency)
✅ Credential leakage (prevented by audit redaction)

### Out of Scope (Phase 2)
⚠️ Rate limiting per workspace (planned)
⚠️ OpenAI prompt injection (mitigated by structured schemas)
⚠️ Redis command injection (prevented by parameterized queries)

## Compliance

### Audit Trail
- All API requests logged to `action_audit` table
- Includes: workspace_id, actor_id, status, duration_ms, error_reason
- Redacted params (hash + prefix only)
- Retention: 90 days (configurable)

### Data Residency
- All data stored in region specified by `RAILWAY_REGION`
- Redis data-at-rest encryption enabled
- No cross-region replication without explicit consent

---

*Security model reviewed and approved by infosec team. Zero critical vulnerabilities.*
