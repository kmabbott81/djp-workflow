# Phase 3 E2E Testing Plan - Complete

**Date:** 2025-10-09
**Sprint:** 54 - Phase C (Gmail Rich Email)
**Status:** ✅ PLAN COMPLETE, READY FOR EXECUTION

## Summary

Created comprehensive E2E testing plan and automation for Gmail Rich Email with real Gmail API validation, telemetry verification, and rollout controller observation.

## Deliverables

### 1. Testing Plan Document
**File:** `docs/specs/PHASE-3-E2E-TESTING-PLAN.md` (450+ lines)

**Contents:**
- 8 comprehensive test scenarios
- Environment configuration requirements
- Metrics monitoring queries
- Success criteria and acceptance checklist
- Timeline and rollback plan

**Test Scenarios:**
1. ✅ Text-only email (baseline verification)
2. ✅ HTML + text fallback (sanitization check)
3. ✅ HTML + inline image (CID references)
4. ✅ Regular attachments (multipart/mixed)
5. ✅ Full complexity (nested multipart)
6. ✅ Validation errors (oversized, blocked MIME, orphan CID)
7. ✅ Internal-only controls (domain filtering)
8. ✅ Rollout controller observation (dry-run mode)

### 2. E2E Test Script
**File:** `scripts/e2e_gmail_test.py` (500+ lines)

**Features:**
- Automated test execution for all 8 scenarios
- Preview + execute validation
- Structured error verification
- Telemetry metrics verification
- Detailed logging with correlation IDs
- JSON results output for CI integration
- Dry-run mode support
- Configurable via CLI arguments or env vars

**Usage:**
```bash
# Run all scenarios
python scripts/e2e_gmail_test.py --scenarios all --verbose

# Run specific scenarios
python scripts/e2e_gmail_test.py --scenarios 1,2,3 --dry-run

# With explicit config
python scripts/e2e_gmail_test.py \
  --workspace-id test-workspace \
  --actor-id user@example.com \
  --recipient test@gmail.com \
  --scenarios all
```

### 3. Setup Checklist
**File:** `docs/specs/PHASE-3-SETUP-CHECKLIST.md` (350+ lines)

**Contents:**
- Infrastructure setup (Redis, Prometheus, Pushgateway)
- OAuth configuration steps
- Environment variables reference
- Verification commands
- Troubleshooting guide
- Quick start TL;DR

**Quick Start:**
```bash
# 1. Infrastructure
docker run -d -p 6379:6379 redis:alpine
docker run -d -p 9091:9091 prom/pushgateway
redis-cli SET flags:google:rollout_percent 0

# 2. Environment
export $(cat .env | xargs)

# 3. Test
python scripts/e2e_gmail_test.py --scenarios all
```

## Test Coverage

### Functional Tests
- ✅ Text-only messages (baseline)
- ✅ HTML sanitization (XSS prevention)
- ✅ Inline images with CID references
- ✅ File attachments (PDF, CSV)
- ✅ Nested multipart structures
- ✅ Validation error handling
- ✅ Internal-only recipient controls
- ✅ Rollout controller dry-run observation

### Non-Functional Tests
- ✅ Latency verification (P95 < 2s target)
- ✅ Telemetry metrics collection
- ✅ Error rate monitoring (< 1% target)
- ✅ Correlation ID logging
- ✅ OAuth token refresh
- ✅ Rollout controller SLO compliance

### Security Tests
- ✅ XSS prevention (script tag removal)
- ✅ Attachment size limits (25MB individual, 50MB total)
- ✅ Blocked MIME types (.exe, .sh, .zip)
- ✅ Domain allowlist enforcement
- ✅ OAuth token security

## Environment Requirements

### Infrastructure
- **Redis:** For rollout feature flags
- **PostgreSQL:** For OAuth tokens
- **Prometheus:** For metrics collection
- **Pushgateway:** For controller telemetry

### Configuration
- **PROVIDER_GOOGLE_ENABLED=true**
- **GOOGLE_INTERNAL_ONLY=true** (start restrictive)
- **ROLLOUT_DRY_RUN=true** (observe before changing)
- **TELEMETRY_ENABLED=true**

### OAuth Setup
- GCP project with Gmail API enabled
- OAuth 2.0 client credentials
- Test account authorized with `gmail.send` scope
- Tokens stored in database

## Metrics to Monitor

### Action Metrics
```promql
# P95 latency
histogram_quantile(0.95, rate(action_latency_seconds_bucket{provider="google"}[5m]))

# Error rate
rate(action_error_total{provider="google"}[5m]) / rate(action_execution_total{provider="google"}[5m])

# Success count
increase(action_execution_total{provider="google", status="ok"}[1h])
```

### MIME Builder Metrics
```promql
# Build time P95
histogram_quantile(0.95, rate(gmail_mime_build_seconds_bucket[5m]))

# Attachment throughput
rate(gmail_attachment_bytes_total[5m])

# HTML sanitization
rate(gmail_html_sanitization_changes_total{change_type="tag_removed"}[5m])

# CID mismatch rate
rate(gmail_inline_refs_total{result="orphan_cid"}[5m]) / rate(gmail_inline_refs_total[5m])
```

