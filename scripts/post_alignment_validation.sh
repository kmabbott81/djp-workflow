#!/bin/bash
###############################################################################
# Post-Alignment Validation Script
#
# Purpose: Validate platform readiness after audit-driven alignment sprints
# Usage: ./scripts/post_alignment_validation.sh
# Exit Codes:
#   0 - All validations passed
#   1 - One or more validations failed
#
# Sprint 52 – Agent Orchestration (Phase 3)
# Date: October 7, 2025
###############################################################################

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Validation counters
PASSED=0
FAILED=0
WARNINGS=0

# Configuration (override with environment variables)
BACKEND_URL="${BACKEND_URL:-http://localhost:8000}"
PROMETHEUS_URL="${PROMETHEUS_URL:-http://localhost:9090}"
GRAFANA_URL="${GRAFANA_URL:-http://localhost:3000}"
GRAFANA_API_KEY="${GRAFANA_API_KEY:-}"

###############################################################################
# Helper Functions
###############################################################################

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
    ((WARNINGS++))
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
    ((FAILED++))
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
    ((PASSED++))
}

check_command() {
    if ! command -v "$1" &> /dev/null; then
        log_error "Required command '$1' not found. Please install it."
        return 1
    fi
    return 0
}

###############################################################################
# Pre-Flight Checks
###############################################################################

pre_flight_checks() {
    log_info "=== Pre-Flight Checks ==="

    # Check required commands
    check_command "curl" || exit 1
    check_command "jq" || log_warn "jq not found - some checks will be skipped"
    check_command "git" || log_warn "git not found - version checks will be skipped"

    # Check if backend is reachable
    if curl -sf "$BACKEND_URL/health" > /dev/null 2>&1; then
        log_success "Backend is reachable at $BACKEND_URL"
    else
        log_error "Backend is not reachable at $BACKEND_URL"
    fi

    echo ""
}

###############################################################################
# Part 1: Codebase Health
###############################################################################

validate_codebase() {
    log_info "=== Part 1: Codebase Health ==="

    # Check git status (should have no uncommitted changes for release)
    if command -v git &> /dev/null; then
        UNCOMMITTED=$(git status --porcelain | wc -l)
        if [ "$UNCOMMITTED" -eq 0 ]; then
            log_success "No uncommitted changes (clean working directory)"
        else
            log_warn "Found $UNCOMMITTED uncommitted changes"
        fi

        # Check current branch
        CURRENT_BRANCH=$(git branch --show-current)
        log_info "Current branch: $CURRENT_BRANCH"

        # Check for unmerged branches (example: sprint/* should eventually merge to main)
        UNMERGED=$(git branch --no-merged main 2>/dev/null | grep -c "sprint/" || echo "0")
        if [ "$UNMERGED" -gt 0 ]; then
            log_warn "Found $UNMERGED unmerged sprint branches"
        else
            log_success "No unmerged sprint branches"
        fi
    fi

    # Check for critical documentation files
    REQUIRED_DOCS=(
        "README.md"
        "docs/observability/SLOs.md"
        "docs/review/PR-AUDIT-CLOSURE-CHECKLIST.md"
        "docs/alignment/ROADMAP-ALIGNMENT-SUMMARY.md"
        "docs/templates/QUARTERLY-AUDIT-TEMPLATE.md"
    )

    for doc in "${REQUIRED_DOCS[@]}"; do
        if [ -f "$doc" ]; then
            log_success "Documentation exists: $doc"
        else
            log_error "Missing documentation: $doc"
        fi
    done

    echo ""
}

###############################################################################
# Part 2: Security Posture
###############################################################################

validate_security() {
    log_info "=== Part 2: Security Posture ==="

    # Check security headers
    log_info "Checking security headers..."

    HEADERS=$(curl -sI "$BACKEND_URL/" 2>/dev/null || echo "")

    if echo "$HEADERS" | grep -qi "Strict-Transport-Security"; then
        log_success "HSTS header present"
    else
        log_error "HSTS header missing"
    fi

    if echo "$HEADERS" | grep -qi "Content-Security-Policy"; then
        log_success "CSP header present"
    else
        log_error "CSP header missing"
    fi

    if echo "$HEADERS" | grep -qi "Referrer-Policy"; then
        log_success "Referrer-Policy header present"
    else
        log_error "Referrer-Policy header missing"
    fi

    if echo "$HEADERS" | grep -qi "X-Content-Type-Options"; then
        log_success "X-Content-Type-Options header present"
    else
        log_error "X-Content-Type-Options header missing"
    fi

    # Check for exposed secrets in codebase (basic scan)
    log_info "Scanning for exposed secrets..."

    if command -v rg &> /dev/null; then
        SECRET_MATCHES=$(rg -i "password\s*=\s*['\"]|api_key\s*=\s*['\"]|secret\s*=\s*['\"]" src/ 2>/dev/null | grep -v "# noqa" | wc -l || echo "0")
        if [ "$SECRET_MATCHES" -eq 0 ]; then
            log_success "No hardcoded secrets found (basic scan)"
        else
            log_error "Found $SECRET_MATCHES potential hardcoded secrets"
        fi
    else
        log_warn "ripgrep (rg) not found - skipping secret scan"
    fi

    # Check .gitignore for sensitive files
    if grep -q "^\.env$" .gitignore 2>/dev/null; then
        log_success ".env is in .gitignore"
    else
        log_error ".env is NOT in .gitignore"
    fi

    if grep -q "^\*\.key$" .gitignore 2>/dev/null; then
        log_success "*.key is in .gitignore"
    else
        log_warn "*.key is NOT in .gitignore"
    fi

    echo ""
}

