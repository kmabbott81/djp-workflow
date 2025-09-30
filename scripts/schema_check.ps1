# PowerShell schema validation script for Windows
# Runs policy tests and artifact validation

Write-Host "DJP Pipeline Schema Check" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan

$ErrorCount = 0

# Run policy tests
Write-Host "`nRunning policy tests..." -ForegroundColor Yellow
try {
    $policyResult = & python -m pytest -q tests/test_policies.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Policy tests passed" -ForegroundColor Green
    } else {
        Write-Host "✗ Policy tests failed" -ForegroundColor Red
        $ErrorCount++
        Write-Host $policyResult -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Failed to run policy tests: $($_.Exception.Message)" -ForegroundColor Red
    $ErrorCount++
}

# Run artifact validation
Write-Host "`nRunning artifact validation..." -ForegroundColor Yellow
try {
    $artifactResult = & python scripts/validate_artifacts.py
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Artifact validation passed" -ForegroundColor Green
    } else {
        Write-Host "✗ Artifact validation failed" -ForegroundColor Red
        $ErrorCount++
    }
} catch {
    Write-Host "✗ Failed to run artifact validation: $($_.Exception.Message)" -ForegroundColor Red
    $ErrorCount++
}

# Summary
if ($ErrorCount -eq 0) {
    Write-Host "`n🎉 All schema checks passed!" -ForegroundColor Green
    exit 0
} else {
    Write-Host "`n💥 $ErrorCount schema check(s) failed!" -ForegroundColor Red
    exit 1
}
