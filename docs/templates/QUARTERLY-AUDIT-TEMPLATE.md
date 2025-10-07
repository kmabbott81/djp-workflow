# Quarterly Audit Template

**Audit Date:** [YYYY-MM-DD]
**Audit Period:** [Quarter] [Year] (e.g., Q4 2025)
**Auditor:** [Name/Team]
**Scope:** Platform-wide operational readiness and security posture

---

## Executive Summary

**Audit Status:** [🟢 PASSED / 🟡 CONDITIONAL / 🔴 FAILED]

**Platform Health:**
- **Security:** [X]% (Previous: [Y]%)
- **Reliability:** [X]% (Previous: [Y]%)
- **Observability:** [X]% (Previous: [Y]%)
- **Documentation:** [X]% (Previous: [Y]%)
- **Product:** [X]% (Previous: [Y]%)
- **Overall:** [X]% (Previous: [Y]%)

**Critical Findings:**
- [X] P0 risks identified
- [X] P1 risks identified
- [X] P2 risks identified
- [X] P3 risks identified

**Recommended Actions:**
1. [Top priority action]
2. [Second priority action]
3. [Third priority action]

---

## Part 1: Pre-Audit Snapshot

### 1.1 System Inventory

**Infrastructure:**
- **Cloud Provider:** [Railway / AWS / GCP / Azure]
- **Compute:** [Service type, instance count]
- **Database:** [Postgres version, instance type]
- **Cache:** [Redis version, instance type]
- **CDN:** [Cloudflare / Vercel / CloudFront]
- **Monitoring:** [Prometheus / Grafana / Datadog]

**Codebase:**
- **Backend:** [Language, framework, version]
- **Frontend:** [Language, framework, version]
- **Repository:** [GitHub URL]
- **Active Branches:** [List sprint branches]
- **Last Deploy:** [Date, commit SHA]

### 1.2 Dependency Snapshot

Run: `pip freeze > docs/audit/[DATE]/snapshot/dependencies.txt`

**Key Dependencies:**
- FastAPI: [version]
- Uvicorn: [version]
- SQLAlchemy: [version]
- Redis: [version]
- OpenTelemetry: [version]

**Vulnerability Scan:**
```bash
# Python
safety check --json > docs/audit/[DATE]/snapshot/vulnerabilities.json

# Node.js (if applicable)
npm audit --json > docs/audit/[DATE]/snapshot/npm-audit.json
```

**Outdated Packages:**
```bash
pip list --outdated > docs/audit/[DATE]/snapshot/outdated-packages.txt
```

### 1.3 File Manifest (SHA256 Hashes)

Run: `python scripts/generate_file_manifest.py > docs/audit/[DATE]/snapshot/file-manifest.txt`

**Purpose:** Detect unauthorized file modifications between audits

### 1.4 Database Schema Snapshot

Run: `pg_dump --schema-only $DATABASE_URL > docs/audit/[DATE]/snapshot/schema.sql`

**Migration History:**
```bash
ls -la migrations/ > docs/audit/[DATE]/snapshot/migrations-list.txt
```

### 1.5 Environment Variables Inventory

**Required Environment Variables:**
```bash
# List all env vars (values redacted)
env | grep -E "DATABASE|REDIS|API_KEY|SECRET" | sed 's/=.*/=[REDACTED]/' > docs/audit/[DATE]/snapshot/environment-variables.md
```

---

## Part 2: Security Audit

### 2.1 Authentication & Authorization

**API Key Management:**
- [ ] **Keys stored hashed** (Argon2, bcrypt, or PBKDF2)
- [ ] **No plaintext keys in database** (verify with SQL query)
- [ ] **Key rotation policy defined** (e.g., 90-day expiry)
- [ ] **Key revocation supported** (DELETE /api/keys/:id endpoint exists)

**Role-Based Access Control (RBAC):**
- [ ] **Roles defined:** admin, developer, viewer (or equivalent)
- [ ] **Role enforcement tested:**
  ```bash
  # Test as viewer (should fail)
  curl -H "X-API-Key: $VIEWER_KEY" -X DELETE https://[backend-url]/api/actions/123
  # Expected: 403 Forbidden
  ```
- [ ] **Permission boundaries documented** (docs/security/RBAC.md)

**Session Management:**
- [ ] **Session expiry configured** (e.g., 24 hours)
- [ ] **Refresh token rotation** (if using JWT)
- [ ] **Logout invalidates sessions** (verify in Redis or DB)

### 2.2 Input Validation & Output Encoding

**SQL Injection Prevention:**
- [ ] **Parameterized queries used** (no string interpolation)
  ```bash
  # Check codebase for unsafe patterns
  rg "execute\(f\"" --type py
  rg "execute\(\".*\{" --type py
  # Expected: No matches
  ```

