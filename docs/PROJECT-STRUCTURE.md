# Project Structure and Organization

**Last Updated:** 2025-10-10
**Sprint:** 54
**Status:** Active reorganization

---

## Overview

This document provides a comprehensive map of the project structure, naming conventions, and file organization patterns established over the past 10+ sprints.

---

## Root Directory Organization

### Naming Conventions

#### Sprint Completion Documents
**Pattern:** `YYYY.MM.DD-HHMM-<DESCRIPTION>-COMPLETE.md`

**Purpose:** Major milestone completion documents with timestamps

**Examples:**
- `2025.10.10-PHASE-3-OAUTH-COMPLETE.md` - Phase 3 OAuth setup completed
- `2025.10.04-SPRINT42-PERF-TELEMETRY-PLAN.md` - Sprint 42 planning
- `2025.10.01-1906-SPRINT5-DEPLOYMENT-COMPLETE.md` - Sprint 5 deployment milestone

#### Project Documentation (Stable)
**Pattern:** `UPPERCASE-HYPHENATED-NAME.md`

**Purpose:** Long-term project documentation, guides, and references

**Examples:**
- `README.md` - Project introduction
- `DEVELOPMENT.md` - Development guide
- `SECURITY.md` - Security policies
- `CONTRIBUTING.md` - Contribution guidelines
- `CHANGELOG.md` - Version history
- `ACTIONS-SPEC.md` - Actions specification

#### Temporary/Working Documents
**Pattern:** Various

**Purpose:** Work-in-progress documents, handoffs, prompts

**Examples:**
- `PHASE3_STATUS.md` - Current phase status (temporary)
- `CHATGPT_SUMMARY.md` - ChatGPT interaction summary
- `HANDOFF-2025.10.02.md` - Team handoff document

---

## Directory Structure

### `/docs` - Documentation Hub

#### `/docs/evidence/sprint-XX/` - Sprint Evidence
**Pattern:** Sprint-specific evidence files

**Naming Convention:**
- `YYYY.MM.DD-<DESCRIPTION>-COMPLETE.md` (timestamped milestones)
- `UPPERCASE-DESCRIPTION.md` (stable references)

**Sprint 54 Examples:**
- `2025.10.10-PHASE-3-OAUTH-SETUP-COMPLETE.md` - OAuth setup evidence
- `PHASE-2-INTEGRATION-COMPLETE.md` - Phase 2 completion
- `PHASE-3-E2E-PLAN-COMPLETE.md` - Phase 3 planning
- `MILESTONE-ROLLOUT-INFRASTRUCTURE.md` - Rollout milestone
- `GMAIL-RICH-EMAIL-COMPLETION.md` - Gmail integration

#### `/docs/planning/` - Sprint Planning
**Pattern:** `SPRINT-XX-PLAN.md`

**Purpose:** Sprint planning documents

**Example:** `SPRINT-54-PLAN.md`

#### `/docs/specs/` - Technical Specifications
**Pattern:** `UPPERCASE-SPEC-NAME.md`

**Purpose:** Detailed technical specifications and design docs

**Sprint 54 Examples:**
- `OAUTH-SETUP-GUIDE.md` - OAuth setup instructions
- `PHASE-3-E2E-TESTING-PLAN.md` - E2E test plan (450 lines)
- `PHASE-3-SETUP-CHECKLIST.md` - Setup checklist
- `GMAIL-RICH-EMAIL-SPEC.md` - Gmail rich email spec
- `GMAIL-RICH-EMAIL-INTEGRATION-DESIGN.md` - Design document
- `GMAIL-INTEGRATION-CONTINUATION.md` - Continuation plan
- `STUDIO-GOOGLE-UX.md` - UX specifications

#### `/docs/observability/` - Observability
**Pattern:** `PHASE-X-OBSERVABILITY.md`

**Purpose:** Monitoring, metrics, and observability documentation

**Example:** `PHASE-C-OBSERVABILITY.md`

#### `/docs/alignment/` - AI Context and Alignment
**Pattern:** `YYYY.MM.DD_<SOURCE>-<DESCRIPTION>.txt`

**Purpose:** Prompts and context from external AI tools

**Example:** `2025.10.08_RELAY_AI-CONTEXT_CHATGPT.txt`

---

### `/scripts` - Automation Scripts

