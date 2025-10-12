# Sprint 54 Phase C: Kickoff Evidence
**Date**: 2025-10-08
**Status**: Ready for Implementation
**Duration**: 10-12 days (Oct 8 - Oct 20, 2025)
**Branch**: `sprint/54-gmail-rich-email`

---

## 1. Executive Summary

**Mission**: Extend Sprint 53's Gmail send integration with rich email features (HTML, file attachments, inline images) and build Studio "Connect Google" UX for end users.

**Scope**:
- ✅ HTML email support (sanitized safe subset)
- ✅ File attachments (up to 10 per email, 25MB each)
- ✅ Inline images with Content-ID (CID) references
- ✅ Studio Google integration UX (OAuth flow, send form, error handling)
- ✅ Comprehensive test coverage (105+ tests)
- ✅ Observability (metrics, alerts, dashboards)

**Key Constraints**:
- Feature-flagged: `PROVIDER_GOOGLE_RICH_EMAIL_ENABLED=false` by default
- No code ships to production until ALL phase gates pass
- Rollout strategy: shadow mode → internal canary → limited beta → full rollout

**Estimated Effort**:
- Development: 6-7 days
- Testing: 2-3 days
- Rollout monitoring: 1-2 days per phase

---

## 2. Planning Documents

All planning documents are complete and ready for implementation:

| **Document** | **Path** | **Status** |
|-------------|---------|-----------|
| Sprint Plan | `docs/planning/SPRINT-54-PLAN.md` | ✅ Complete |
| Gmail API Spec | `docs/specs/GMAIL-RICH-EMAIL-SPEC.md` | ✅ Complete |
| Studio UX Spec | `docs/specs/STUDIO-GOOGLE-UX.md` | ✅ Complete |
| Test Matrix | `tests/plans/SPRINT-54-TEST-MATRIX.md` | ✅ Complete |
| Observability Plan | `docs/observability/PHASE-C-OBSERVABILITY.md` | ✅ Complete |
| Scaffolds Script | `scripts/dev/scaffolds.sh` | ✅ Complete |
| Kickoff Evidence | `docs/evidence/sprint-54/PHASE-C-KICKOFF.md` | ✅ Complete (this doc) |

---

## 3. Technical Architecture

### 3.1 New Modules

**Backend**:
- `src/actions/adapters/google_mime.py` - MIME message builder (multipart/mixed, multipart/alternative, multipart/related)
- `src/actions/validation/attachments.py` - Attachment validation (size, count, MIME type, filename)
- `src/actions/validation/html_sanitization.py` - HTML sanitization (bleach-based allowlist)

**Frontend (Studio)**:
- `src/studio/components/GoogleConnect.tsx` - OAuth connection UI
- `src/studio/components/GmailSendForm.tsx` - Rich email send form
- `src/studio/components/AttachmentUpload.tsx` - File upload with validation

### 3.2 Extended Modules

**Backend**:
- `src/actions/adapters/google.py` - Add `html`, `attachments[]`, `inline[]` parameters to preview/execute
- `src/webapi.py` - Add feature flag gate for rich email params

**Tests**:
- `tests/actions/test_google_mime_unit.py` (25 tests)
- `tests/actions/test_html_sanitization_unit.py` (20 tests)
- `tests/actions/test_attachment_validation_unit.py` (15 tests)
- `tests/actions/test_gmail_adapter_extended_unit.py` (20 tests)
- `tests/integration/test_google_rich_email_flow.py` (10 tests, quarantined)

### 3.3 Data Model

**No database schema changes required**. All data flows through existing `/actions/preview` and `/actions/execute` endpoints.

**Request Schema Extension**:
```json
{
  "action_id": "gmail.send",
  "parameters": {
    "to": "user@example.com",
    "subject": "Hello",
    "body": "Plain text body",
    "html": "<p>HTML body</p>",  // NEW
    "attachments": [              // NEW
      {
        "content": "base64_encoded_bytes",
        "filename": "report.pdf",
        "content_type": "application/pdf"
      }
    ],
    "inline": [                   // NEW
      {
        "content": "base64_encoded_bytes",
        "content_id": "logo",
        "filename": "logo.png",
        "content_type": "image/png"
      }
    ]
  }
}
```

