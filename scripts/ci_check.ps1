# PowerShell CI/CD Check Script for DJP Pipeline
# Runs all validation checks required for CI/CD pipeline

$ErrorActionPreference = "Stop"
$exit_code = 0

Write-Host "DJP Pipeline CI/CD Validation" -ForegroundColor Cyan
Write-Host "=============================" -ForegroundColor Cyan

# Test 1: Policy tests
Write-Host ""
Write-Host "Running policy tests..." -ForegroundColor Yellow
try {
    $result = python -m pytest tests/test_policies.py -q
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Policy tests passed" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Policy tests failed" -ForegroundColor Red
        $exit_code = 1
    }
} catch {
    Write-Host "[ERROR] Failed to run policy tests: $_" -ForegroundColor Red
    $exit_code = 1
}

# Test 2: Schema validation
Write-Host ""
Write-Host "Running schema validation..." -ForegroundColor Yellow
try {
    $result = python scripts/validate_artifacts.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Schema validation passed" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Schema validation failed" -ForegroundColor Red
        $exit_code = 1
    }
} catch {
    Write-Host "[ERROR] Failed to run schema validation: $_" -ForegroundColor Red
    $exit_code = 1
}

# Test 3: Guardrails tests
Write-Host ""
Write-Host "Running guardrails tests..." -ForegroundColor Yellow
try {
    $result = python -m pytest tests/test_guardrails.py -q
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Guardrails tests passed" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Guardrails tests failed" -ForegroundColor Red
        $exit_code = 1
    }
} catch {
    Write-Host "[ERROR] Failed to run guardrails tests: $_" -ForegroundColor Red
    $exit_code = 1
}

# Test 4: Performance smoke tests
Write-Host ""
Write-Host "Running performance smoke tests..." -ForegroundColor Yellow
try {
    $result = python -m pytest tests/test_perf_smoke.py -q
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Performance smoke tests passed" -ForegroundColor Green
    } else {
        Write-Host "[ERROR] Performance smoke tests failed" -ForegroundColor Red
        $exit_code = 1
    }
} catch {
    Write-Host "[ERROR] Failed to run performance smoke tests: $_" -ForegroundColor Red
    $exit_code = 1
}

# Summary
Write-Host ""
Write-Host "=============================" -ForegroundColor Cyan
if ($exit_code -eq 0) {
    Write-Host "[SUCCESS] All CI checks passed!" -ForegroundColor Green
} else {
    Write-Host "[FAILED] CI checks failed!" -ForegroundColor Red
}

exit $exit_code