#### `/scripts/` - Root Scripts
**Purpose:** Main automation scripts, E2E tests, utilities

**Examples:**
- `e2e_gmail_test.py` - E2E test suite (8 scenarios)
- `generate_mime_samples.py` - MIME sample generator
- `verify_dry_run.py` - Dry-run verification

#### `/scripts/dev/` - Development Utilities
**Purpose:** Development helper scripts

**Contents:** Development tools and utilities

#### `/scripts/oauth/` - OAuth Helper Scripts (Recommended)
**Purpose:** OAuth setup and token management scripts

**Current Location:** `scripts/*.py` (should be moved here)

**Scripts:**
- `manual_token_setup.py` - Interactive OAuth flow
- `complete_oauth.py` - Non-interactive OAuth completion
- `store_tokens.py` - Manual token storage
- `oauth_flow.py` - OAuth flow helper

---

### `/src` - Source Code

#### `/src/actions/adapters/` - Action Adapters
**Purpose:** Provider-specific action implementations

**Examples:**
- `google.py` - Google API adapter
- `google_mime.py` - MIME message builder

#### `/src/auth/oauth/` - OAuth Implementation
**Purpose:** OAuth state and token management

**Files:**
- `state.py` - State management (Redis-backed)
- `tokens.py` - Token storage and encryption

#### `/src/telemetry/` - Telemetry and Metrics
**Purpose:** Prometheus metrics and observability

**Files:**
- `prom.py` - Prometheus metrics definitions

#### `/src/validation/` - Validation Layer
**Purpose:** Input validation and error handling

**Contents:** Validation utilities

#### `/src/rollout/` - Rollout Controller
**Purpose:** SLO-driven rollout controller

**Files:**
- `controller.py` - Main controller logic

#### `/src/webapi.py` - Web API
**Purpose:** FastAPI application with OAuth endpoints

**Key Endpoints:**
- `/oauth/google/authorize` - OAuth authorization flow
- `/oauth/google/callback` - OAuth callback handler

---

### `/tests` - Test Suites

#### `/tests/actions/` - Action Tests
**Purpose:** Unit tests for action adapters

**Examples:**
- `test_google_adapter_errors.py` - Error handling tests
- `test_google_mime_unit.py` - MIME builder unit tests
- `test_mime_performance.py` - Performance tests

#### `/tests/plans/` - Plan Tests
**Purpose:** Test plans and test case definitions

#### `/tests/validation/` - Validation Tests
**Purpose:** Tests for validation layer

---

### `/audit` - Audit Logs
**Pattern:** `audit-YYYY-MM-DD.jsonl`

**Purpose:** JSON Lines audit logs for observability

**Example:** `audit-2025-10-09.jsonl`

---

### `/logs` - Application Logs
**Pattern:** `<component>.jsonl`

**Purpose:** Structured application logs

**Examples:**
- `connectors.jsonl` - Connector logs
- `teams.jsonl` - Teams logs
- `connectors/circuit_state.jsonl` - Circuit breaker state
- `connectors/metrics.jsonl` - Connector metrics

---

### `/.github/workflows/` - CI/CD
**Purpose:** GitHub Actions workflows

**Example:** `rollout-controller.yml` - Rollout controller automation

---

## Root-Level Scripts and Configuration

### OAuth Setup Scripts (Temporary)
**Current Location:** Root directory

**Files:**
- `start_oauth_server.bat` - Windows batch script for OAuth server
- `start_server.py` - Python-based server startup with `.env.e2e` loading
- `oauth_start.html` - OAuth start page (temporary test file)

**Recommendation:** Keep for E2E testing phase, archive after Phase 3 completion

### Configuration Files
- `.env.e2e` - E2E testing environment variables
- `.claude/` - Claude Code configuration

---

## File Organization Recommendations

### Phase 3 (Current)
1. ✅ Root-level summary created: `2025.10.10-PHASE-3-OAUTH-COMPLETE.md`
2. ✅ Detailed evidence: `docs/evidence/sprint-54/2025.10.10-PHASE-3-OAUTH-SETUP-COMPLETE.md`
3. ⚠️ Keep OAuth scripts in root for now (referenced by documentation)
4. ⚠️ Keep `PHASE3_STATUS.md` for quick reference during testing