---

## 4. Feature Flags

| **Flag** | **Default** | **Purpose** | **Controlled By** |
|---------|------------|-----------|------------------|
| `PROVIDER_GOOGLE_ENABLED` | `false` | Enable Google OAuth + Gmail send (Sprint 53) | Env var |
| `PROVIDER_GOOGLE_RICH_EMAIL_ENABLED` | `false` | Enable HTML, attachments, inline images (Sprint 54) | Env var |
| `ATTACHMENTS_ENABLED` | `false` | Global kill switch for all attachments (cross-provider) | Env var |

**Safety**:
- All flags default to `false` in production
- Can disable rich email features without disabling basic Gmail send
- `ATTACHMENTS_ENABLED` provides cross-provider kill switch

---

## 5. Risks & Mitigations

| **Risk** | **Severity** | **Mitigation** |
|---------|-------------|---------------|
| **Token scope creep** | High | Feature-flag rich email separately from basic send; require explicit user consent in Studio OAuth flow |
| **Oversize payloads** | High | Hard limit: 35MB total (Gmail API max); client-side validation in Studio; server-side validation before MIME build |
| **Gmail API quota exhaustion** | Medium | Monitor `GmailQuotaNearExhaustion` alert (>80% daily quota); implement rate limiting if needed |
| **Abuse vectors** | High | MIME type blocklist (.exe, .sh, .zip); filename extension blocklist; HTML sanitization with bleach |
| **XSS via HTML injection** | Critical | Allowlist-based sanitization (ALLOWED_TAGS, ALLOWED_ATTRIBUTES); strip all `<script>`, `<iframe>`, event handlers |

---

## 6. Rollout Strategy (4 Phases)

### Phase 1: Shadow Mode (Week 1)
**Goal**: Verify scaffolds, test coverage, and monitoring setup

**Actions**:
- Deploy to staging with `PROVIDER_GOOGLE_RICH_EMAIL_ENABLED=false`
- Run full test suite (105+ tests)
- Verify Prometheus metrics appear in Grafana
- Confirm alerts configured in Alertmanager

**Success Criteria**:
- All unit tests pass (90+ tests)
- Integration tests quarantined correctly
- Dashboards render in Grafana
- No regression in existing Gmail send (plain text)

**Gate**: Engineering Lead approval

---

### Phase 2: Internal Canary (Week 2)
**Goal**: Supervised live testing with internal users

**Actions**:
- Enable `PROVIDER_GOOGLE_RICH_EMAIL_ENABLED=true` for internal test accounts only
- Studio UX: Beta banner at top ("Gmail Rich Email: Internal Testing")
- Send 10-20 test emails (HTML, attachments, inline images)
- Monitor metrics: MIME build latency, validation errors, quota usage

**Success Criteria**:
- MIME build P95 latency < 500ms
- Validation error rate < 1%
- No orphan CID references detected
- Studio OAuth flow success rate > 95%
- Zero XSS/security incidents

**Gate**: Product + Engineering approval; no P0/P1 incidents for 48h

---

### Phase 3: Limited Beta (Week 3)
**Goal**: Gradual rollout to 10% of production users

**Actions**:
- Enable `PROVIDER_GOOGLE_RICH_EMAIL_ENABLED=true` for 10% of traffic (user ID hash-based)
- Studio UX: Remove beta banner for selected users
- Monitor for 48h with all alerts active
- Gather user feedback (Studio in-app survey)

**Success Criteria**:
- Error rate < 1% (SLO: 99% success)
- P95 latency < 500ms (SLO)
- No Gmail API quota alerts
- HTML sanitization change rate stable (no excessive removals)
- User feedback positive (NPS > 7)

**Gate**: Product approval; SLOs green for 48h; no P0/P1/P2 incidents

---