**XSS Prevention:**
- [ ] **CSP header active:** `Content-Security-Policy: default-src 'self'`
- [ ] **User input escaped** (HTML, JSON, URL)
- [ ] **Template engine auto-escapes** (Jinja2, React)

**File Upload Security:**
- [ ] **File size limits enforced** (e.g., 10MB max)
- [ ] **MIME type validation** (no executable uploads)
- [ ] **Virus scanning** (if file uploads exist)

### 2.3 Security Headers

**Verify Production Headers:**
```bash
curl -I https://[backend-url]/ | grep -E "Strict-Transport-Security|Content-Security-Policy|Referrer-Policy|X-Content-Type-Options"
```

**Required Headers:**
- [ ] **HSTS:** `Strict-Transport-Security: max-age=31536000; includeSubDomains`
- [ ] **CSP:** `Content-Security-Policy: default-src 'self'; ...`
- [ ] **Referrer Policy:** `Referrer-Policy: strict-origin-when-cross-origin`
- [ ] **MIME Sniffing:** `X-Content-Type-Options: nosniff`
- [ ] **Frame Options:** `X-Frame-Options: DENY`

### 2.4 Rate Limiting

**Verify Rate Limits:**
```bash
# Test rate limit threshold
for i in {1..150}; do curl -X GET https://[backend-url]/api/actions; done
# Expected: 429 Too Many Requests after ~100 requests
```

**Configuration Check:**
- [ ] **Rate limit per workspace** (not global)
- [ ] **Redis-backed** (with in-process fallback)
- [ ] **Burst allowance** (e.g., 100 req/min, burst 120)
- [ ] **Rate limit headers returned:**
  - `X-RateLimit-Limit: 100`
  - `X-RateLimit-Remaining: 45`
  - `X-RateLimit-Reset: 1633024800`

### 2.5 Secrets Management

**Secrets Scan:**
```bash
# Check for hardcoded secrets
rg -i "password|secret|api_key|token" --type py --type js | grep -v "# noqa" | grep -v "example"
# Expected: No matches (except comments/docs)
```

**Environment Variable Usage:**
- [ ] **All secrets in env vars** (not hardcoded)
- [ ] **`.env` in `.gitignore`**
- [ ] **Pre-commit hook prevents secret commits** (`detect-private-key`)

**Secret Rotation:**
- [ ] **Database password rotated** (within last 90 days)
- [ ] **API keys rotated** (within last 90 days)
- [ ] **GitHub secrets updated** (within last 90 days)

### 2.6 Audit Logging

**Verify Audit Logs:**
```bash
# Check audit log table
psql $DATABASE_URL -c "SELECT COUNT(*) FROM audit_logs WHERE created_at > NOW() - INTERVAL '7 days';"
# Expected: >0 (logs exist)
```

**Audit Log Coverage:**
- [ ] **User actions logged:** login, logout, API key creation, permission changes
- [ ] **Action executions logged:** action type, user, workspace, timestamp
- [ ] **Sensitive parameters redacted:** passwords, tokens, credit card numbers
- [ ] **Log retention:** 90 days (or per compliance requirements)

---

## Part 3: Reliability Audit

### 3.1 CI/CD Pipeline

**Pipeline Configuration:**
- [ ] **Workflow exists:** `.github/workflows/deploy.yml`
- [ ] **Automated tests run:** unit tests, integration tests, smoke tests
- [ ] **Deployment triggers:** merge to `main` or manual dispatch
- [ ] **Rollback automation:** `scripts/rollback_release.py` tested

**Test Results:**
```bash
# Run tests locally
pytest --cov=src tests/
# Expected: ≥80% coverage, all tests pass
```

**Deployment History:**
```bash
# Last 5 deployments
gh run list --workflow=deploy.yml --limit=5
```

### 3.2 Database Backups

**Backup Schedule:**
- [ ] **Daily backups configured:** `.github/workflows/backup.yml`
- [ ] **Backup retention:** 30 days (daily) + 12 months (monthly)
- [ ] **Backup storage:** Encrypted at rest (S3, Railway, etc.)
- [ ] **Backup size monitored:** Alert if size drops >50%

**Restore Drill:**
- [ ] **Last restore drill executed:** [Date]
- [ ] **Restore drill passed:** [✅ YES / ❌ NO]
- [ ] **Restore time:** [X minutes]
- [ ] **Data integrity validated:** Table counts, row counts, key table existence

**Run Restore Drill:**
```bash
python scripts/db_restore_check.py
# Expected: All checks pass, evidence report generated
```

### 3.3 Error Handling & Retry Logic

**Error Handling Coverage:**
- [ ] **Database connection errors handled** (retry with exponential backoff)
- [ ] **Redis connection errors handled** (fallback to in-process)
- [ ] **External API errors handled** (retry with circuit breaker)
- [ ] **Timeout errors handled** (configurable timeout, clear error message)

