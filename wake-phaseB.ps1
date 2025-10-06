# wake-phaseB.ps1
# Sprint 49 Phase B - Keep-Alive Script
# Keeps computer awake for 5 hours (enough for full Phase B run + buffer)
# Scheduled to run at 10:00 PM PDT (05:00 UTC Oct 6, 2025)

Write-Host "==================================" -ForegroundColor Cyan
Write-Host "Sprint 49 Phase B - Wake & Keep-Alive" -ForegroundColor Cyan
Write-Host "Start Time: $(Get-Date)" -ForegroundColor Cyan
Write-Host "Will keep system awake for 5 hours" -ForegroundColor Cyan
Write-Host "==================================" -ForegroundColor Cyan

# Prevent system from sleeping
Add-Type -AssemblyName System.Windows.Forms

# Duration: 5 hours (18000 seconds)
$endTime = (Get-Date).AddHours(5)
$iteration = 0

Write-Host "`n[$(Get-Date -Format 'HH:mm:ss')] Keep-alive loop started..." -ForegroundColor Green

# Keep system awake by simulating user activity
while ((Get-Date) -lt $endTime) {
    $iteration++

    # Send NumLock key twice (toggles on then off - invisible to user)
    [System.Windows.Forms.SendKeys]::SendWait("{NUMLOCK}{NUMLOCK}")

    # Log progress every 30 minutes
    if ($iteration % 30 -eq 0) {
        $remaining = ($endTime - (Get-Date)).ToString("hh\:mm\:ss")
        Write-Host "[$(Get-Date -Format 'HH:mm:ss')] System kept awake - Time remaining: $remaining" -ForegroundColor Yellow
    }

    # Sleep for 60 seconds between keep-alive signals
    Start-Sleep -Seconds 60
}

Write-Host "`n==================================" -ForegroundColor Cyan
Write-Host "Keep-alive completed at $(Get-Date)" -ForegroundColor Green
Write-Host "Phase B should be complete" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Cyan