### Phase 4: Full Rollout (Week 4)
**Goal**: 100% availability to all users

**Actions**:
- Enable `PROVIDER_GOOGLE_RICH_EMAIL_ENABLED=true` for 100% of traffic
- Update docs: Mark feature as GA (Generally Available)
- Announce feature launch (blog post, changelog)

**Success Criteria**:
- All SLOs maintained (error rate, latency, availability)
- No increase in support tickets
- Feature adoption measured (% of Gmail sends using HTML/attachments)

**Gate**: Product approval; 7 days of stable operation

---

## 7. Test Coverage Summary

| **Module** | **Unit Tests** | **Integration Tests** | **Coverage Target** |
|-----------|---------------|---------------------|-------------------|
| MIME Builder | 25 | 2 | >95% |
| HTML Sanitization | 20 | 2 | >90% |
| Attachment Validation | 15 | 2 | >90% |
| Gmail Adapter (Extended) | 20 | 2 | >90% |
| Studio UX | 15 (Jest) | N/A | >85% |
| E2E Smoke | N/A | 5 | N/A |
| **Total** | **95** | **13** | **>90% overall** |

**Test Isolation**:
- Unit tests: No network, mocked Gmail API
- Integration tests: Quarantined with `@pytest.mark.integration`, skipped in CI
- Smoke tests: Run post-deployment on staging

---

## 8. Observability Plan

### 8.1 New Metrics

| **Metric** | **Type** | **Purpose** |
|-----------|---------|-----------|
| `gmail_mime_build_seconds` | Histogram | Track MIME build latency by structure type |
| `gmail_attachment_bytes_total` | Counter | Monitor attachment payload sizes |
| `gmail_inline_refs_total` | Counter | Track inline CID match rate (detect orphans) |
| `gmail_html_sanitization_seconds` | Histogram | HTML cleaning latency |
| `gmail_html_sanitization_changes_total` | Counter | Track tags/attributes removed |
| `gmail_validation_errors_total` | Counter | Validation error reasons (bounded taxonomy) |
| `studio_google_oauth_flow_total` | Counter | OAuth success rate from Studio |
| `studio_gmail_send_attempts_total` | Counter | Studio Gmail send attempts (by result) |

### 8.2 Alert Rules

| **Alert** | **Threshold** | **Severity** | **SLO** |
|----------|-------------|-------------|---------|
| `GmailMIMEBuildSlow` | P95 > 500ms for 5m | Warning | Latency SLO |
| `GmailValidationErrorsHigh` | Error rate > 5% for 10m | Warning | Error rate SLO |
| `GmailInlineCIDOrphansHigh` | Orphan rate > 10% for 5m | Warning | Data quality |
| `GmailQuotaNearExhaustion` | >80% daily quota | Critical | Availability SLO |
| `StudioGmailOAuthFailureHigh` | Success rate < 90% for 10m | Warning | UX quality |

### 8.3 Dashboards

**New Panels** (added to `relay-actions-gmail.json`):
1. Gmail Rich Email Features (HTML usage, attachment usage, plain text)
2. MIME Build Latency (P50/P95/P99)
3. Attachment Bytes & Inline CIDs
4. Validation Errors Breakdown (top 5)
5. HTML Sanitization Activity (tags/attributes/CSS removed)

**New Dashboard** (Studio):
- `relay-studio.json`: Google OAuth Success Rate gauge

---

## 9. Open Questions & Decisions Needed

| **Question** | **Owner** | **Deadline** | **Status** |
|-------------|---------|------------|-----------|
| 1. Gmail API daily quota? | DevOps | Before Phase 2 | ⏳ Pending |
| 2. Attachment storage: direct upload or presigned URLs? | Engineering Lead | Before Phase 1 | ⏳ Pending |
| 3. HTML sanitization library: bleach or html5lib? | Engineering | Before Phase 1 | ✅ Decided: bleach |
| 4. Studio vs API-driven sends: separate metrics? | Product | Before Phase 2 | ⏳ Pending |
| 5. Content-ID generation: client-side or server-side? | Engineering | Before Phase 1 | ⏳ Pending |

