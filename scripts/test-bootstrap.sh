#!/bin/bash
# Test script for bootstrap.py
# Demonstrates various usage patterns on Unix-like systems

set -e  # Exit on error

echo "========================================"
echo "Bootstrap Script Test Suite"
echo "========================================"
echo ""

# Test 1: Using CLI flags
echo "Test 1: Using CLI flags"
python scripts/bootstrap.py --user "test-cli@example.com" --tenant "test-cli-tenant"
echo ""

# Test 2: Using environment variables
echo "Test 2: Using environment variables"
export BOOTSTRAP_ADMIN_USER="test-env@example.com"
export BOOTSTRAP_TENANT="test-env-tenant"
python scripts/bootstrap.py
echo ""

# Test 3: CLI flags override environment
echo "Test 3: CLI flags override environment"
export BOOTSTRAP_ADMIN_USER="wrong@example.com"
export BOOTSTRAP_TENANT="wrong-tenant"
python scripts/bootstrap.py --user "override@example.com" --tenant "override-tenant"
echo ""

# Test 4: Dry run mode
echo "Test 4: Dry run mode"
python scripts/bootstrap.py --user "dryrun@example.com" --tenant "dryrun-tenant" --dry-run
echo ""

# Test 5: Idempotency (re-run with same params)
echo "Test 5: Idempotency test"
python scripts/bootstrap.py --user "idempotent@example.com" --tenant "idempotent-tenant"
echo "Re-running with same parameters..."
python scripts/bootstrap.py --user "idempotent@example.com" --tenant "idempotent-tenant"
echo ""

# Test 6: Missing parameters (should fail)
echo "Test 6: Error handling (missing parameters)"
unset BOOTSTRAP_ADMIN_USER
unset BOOTSTRAP_TENANT
python scripts/bootstrap.py 2>&1 || echo "Expected failure: missing parameters"
echo ""

echo "========================================"
echo "Test Suite Complete"
echo "========================================"