### Post-Phase 3 Cleanup
1. Archive OAuth setup scripts to `scripts/archive/oauth-setup/`
2. Remove temporary OAuth files (`oauth_start.html`, `start_oauth_server.bat`)
3. Consolidate `PHASE3_STATUS.md` into evidence document
4. Update this structure document

---

## Naming Convention Summary

| File Type | Pattern | Location | Example |
|-----------|---------|----------|---------|
| Sprint Milestone | `YYYY.MM.DD-HHMM-DESC-COMPLETE.md` | Root or `/docs/evidence/sprint-XX/` | `2025.10.10-PHASE-3-OAUTH-COMPLETE.md` |
| Sprint Evidence | `YYYY.MM.DD-DESC-COMPLETE.md` or `UPPERCASE-DESC.md` | `/docs/evidence/sprint-XX/` | `PHASE-2-INTEGRATION-COMPLETE.md` |
| Sprint Plan | `SPRINT-XX-PLAN.md` | `/docs/planning/` | `SPRINT-54-PLAN.md` |
| Technical Spec | `UPPERCASE-SPEC-NAME.md` | `/docs/specs/` | `OAUTH-SETUP-GUIDE.md` |
| Project Doc | `UPPERCASE-NAME.md` | Root | `README.md`, `SECURITY.md` |
| Audit Log | `audit-YYYY-MM-DD.jsonl` | `/audit/` | `audit-2025-10-09.jsonl` |
| App Log | `<component>.jsonl` | `/logs/` | `connectors.jsonl` |
| Test File | `test_<component>_<aspect>.py` | `/tests/<category>/` | `test_google_mime_unit.py` |
| Script | `<function>.py` or `<function>.bat` | `/scripts/` | `e2e_gmail_test.py` |

---

## Quick Reference: Where to Find Things

### OAuth Setup
- **Setup Guide:** `docs/specs/OAUTH-SETUP-GUIDE.md`
- **Setup Evidence:** `docs/evidence/sprint-54/2025.10.10-PHASE-3-OAUTH-SETUP-COMPLETE.md`
- **Status:** `PHASE3_STATUS.md` (root)
- **Scripts:** `scripts/oauth/` (recommended) or `scripts/*.py` (current)
- **Server Startup:** `start_server.py`, `start_oauth_server.bat` (root, temporary)

### E2E Testing
- **Test Plan:** `docs/specs/PHASE-3-E2E-TESTING-PLAN.md` (450 lines)
- **Test Script:** `scripts/e2e_gmail_test.py`
- **Execution Status:** `docs/evidence/sprint-54/PHASE-3-EXECUTION-STATUS.md`

### Gmail Integration
- **Spec:** `docs/specs/GMAIL-RICH-EMAIL-SPEC.md`
- **Design:** `docs/specs/GMAIL-RICH-EMAIL-INTEGRATION-DESIGN.md`
- **Evidence:** `docs/evidence/sprint-54/GMAIL-RICH-EMAIL-COMPLETION.md`
- **Implementation:** `src/actions/adapters/google_mime.py`

### Rollout Infrastructure
- **Milestone:** `docs/evidence/sprint-54/MILESTONE-ROLLOUT-INFRASTRUCTURE.md`
- **Usage Guide:** `docs/evidence/sprint-54/CONTROLLER-USAGE.md`
- **Testing Checklist:** `docs/evidence/sprint-54/CONTROLLER-TESTING-CHECKLIST.md`
- **Controller:** `src/rollout/controller.py`
- **Workflow:** `.github/workflows/rollout-controller.yml`

### Observability
- **Phase C Plan:** `docs/observability/PHASE-C-OBSERVABILITY.md`
- **Metrics:** `src/telemetry/prom.py`
- **Grafana Queries:** `grafana-queries.md` (root)

---

## Maintenance Notes

This structure has evolved organically over 40+ sprints. The naming conventions are consistent and intentional:

1. **Timestamps** indicate completion milestones
2. **UPPERCASE** indicates stable, long-term documentation
3. **lowercase-with-hyphens** for specific implementation files
4. **Sprint folders** keep evidence organized and traceable

**Do not reorganize without careful consideration** - many scripts and documentation files reference these paths.

---

## Future Improvements

1. Create `scripts/archive/` for completed sprint-specific scripts
2. Consolidate temporary status files into evidence documents
3. Create automated structure validation
4. Generate this document automatically from project files