---

## 10. Go/No-Go Checklist

### 10.1 Phase Gate 0: Pre-Implementation

- [x] All planning documents complete (7 docs)
- [x] Sprint 53 Phase B merged and deployed (PR #34)
- [x] `PROVIDER_GOOGLE_ENABLED=false` in production
- [x] Feature flags defined (`PROVIDER_GOOGLE_RICH_EMAIL_ENABLED`, `ATTACHMENTS_ENABLED`)
- [x] Scaffolds script ready (`scripts/dev/scaffolds.sh`)
- [ ] Open questions resolved (5 questions pending)
- [ ] Engineering team capacity confirmed (10-12 days)

**Decision**: ⏳ Pending (resolve open questions first)

---

### 10.2 Phase Gate 1: Shadow Mode → Internal Canary

**Prerequisites**:
- [ ] All unit tests passing (95+ tests)
- [ ] Integration tests quarantined correctly
- [ ] Prometheus metrics visible in Grafana
- [ ] Alert rules configured in Alertmanager
- [ ] Dashboards render correctly
- [ ] No regression in plain text Gmail send
- [ ] Code review approved by 2+ engineers
- [ ] Security review: HTML sanitization, MIME type blocklist

**Go/No-Go Decision**:
- **GO**: All prerequisites met, Engineering Lead approval
- **NO-GO**: Test failures, missing metrics, security concerns

**Rollback Plan**: Disable `PROVIDER_GOOGLE_RICH_EMAIL_ENABLED`, fall back to plain text only

---

### 10.3 Phase Gate 2: Internal Canary → Limited Beta

**Prerequisites**:
- [ ] Internal testing complete (10-20 test emails sent)
- [ ] MIME build P95 latency < 500ms
- [ ] Validation error rate < 1%
- [ ] No orphan CID references
- [ ] Studio OAuth success rate > 95%
- [ ] Zero security incidents (XSS, malicious attachments)
- [ ] No Gmail API quota alerts
- [ ] No P0/P1 incidents for 48h

**Go/No-Go Decision**:
- **GO**: All SLOs met, Product + Engineering approval
- **NO-GO**: Latency issues, high error rate, security incident

**Rollback Plan**: Reduce to 1% traffic or disable entirely

---

### 10.4 Phase Gate 3: Limited Beta → Full Rollout

**Prerequisites**:
- [ ] 10% beta running stable for 48h
- [ ] Error rate < 1% (SLO)
- [ ] P95 latency < 500ms (SLO)
- [ ] HTML sanitization stable (no excessive removals)
- [ ] User feedback positive (NPS > 7)
- [ ] No increase in support tickets
- [ ] No P0/P1/P2 incidents during beta
- [ ] Runbooks tested (at least 1 incident drilled)

**Go/No-Go Decision**:
- **GO**: All SLOs green, Product approval, 48h stable
- **NO-GO**: SLO violations, negative feedback, P2+ incidents

**Rollback Plan**: Revert to 10% traffic, investigate root cause

---

### 10.5 Phase Gate 4: Full Rollout → GA

**Prerequisites**:
- [ ] 100% traffic running stable for 7 days
- [ ] All SLOs maintained
- [ ] Feature adoption measured (% of sends using HTML/attachments)
- [ ] Docs updated (mark as GA)
- [ ] Changelog published
- [ ] Blog post announcing feature (optional)

**Go/No-Go Decision**:
- **GO**: 7 days stable, Product approval
- **NO-GO**: SLO degradation, unexpected issues

**Rollback Plan**: Feature flags remain in place; can disable if needed

---

## 11. Definition of Done

Sprint 54 Phase C is **COMPLETE** when:

### Code
- [x] Scaffolds generated (`scripts/dev/scaffolds.sh` run)
- [ ] All modules implemented (MIME builder, validation, sanitization)
- [ ] Gmail adapter extended with `html`, `attachments[]`, `inline[]` params
- [ ] Studio UX components built (GoogleConnect, GmailSendForm, AttachmentUpload)
- [ ] Feature flags integrated (`PROVIDER_GOOGLE_RICH_EMAIL_ENABLED`, `ATTACHMENTS_ENABLED`)

### Tests
- [ ] 95+ unit tests passing (>90% coverage)
- [ ] 13 integration tests written (quarantined by default)
- [ ] 5 E2E smoke tests passing on staging
- [ ] Security tests: XSS prevention, malicious file upload

### Documentation
- [x] Sprint plan complete
- [x] API spec complete
- [x] Studio UX spec complete
- [x] Test matrix complete
- [x] Observability plan complete
- [ ] Runbooks written (MIME build slow, validation errors high, orphan CIDs)
- [ ] User-facing docs (Studio help articles)

### Observability
- [ ] 8 new metrics instrumented
- [ ] 5 alert rules configured
- [ ] 6 dashboard panels added
- [ ] Structured logging added (MIME build, sanitization, validation)

### Rollout
- [ ] Phase 1 (Shadow Mode): Complete
- [ ] Phase 2 (Internal Canary): Complete
- [ ] Phase 3 (Limited Beta): Complete
- [ ] Phase 4 (Full Rollout): Complete
- [ ] Post-launch review conducted

---

## 12. Success Metrics (30 Days Post-Launch)

| **Metric** | **Target** | **Measurement** |
|-----------|-----------|----------------|
| **Error Rate** | < 1% | `sum(rate(gmail_validation_errors_total[30d])) / sum(rate(relay_actions_executed_total{action_id="gmail.send"}[30d]))` |
| **P95 Latency** | < 500ms | `histogram_quantile(0.95, sum by (le) (rate(gmail_mime_build_seconds_bucket[30d])))` |
| **Availability** | > 99.5% | Gmail API quota not exceeded; no prolonged outages |
| **Feature Adoption** | > 20% | Percentage of Gmail sends using HTML or attachments |
| **Security Incidents** | 0 | No XSS, no malicious file uploads, no token leaks |
| **User Satisfaction** | NPS > 7 | Studio in-app survey |

---

## 13. Next Steps (Immediate)

1. **Resolve Open Questions** (before implementation):
   - Confirm Gmail API daily quota limit
   - Decide attachment storage strategy (direct vs presigned URLs)
   - Finalize Content-ID generation approach

2. **Run Scaffolds Script**:
   ```bash
   bash scripts/dev/scaffolds.sh
   ```

3. **Install Dependencies**:
   ```bash
   pip install bleach  # HTML sanitization library
   ```

4. **Start Implementation** (in order):
   - Implement `MimeBuilder.build_simple_text()` first (simplest case)
   - Write unit tests for each method (TDD approach)
   - Implement HTML sanitization with `bleach.clean()`
   - Implement attachment validation (size, count, MIME type)
   - Extend Gmail adapter with new parameters
   - Add telemetry metrics
   - Build Studio UX components (React/TypeScript)

5. **Create Feature Branch**:
   ```bash
   git checkout -b sprint/54-gmail-rich-email
   ```

---

## 14. Automated Rollout (Recommended)

**Sprint 53.5**: Automated SLO-based rollout controller.

### Quick Start

1. **Configure GitHub Secrets** (one-time setup):
   - `REDIS_URL` - Redis connection URL
   - `PROMETHEUS_BASE_URL` - Prometheus server URL

2. **Initialize Redis** (one-time setup):
   ```bash
   redis-cli SET flags:google:enabled "true"
   redis-cli SET flags:google:internal_only "true"
   redis-cli SET flags:google:rollout_percent "0"
   redis-cli SET flags:google:paused "false"
   ```

3. **Enable Controller**:
   - Merge this PR (includes `.github/workflows/rollout-controller.yml`)
   - Controller runs automatically every 10 minutes

4. **Monitor**:
   - Check **Actions** tab → **Rollout Controller** workflow
   - View audit log: `docs/evidence/sprint-54/rollout_log.md`
   - Prometheus alerts (GmailErrorRateHigh, GmailLatencySlow, OAuthRefreshFailures)

**Automatic progression:**
```
0% → 10% → 50% → 100% (when SLOs green)
Any % → 10% (when SLO violated)
```

**Safety guards:**
- 15 min dwell time between changes
- 1 hour cooldown after rollback
- Manual pause: `redis-cli SET flags:google:paused "true"`

**Detailed guide:** See `docs/evidence/sprint-54/CONTROLLER-USAGE.md`

---

## 14B. Manual Rollout Playbook (Alternative)

**If you prefer manual control**, use this 7-day playbook instead of the automated controller.

### Prerequisites

1. **PR #34 merged** (Sprint 53 Phase B: Google OAuth + Gmail send)
2. **Rollout seams implemented** (see commit SHA from this PR)
3. **Redis running** with `REDIS_URL` configured
4. **Prometheus alerts deployed** (3 Gmail SLO alerts)

### Redis Configuration

Set these keys in Redis before rollout:

```bash
# Redis CLI
redis-cli

SET flags:google:enabled "true"
SET flags:google:internal_only "true"
SET flags:google:rollout_percent "0"
```

Or via Python:

```python
import redis
r = redis.from_url(os.getenv("REDIS_URL"))
r.set("flags:google:enabled", "true")
r.set("flags:google:internal_only", "true")
r.set("flags:google:rollout_percent", "0")
```

### Rollout Schedule

#### **Day 0: Merge & Baseline**
- **Action**: Merge PR #34 + rollout seams PR
- **Config**: `PROVIDER_GOOGLE_ENABLED=false`, `rollout_percent=0`
- **Check**: All tests pass, no regressions

#### **Day 1-2: Internal Test (0% → 10%)**
- **Action**:
  1. Set `PROVIDER_GOOGLE_ENABLED=true` (env var)
  2. Keep `internal_only=true`, `rollout_percent=0`
  3. Send 5-10 test emails manually
  4. Verify alerts stay quiet
- **Log**: Record results in `docs/evidence/sprint-54/rollout_log.md`

#### **Day 3: Initial Canary (10%)**
- **Action**:
  ```bash
  redis-cli SET flags:google:rollout_percent "10"
  ```
- **Log**:
  ```python
  from src.rollout.audit import append_rollout_log
  append_rollout_log("google", 0, 10, "Initial canary test", by="manual")
  ```
- **Monitor**: Watch Grafana for 24h:
  - `GmailErrorRateHigh` alert (should stay quiet)
  - `GmailLatencySlow` alert (should stay quiet)
  - `OAuthRefreshFailures` alert (should stay quiet)
- **Success Criteria**: Error rate <1%, P95 latency <500ms, 0 OAuth failures

#### **Day 5: Ramp to 50%**
- **Prerequisite**: Day 3-4 monitoring clean (no alerts fired)
- **Action**:
  ```bash
  redis-cli SET flags:google:rollout_percent "50"
  ```
- **Log**:
  ```python
  append_rollout_log("google", 10, 50, "Healthy → ramp to 50%", by="manual")
  ```
- **Monitor**: Watch for 48h
- **Rollback Plan**: If ANY alert fires:
  ```bash
  redis-cli SET flags:google:rollout_percent "10"
  ```
  Log rollback:
  ```python
  append_rollout_log("google", 50, 10, "Alert fired: <reason>", by="manual")
  ```

#### **Day 7+: Full Rollout (100%)**
- **Prerequisite**: Day 5-6 monitoring clean
- **Action**:
  ```bash
  redis-cli SET flags:google:rollout_percent "100"
  ```
- **Log**:
  ```python
  append_rollout_log("google", 50, 100, "Healthy → full rollout", by="manual")
  ```
- **Monitor**: Watch for 7 days
- **Final Step**: Set `internal_only=false` when ready for external traffic
  ```bash
  redis-cli SET flags:google:internal_only "false"
  ```

### Monitoring Checklist

**Daily checks during rollout:**

- [ ] Check Grafana Gmail dashboard
  - Error rate trend (should be <1%)
  - P95 latency trend (should be <500ms)
  - OAuth refresh success rate (should be >95%)

- [ ] Check Prometheus alerts
  - `GmailErrorRateHigh` - Should be green
  - `GmailLatencySlow` - Should be green
  - `OAuthRefreshFailures` - Should be green

- [ ] Check rollout audit log
  ```bash
  cat docs/evidence/sprint-54/rollout_log.md
  ```

- [ ] Check action execution metrics
  ```promql
  # Total Gmail sends
  sum(increase(action_exec_total{provider="google",action="gmail.send"}[1d]))

  # Error rate
  sum(increase(action_error_total{provider="google"}[1d]))
    /
  sum(increase(action_exec_total{provider="google"}[1d]))
  ```

### Rollback Procedures

**Immediate rollback** (if ANY alert fires):

1. **Reduce rollout percentage**:
   ```bash
   redis-cli SET flags:google:rollout_percent "0"  # or "10" to hold at canary
   ```

2. **Log the rollback**:
   ```python
   from src.rollout.audit import append_rollout_log
   append_rollout_log(
       "google",
       old_pct=50,  # Current %
       new_pct=10,  # Safe %
       reason="Alert: GmailErrorRateHigh fired - error rate 2.3%",
       by="manual"
   )
   ```

3. **Investigate**:
   - Check Prometheus for error spike timing
   - Query logs for specific error reasons
   - Review recent code changes

4. **Document findings**:
   - Add to `docs/evidence/sprint-54/rollout_log.md`
   - File GitHub issue if bug found
   - Update SLO thresholds if false positive

### Tuning SLO Thresholds

During manual rollout, you may need to adjust policy thresholds in `src/rollout/policy.py`:

**Example: Error rate threshold too sensitive**

If you observe 1.2% error rate is normal (e.g., user typos in email addresses):

```python
# Before
if error_rate > 0.01:  # 1%
    return Recommendation(...)

# After
if error_rate > 0.03:  # 3% (more tolerant)
    return Recommendation(...)
```

**Document all threshold changes** in rollout log with rationale.

### Post-Rollout Actions

After 7 days at 100% with no incidents:

1. **Mark rollout complete**:
   - Update `docs/evidence/sprint-54/PHASE-C-KICKOFF.md` (this doc)
   - Set "Rollout" checklist items to complete

2. **Retrospective**:
   - What SLO thresholds needed tuning?
   - Were there any false positives?
   - How long did each phase actually take?
   - Document lessons learned

3. **Prepare for automated controller** (Sprint 55+):
   - Review rollout log for patterns
   - Finalize threshold values
   - Implement `scripts/rollout_controller.py` using tuned policy

---

## 15. References

- **Sprint 53 Phase B PR**: https://github.com/kmabbott81/djp-workflow/pull/34
- **Planning Docs**: `docs/planning/SPRINT-54-PLAN.md`
- **API Spec**: `docs/specs/GMAIL-RICH-EMAIL-SPEC.md`
- **Studio UX Spec**: `docs/specs/STUDIO-GOOGLE-UX.md`
- **Test Matrix**: `tests/plans/SPRINT-54-TEST-MATRIX.md`
- **Observability**: `docs/observability/PHASE-C-OBSERVABILITY.md`
- **Scaffolds**: `scripts/dev/scaffolds.sh`

---

## 15. Sign-Off

| **Role** | **Name** | **Date** | **Approval** |
|---------|---------|---------|-------------|
| Product Owner | TBD | TBD | ⏳ Pending |
| Engineering Lead | TBD | TBD | ⏳ Pending |
| Security Review | TBD | TBD | ⏳ Pending |
| DevOps | TBD | TBD | ⏳ Pending |

**Sprint Status**: ✅ Ready for Implementation (pending open question resolution)

---

**Document Version**: 1.0
**Last Updated**: 2025-10-08
**Author**: Claude (AI Assistant)
**Review Status**: Awaiting Team Review
