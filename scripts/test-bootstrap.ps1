# Test script for bootstrap.py
# Demonstrates various usage patterns

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Bootstrap Script Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Test 1: Using CLI flags
Write-Host "Test 1: Using CLI flags" -ForegroundColor Yellow
python scripts/bootstrap.py --user "test-cli@example.com" --tenant "test-cli-tenant"
Write-Host ""

# Test 2: Using environment variables
Write-Host "Test 2: Using environment variables" -ForegroundColor Yellow
$env:BOOTSTRAP_ADMIN_USER = "test-env@example.com"
$env:BOOTSTRAP_TENANT = "test-env-tenant"
python scripts/bootstrap.py
Write-Host ""

# Test 3: CLI flags override environment
Write-Host "Test 3: CLI flags override environment" -ForegroundColor Yellow
$env:BOOTSTRAP_ADMIN_USER = "wrong@example.com"
$env:BOOTSTRAP_TENANT = "wrong-tenant"
python scripts/bootstrap.py --user "override@example.com" --tenant "override-tenant"
Write-Host ""

# Test 4: Dry run mode
Write-Host "Test 4: Dry run mode" -ForegroundColor Yellow
python scripts/bootstrap.py --user "dryrun@example.com" --tenant "dryrun-tenant" --dry-run
Write-Host ""

# Test 5: Idempotency (re-run with same params)
Write-Host "Test 5: Idempotency test" -ForegroundColor Yellow
python scripts/bootstrap.py --user "idempotent@example.com" --tenant "idempotent-tenant"
Write-Host "Re-running with same parameters..." -ForegroundColor Gray
python scripts/bootstrap.py --user "idempotent@example.com" --tenant "idempotent-tenant"
Write-Host ""

# Test 6: Missing parameters
Write-Host "Test 6: Error handling (missing parameters)" -ForegroundColor Yellow
Remove-Item env:BOOTSTRAP_ADMIN_USER -ErrorAction SilentlyContinue
Remove-Item env:BOOTSTRAP_TENANT -ErrorAction SilentlyContinue
python scripts/bootstrap.py 2>&1
Write-Host ""

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Test Suite Complete" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