###############################################################################
# Part 3: Operational Readiness
###############################################################################

validate_operations() {
    log_info "=== Part 3: Operational Readiness ==="

    # Check health endpoint
    log_info "Checking /health endpoint..."

    HEALTH_RESPONSE=$(curl -sf "$BACKEND_URL/health" 2>/dev/null || echo "{}")

    if echo "$HEALTH_RESPONSE" | grep -q "healthy"; then
        log_success "Health endpoint returns healthy status"
    else
        log_error "Health endpoint did not return healthy status"
    fi

    # Check metrics endpoint
    log_info "Checking /metrics endpoint..."

    METRICS_RESPONSE=$(curl -sf "$BACKEND_URL/metrics" 2>/dev/null || echo "")

    if echo "$METRICS_RESPONSE" | grep -q "http_requests_total"; then
        log_success "Metrics endpoint exposes http_requests_total"
    else
        log_error "Metrics endpoint does not expose http_requests_total"
    fi

    if echo "$METRICS_RESPONSE" | grep -q "http_request_duration_seconds"; then
        log_success "Metrics endpoint exposes http_request_duration_seconds"
    else
        log_error "Metrics endpoint does not expose http_request_duration_seconds"
    fi

    # Check CI/CD workflow files
    log_info "Checking CI/CD workflow files..."

    if [ -f ".github/workflows/deploy.yml" ]; then
        log_success "Deployment workflow exists"
    else
        log_error "Deployment workflow missing"
    fi

    if [ -f ".github/workflows/backup.yml" ]; then
        log_success "Backup workflow exists"
    else
        log_error "Backup workflow missing"
    fi

    # Check for rollback script
    if [ -f "scripts/rollback_release.py" ]; then
        log_success "Rollback script exists"
    else
        log_error "Rollback script missing"
    fi

    echo ""
}

###############################################################################
# Part 4: Observability Stack
###############################################################################

validate_observability() {
    log_info "=== Part 4: Observability Stack ==="

    # Check SLO documentation
    if [ -f "docs/observability/SLOs.md" ]; then
        SLO_COUNT=$(grep -c "^### SLO" docs/observability/SLOs.md || echo "0")
        if [ "$SLO_COUNT" -ge 4 ]; then
            log_success "Found $SLO_COUNT SLOs defined (expected ≥4)"
        else
            log_error "Found only $SLO_COUNT SLOs (expected ≥4)"
        fi
    else
        log_error "SLO documentation missing"
    fi

    # Check alert rules file
    if [ -f "observability/dashboards/alerts.json" ]; then
        if command -v jq &> /dev/null; then
            ALERT_COUNT=$(jq -r '.alerts | length' observability/dashboards/alerts.json 2>/dev/null || echo "0")
            if [ "$ALERT_COUNT" -ge 8 ]; then
                log_success "Found $ALERT_COUNT alerts defined (expected ≥8)"
            else
                log_error "Found only $ALERT_COUNT alerts (expected ≥8)"
            fi
        else
            log_warn "jq not found - skipping alert count validation"
        fi
    else
        log_error "Alert rules file missing"
    fi

    # Check Grafana dashboard file
    if [ -f "observability/dashboards/golden-signals.json" ]; then
        if command -v jq &> /dev/null; then
            PANEL_COUNT=$(jq -r '.dashboard.panels | length' observability/dashboards/golden-signals.json 2>/dev/null || echo "0")
            if [ "$PANEL_COUNT" -ge 8 ]; then
                log_success "Found $PANEL_COUNT dashboard panels (expected ≥8)"
            else
                log_error "Found only $PANEL_COUNT panels (expected ≥8)"
            fi
        fi
    else
        log_error "Grafana dashboard file missing"
    fi

    # Check Prometheus connectivity (if URL provided)
    if [ -n "$PROMETHEUS_URL" ] && [ "$PROMETHEUS_URL" != "http://localhost:9090" ]; then
        log_info "Checking Prometheus connectivity..."

        if curl -sf "$PROMETHEUS_URL/-/healthy" > /dev/null 2>&1; then
            log_success "Prometheus is reachable at $PROMETHEUS_URL"

            # Check if backend metrics are being scraped
            if command -v jq &> /dev/null; then
                UP_STATUS=$(curl -sf "$PROMETHEUS_URL/api/v1/query?query=up{job=\"relay-backend\"}" 2>/dev/null | jq -r '.data.result[0].value[1]' || echo "0")
                if [ "$UP_STATUS" = "1" ]; then
                    log_success "Prometheus is scraping backend metrics"
                else
                    log_error "Prometheus is NOT scraping backend metrics (up=0)"
                fi
            fi
        else
            log_warn "Prometheus is not reachable at $PROMETHEUS_URL (may not be deployed yet)"
        fi
    else
        log_warn "Prometheus URL not provided - skipping connectivity check"
    fi

    # Check Grafana connectivity (if API key provided)
    if [ -n "$GRAFANA_API_KEY" ] && [ -n "$GRAFANA_URL" ]; then
        log_info "Checking Grafana connectivity..."

        if curl -sf -H "Authorization: Bearer $GRAFANA_API_KEY" "$GRAFANA_URL/api/health" > /dev/null 2>&1; then
            log_success "Grafana is reachable at $GRAFANA_URL"

            # Check if dashboard exists
            if command -v jq &> /dev/null; then
                DASHBOARD_COUNT=$(curl -sf -H "Authorization: Bearer $GRAFANA_API_KEY" "$GRAFANA_URL/api/search?query=Relay" 2>/dev/null | jq -r '. | length' || echo "0")
                if [ "$DASHBOARD_COUNT" -gt 0 ]; then
                    log_success "Found $DASHBOARD_COUNT Relay dashboard(s) in Grafana"
                else
                    log_warn "No Relay dashboards found in Grafana (may not be imported yet)"
                fi
            fi
        else
            log_warn "Grafana is not reachable at $GRAFANA_URL (may not be deployed yet)"
        fi
    else
        log_warn "Grafana API key not provided - skipping connectivity check"
    fi

    echo ""
}