### Rollout Controller Metrics
```promql
# Controller evaluations
rollout_controller_evaluation_total{provider="google"}

# Current rollout percent
rollout_feature_percent{provider="google"}

# Promotion/rollback actions
rollout_controller_action_total{provider="google", action="promote"}
rollout_controller_action_total{provider="google", action="rollback"}
```

## Success Criteria

Phase 3 considered complete when:

1. ✅ All 8 E2E scenarios pass
2. ✅ Test emails received correctly in Gmail inbox
3. ✅ Telemetry metrics flowing to Prometheus
4. ✅ Controller observes in dry-run mode (no changes)
5. ✅ Audit logs contain expected entries
6. ✅ P95 latency < 2 seconds
7. ✅ Error rate < 1% (should be 0% for internal testing)
8. ✅ No unexpected errors in logs
9. ✅ 24-48 hours stable operation in dry-run mode

## Execution Timeline

**Day 1-2:** Environment setup
- Set up Redis, Prometheus, Pushgateway
- Configure OAuth tokens
- Verify database connectivity

**Day 3:** Run E2E tests
- Execute all 8 scenarios
- Verify emails received
- Check telemetry metrics

**Day 4-5:** Monitor dry-run mode
- Enable controller with ROLLOUT_DRY_RUN=true
- Observe 24-48 hours
- Verify no regressions

**Day 6:** Review and decision
- Analyze metrics and logs
- Decide: proceed to Phase 4 or iterate

**Day 7:** Disable dry-run (if approved)
- Set ROLLOUT_DRY_RUN=false
- Observe first automated promotion
- Monitor closely

**Total:** ~1 week for complete Phase 3

## Next Steps

After Phase 3 completes:

### Phase 4: Observability Enhancements
- Add Prometheus recording rules
- Create Grafana dashboards
- Set up alerting (PagerDuty, Slack)

### Phase 5: Gradual Public Rollout
- Flip GOOGLE_INTERNAL_ONLY=false
- Use controller for 0% → 10% → 50% → 100%
- Monitor SLO compliance at each step

### Phase 6: Studio UX Integration
- Wire up rich email composer UI
- Add attachment/inline image pickers
- Show sanitization preview

## Files Created

**Planning:**
- `docs/specs/PHASE-3-E2E-TESTING-PLAN.md` (450 lines)
- `docs/specs/PHASE-3-SETUP-CHECKLIST.md` (350 lines)
- `docs/evidence/sprint-54/PHASE-3-E2E-PLAN-COMPLETE.md` (this file)

**Automation:**
- `scripts/e2e_gmail_test.py` (500 lines)

**Total:** 4 files, ~1,400 lines

## Key Features

### Test Script Features
1. **Automated execution** - Run all scenarios with single command
2. **Dry-run mode** - Preview-only testing without Gmail sends
3. **Structured validation** - Verify error codes and payloads
4. **Telemetry checks** - Confirm metrics collection
5. **JSON output** - CI/CD integration ready
6. **Detailed logging** - Correlation ID tracking
7. **Configurable** - CLI args or environment variables

### Test Scenarios
1. **Happy paths** - Text, HTML, inline, attachments, full complexity
2. **Error paths** - Validation failures with structured errors
3. **Security** - Domain filtering, XSS prevention, MIME blocking
4. **Observability** - Controller dry-run, metrics verification

### Infrastructure Support
1. **Redis** - Feature flag storage
2. **Prometheus** - Metrics collection and querying
3. **Pushgateway** - Controller telemetry
4. **PostgreSQL** - OAuth token persistence

## Risk Mitigation

### Rollback Plan
If issues found during E2E:
```bash
# Immediate stop
redis-cli SET flags:google:rollout_percent 0
# or
export PROVIDER_GOOGLE_ENABLED=false
```

### Dry-Run Protection
- Start with ROLLOUT_DRY_RUN=true
- Controller observes but doesn't change state
- Safe to run for 24-48 hours before enabling

### Internal-Only First
- GOOGLE_INTERNAL_ONLY=true by default
- Controlled recipient list
- Test thoroughly before public rollout

## Documentation Quality

All documentation includes:
- ✅ Clear prerequisites
- ✅ Step-by-step instructions
- ✅ Example commands (copy-pasteable)
- ✅ Verification steps
- ✅ Troubleshooting guides
- ✅ Success criteria
- ✅ Rollback procedures

## Ready for Execution

Phase 3 planning is **complete**. All documentation, automation, and checklists are ready for execution.

**Next action:** Set up test environment per `PHASE-3-SETUP-CHECKLIST.md` and execute E2E tests.

---

**PHASE 3 PLAN: COMPLETE** ✅
**READY FOR:** Environment setup and E2E execution
**ESTIMATED TIME:** ~1 week (setup + testing + observation)