**Retry Configuration:**
```python
# Example: Verify retry logic in code
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=1, max=10))
def call_external_api():
    ...
```

### 3.4 Health Checks & Readiness Probes

**Health Check Endpoint:**
```bash
curl https://[backend-url]/health
# Expected: {"status": "healthy", "database": "connected", "redis": "connected"}
```

**Readiness Probe:**
```bash
curl https://[backend-url]/readiness
# Expected: 200 OK (returns only when service is ready to accept traffic)
```

**Liveness Probe:**
```bash
curl https://[backend-url]/liveness
# Expected: 200 OK (returns even if dependencies are down, indicates process is alive)
```

---

## Part 4: Observability Audit

### 4.1 Service Level Objectives (SLOs)

**SLO Definitions:**
- [ ] **Latency SLOs defined:** p99 ≤ [X]ms for light endpoints
- [ ] **Error rate SLOs defined:** ≤ [X]% for 7-day window
- [ ] **Availability SLOs defined:** ≥ [X]% uptime (monthly)
- [ ] **SLO documentation exists:** `docs/observability/SLOs.md`

**SLO Compliance Check:**
```promql
# Light endpoint p99 latency
histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{path=~"/actions|/audit"}[5m]))
# Target: ≤0.05 (50ms)

# Error rate
sum(rate(http_requests_total{status=~"5.."}[7d])) / sum(rate(http_requests_total[7d]))
# Target: ≤0.01 (1%)

# Availability
avg_over_time(up{job="relay-backend"}[30d])
# Target: ≥0.999 (99.9%)
```

### 4.2 Prometheus Alerts

**Alert Rules:**
- [ ] **Alert rules exist:** `observability/dashboards/alerts.json`
- [ ] **Alerts deployed to Prometheus:** Verify at `https://[prometheus-url]/alerts`
- [ ] **Alert coverage:** Each SLO has corresponding alert
- [ ] **Alert severity levels:** `info`, `warning`, `critical`, `page`

**Alert Validation:**
```bash
# Check alert rules loaded
curl https://[prometheus-url]/api/v1/rules | jq '.data.groups[].rules[] | select(.type=="alerting") | .name'
# Expected: List of alert names (LightEndpointLatencyHigh, etc.)
```

### 4.3 Grafana Dashboards

**Dashboard Inventory:**
- [ ] **Golden signals dashboard exists:** `observability/dashboards/golden-signals.json`
- [ ] **Dashboard deployed to Grafana:** Verify at `https://[grafana-url]/dashboards`
- [ ] **Dashboard panels aligned with SLOs:** Each SLO has visual representation
- [ ] **Alert annotations visible:** Firing alerts shown on timeline

**Dashboard Validation:**
```bash
# Check dashboard exists
curl -H "Authorization: Bearer $GRAFANA_API_KEY" \
  https://[grafana-url]/api/search?query=Relay%20Golden%20Signals
# Expected: Dashboard UID returned
```

### 4.4 Distributed Tracing

**Tracing Configuration:**
- [ ] **OpenTelemetry SDK integrated:** `opentelemetry-api`, `opentelemetry-sdk`
- [ ] **Trace context propagated:** `traceparent` header in HTTP requests
- [ ] **Spans exported:** Tempo, Jaeger, or equivalent backend
- [ ] **Request ID tracking:** `X-Request-ID` header in responses

**Trace Validation:**
```bash
# Trigger traced request
curl -H "X-Request-ID: test-trace-123" https://[backend-url]/api/actions
# Expected: Trace visible in Tempo/Jaeger with span ID
```

### 4.5 Metrics Exposure

**Metrics Endpoint:**
```bash
curl https://[backend-url]/metrics
# Expected: Prometheus-formatted metrics
```

**Required Metrics:**
- [ ] **HTTP request metrics:** `http_requests_total`, `http_request_duration_seconds`
- [ ] **Action execution metrics:** `action_exec_total`, `action_latency_seconds`, `action_error_total`
- [ ] **Database metrics:** `db_pool_connections_in_use`, `db_pool_connections_max`
- [ ] **Redis metrics:** `redis_up`, `redis_commands_total`

---

## Part 5: Documentation Audit

### 5.1 README & Setup Docs

- [ ] **README.md up-to-date:** Setup instructions, deployment, troubleshooting
- [ ] **Environment variables documented:** `.env.example` file exists
- [ ] **Dependency installation documented:** `pip install -r requirements.txt` or equivalent
- [ ] **Local development documented:** How to run locally, run tests, debug

### 5.2 API Documentation

- [ ] **OpenAPI spec up-to-date:** `/openapi.json` reflects all endpoints
- [ ] **API endpoints documented:** Examples for each endpoint
- [ ] **Postman collection exists:** `docs/postman/relay-api.json`
- [ ] **SDK documentation exists:** JS/Python client usage examples

