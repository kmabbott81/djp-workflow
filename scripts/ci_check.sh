#!/bin/bash
# Bash CI/CD Check Script for DJP Pipeline
# Runs all validation checks required for CI/CD pipeline

set -e
exit_code=0

echo "DJP Pipeline CI/CD Validation"
echo "============================="

# Test 1: Policy tests
echo ""
echo "Running policy tests..."
if python -m pytest tests/test_policies.py -q; then
    echo "[OK] Policy tests passed"
else
    echo "[ERROR] Policy tests failed"
    exit_code=1
fi

# Test 2: Schema validation
echo ""
echo "Running schema validation..."
if python scripts/validate_artifacts.py; then
    echo "[OK] Schema validation passed"
else
    echo "[ERROR] Schema validation failed"
    exit_code=1
fi

# Test 3: Guardrails tests
echo ""
echo "Running guardrails tests..."
if python -m pytest tests/test_guardrails.py -q; then
    echo "[OK] Guardrails tests passed"
else
    echo "[ERROR] Guardrails tests failed"
    exit_code=1
fi

# Test 4: Performance smoke tests
echo ""
echo "Running performance smoke tests..."
if python -m pytest tests/test_perf_smoke.py -q; then
    echo "[OK] Performance smoke tests passed"
else
    echo "[ERROR] Performance smoke tests failed"
    exit_code=1
fi

# Summary
echo ""
echo "============================="
if [ $exit_code -eq 0 ]; then
    echo "[SUCCESS] All CI checks passed!"
else
    echo "[FAILED] CI checks failed!"
fi

exit $exit_code
