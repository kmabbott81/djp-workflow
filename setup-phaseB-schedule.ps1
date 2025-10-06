# setup-phaseB-schedule.ps1
# Run this script AS ADMINISTRATOR to schedule Phase B wake task
# Right-click → Run as Administrator

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Sprint 49 Phase B - Schedule Setup" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# Check if running as administrator
$isAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)

if (-not $isAdmin) {
    Write-Host "`nERROR: This script must be run as Administrator!" -ForegroundColor Red
    Write-Host "Right-click this script and select 'Run as Administrator'" -ForegroundColor Yellow
    pause
    exit 1
}

Write-Host "`n[OK] Running as Administrator" -ForegroundColor Green

$scriptPath = "C:\Users\kylem\openai-agents-workflows-2025.09.28-v1\wake-phaseB.ps1"

# Verify script exists
if (-not (Test-Path $scriptPath)) {
    Write-Host "`nERROR: wake-phaseB.ps1 not found at: $scriptPath" -ForegroundColor Red
    pause
    exit 1
}

Write-Host "[OK] Found wake-phaseB.ps1" -ForegroundColor Green

# Delete existing task if present
schtasks /Delete /TN "RelayPhaseBWake" /F 2>$null | Out-Null

# Create scheduled task
Write-Host "`nCreating scheduled task..." -ForegroundColor Yellow

$taskResult = schtasks /Create /TN "RelayPhaseBWake" `
    /TR "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -File `"$scriptPath`"" `
    /SC ONCE `
    /ST 22:00 `
    /SD 10/05/2025 `
    /RU "$env:USERNAME" `
    /RL HIGHEST `
    /F

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n[SUCCESS] Scheduled task created!" -ForegroundColor Green
    Write-Host "`nTask Details:" -ForegroundColor Cyan
    Write-Host "  Name: RelayPhaseBWake" -ForegroundColor White
    Write-Host "  Trigger: Tonight at 10:00 PM (October 5, 2025)" -ForegroundColor White
    Write-Host "  Duration: 5 hours (keeps system awake)" -ForegroundColor White
    Write-Host "  Script: $scriptPath" -ForegroundColor White

    Write-Host "`nVerifying task..." -ForegroundColor Yellow
    schtasks /Query /TN "RelayPhaseBWake" /FO LIST /V | Select-String -Pattern "(Task Name|Next Run Time|Status)"

    Write-Host "`n==================================" -ForegroundColor Green
    Write-Host "Setup Complete!" -ForegroundColor Green
    Write-Host "==================================" -ForegroundColor Green
    Write-Host "`nYour computer will:" -ForegroundColor Yellow
    Write-Host "1. Wake at 10:00 PM tonight" -ForegroundColor White
    Write-Host "2. Stay awake for 5 hours" -ForegroundColor White
    Write-Host "3. Allow Phase B to execute uninterrupted" -ForegroundColor White
    Write-Host "`nYou can close this window now." -ForegroundColor Cyan
} else {
    Write-Host "`n[ERROR] Failed to create scheduled task" -ForegroundColor Red
    Write-Host "Error code: $LASTEXITCODE" -ForegroundColor Red
}

pause