### 5.3 Operational Runbooks

- [ ] **Deployment runbook:** `docs/runbooks/deployment.md`
- [ ] **Incident response runbook:** `docs/runbooks/incident-response.md`
- [ ] **Backup/restore runbook:** `docs/runbooks/backup-restore.md`
- [ ] **Alert runbooks:** Each alert has `runbook_url` annotation

### 5.4 Architecture Decision Records (ADRs)

- [ ] **ADR directory exists:** `docs/adr/`
- [ ] **Significant decisions documented:** Rate limiting, OAuth, multi-tenancy, etc.
- [ ] **ADR template used:** Consistent format (Context, Decision, Consequences)

---

## Part 6: Risk Prioritization

### Risk Matrix

| ID | Severity | Impact | Likelihood | Title | Owner | Due Date |
|----|----------|--------|------------|-------|-------|----------|
| P0-001 | Critical | High | High | [Risk title] | [Team] | [Date] |
| P1-002 | High | Medium | High | [Risk title] | [Team] | [Date] |
| P2-003 | Medium | Low | Medium | [Risk title] | [Team] | [Date] |
| P3-004 | Low | Low | Low | [Risk title] | [Team] | [Date] |

**Priority Definitions:**
- **P0 (Critical):** Production outage risk, data loss risk, security breach risk → Fix immediately (24 hours)
- **P1 (High):** Performance degradation, partial outage, compliance gap → Fix within 1 week
- **P2 (Medium):** Technical debt, observability gap, documentation gap → Fix within 1 month
- **P3 (Low):** Nice-to-have improvements, optimization opportunities → Fix within 1 quarter

---

## Part 7: Recommendations & Next Steps

### Immediate Actions (P0/P1)

1. **[Action 1]**
   - **Why:** [Rationale]
   - **Owner:** [Team/Person]
   - **Deadline:** [Date]
   - **Success Criteria:** [Measurable outcome]

2. **[Action 2]**
   - **Why:** [Rationale]
   - **Owner:** [Team/Person]
   - **Deadline:** [Date]
   - **Success Criteria:** [Measurable outcome]

### Strategic Improvements (P2/P3)

1. **[Improvement 1]**
   - **Why:** [Rationale]
   - **Effort:** [S/M/L/XL]
   - **Impact:** [Low/Medium/High]
   - **Proposed Sprint:** [Sprint number]

2. **[Improvement 2]**
   - **Why:** [Rationale]
   - **Effort:** [S/M/L/XL]
   - **Impact:** [Low/Medium/High]
   - **Proposed Sprint:** [Sprint number]

---

## Part 8: Sign-Off

**Audit Completed By:** [Name]
**Date:** [YYYY-MM-DD]
**Next Audit Due:** [YYYY-MM-DD] (Quarterly: +3 months)

**Approval:**
- [ ] **Platform Team Lead:** [Name] ✅
- [ ] **Security Lead:** [Name] ✅
- [ ] **Product Lead:** [Name] ✅

**Status:** [🟢 APPROVED / 🟡 APPROVED WITH CONDITIONS / 🔴 BLOCKED]

---

## Appendix: Automation Scripts

### A.1 Generate Dependency Snapshot
```bash
#!/bin/bash
# scripts/generate_dependency_snapshot.sh
pip freeze > docs/audit/$(date +%Y-%m-%d)/snapshot/dependencies.txt
safety check --json > docs/audit/$(date +%Y-%m-%d)/snapshot/vulnerabilities.json
pip list --outdated > docs/audit/$(date +%Y-%m-% d)/snapshot/outdated-packages.txt
```

### A.2 Generate File Manifest
```bash
#!/bin/bash
# scripts/generate_file_manifest.sh
find src/ -type f -exec sha256sum {} \; | sort > docs/audit/$(date +%Y-%m-%d)/snapshot/file-manifest.txt
```

### A.3 Run Security Scan
```bash
#!/bin/bash
# scripts/run_security_scan.sh
rg -i "password|secret|api_key|token" --type py --type js | grep -v "# noqa" > docs/audit/$(date +%Y-%m-%d)/security/secrets-scan.txt
bandit -r src/ -f json -o docs/audit/$(date +%Y-%m-%d)/security/bandit-report.json
```

### A.4 Validate SLO Compliance
```bash
#!/bin/bash
# scripts/validate_slo_compliance.sh
curl -sf "$PROMETHEUS_URL/api/v1/query?query=histogram_quantile(0.99, rate(http_request_duration_seconds_bucket{path=~\"/actions|/audit\"}[5m]))" | jq -r '.data.result[0].value[1]'
# Expected: ≤0.05 (50ms)
```

---

**Template Version:** 1.0
**Last Updated:** October 7, 2025
**Maintained By:** Platform + SRE Team