###############################################################################
# Part 5: Test Coverage
###############################################################################

validate_tests() {
    log_info "=== Part 5: Test Coverage ==="

    # Check if pytest is available
    if command -v pytest &> /dev/null; then
        log_info "Running unit tests..."

        # Run pytest with coverage
        if pytest --cov=src --cov-report=term-missing tests/ > /tmp/pytest-output.txt 2>&1; then
            PASSED_TESTS=$(grep -oP '\d+(?= passed)' /tmp/pytest-output.txt || echo "0")
            FAILED_TESTS=$(grep -oP '\d+(?= failed)' /tmp/pytest-output.txt || echo "0")
            COVERAGE=$(grep -oP '\d+(?=%)' /tmp/pytest-output.txt | tail -1 || echo "0")

            log_success "$PASSED_TESTS tests passed"

            if [ "$FAILED_TESTS" -gt 0 ]; then
                log_error "$FAILED_TESTS tests failed"
            fi

            if [ "$COVERAGE" -ge 80 ]; then
                log_success "Test coverage: $COVERAGE% (≥80%)"
            else
                log_warn "Test coverage: $COVERAGE% (<80%)"
            fi
        else
            log_error "Tests failed to run (see /tmp/pytest-output.txt for details)"
        fi
    else
        log_warn "pytest not found - skipping test execution"
    fi

    echo ""
}

###############################################################################
# Part 6: Database Validation
###############################################################################

validate_database() {
    log_info "=== Part 6: Database Validation ==="

    # Check if database connection is healthy (via health endpoint)
    if curl -sf "$BACKEND_URL/health" 2>/dev/null | grep -q "database.*connected"; then
        log_success "Database connection is healthy"
    else
        log_error "Database connection is NOT healthy"
    fi

    # Check for backup scripts
    if [ -f "scripts/db_restore_check.py" ]; then
        log_success "Database restore validation script exists"
    else
        log_error "Database restore validation script missing"
    fi

    # Check for migration files
    if [ -d "migrations" ]; then
        MIGRATION_COUNT=$(find migrations -name "*.sql" -o -name "*.py" | wc -l || echo "0")
        if [ "$MIGRATION_COUNT" -gt 0 ]; then
            log_success "Found $MIGRATION_COUNT migration files"
        else
            log_warn "No migration files found (may use ORM auto-migrations)"
        fi
    else
        log_warn "migrations/ directory not found"
    fi

    echo ""
}

###############################################################################
# Summary & Exit
###############################################################################

print_summary() {
    echo ""
    log_info "=== Validation Summary ==="
    echo ""
    echo -e "${GREEN}Passed:${NC}   $PASSED"
    echo -e "${RED}Failed:${NC}   $FAILED"
    echo -e "${YELLOW}Warnings:${NC} $WARNINGS"
    echo ""

    if [ "$FAILED" -eq 0 ]; then
        echo -e "${GREEN}✓ All critical validations passed!${NC}"
        echo ""
        echo "Platform is ready for deployment."
        return 0
    else
        echo -e "${RED}✗ $FAILED critical validation(s) failed.${NC}"
        echo ""
        echo "Please address the failures above before deploying to production."
        return 1
    fi
}

###############################################################################
# Main Execution
###############################################################################

main() {
    echo "=============================================================================="
    echo "  Post-Alignment Validation Script"
    echo "  Sprint 52 – Agent Orchestration (Phase 3)"
    echo "=============================================================================="
    echo ""

    pre_flight_checks
    validate_codebase
    validate_security
    validate_operations
    validate_observability
    validate_tests
    validate_database

    print_summary

    return $?
}

# Run main and exit with its exit code
main
exit $?
