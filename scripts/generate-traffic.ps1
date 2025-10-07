#!/usr/bin/env pwsh
# Generate traffic to staging API for metrics validation
# Usage: .\scripts\generate-traffic.ps1 -Count 100 -Interval 2

param(
    [int]$Count = 50,
    [int]$Interval = 2,
    [string]$BaseUrl = "https://relay-production-f2a6.up.railway.app"
)

Write-Host "Generating $Count requests to $BaseUrl with ${Interval}s interval..." -ForegroundColor Cyan

$endpoints = @(
    "/_stcore/health",
    "/api/templates",
    "/metrics"
)

for ($i = 1; $i -le $Count; $i++) {
    $endpoint = $endpoints[$i % $endpoints.Length]
    $url = "$BaseUrl$endpoint"

    try {
        $response = Invoke-WebRequest -Uri $url -Method GET -TimeoutSec 10 -UseBasicParsing
        $statusCode = $response.StatusCode
        Write-Host "[${i}/${Count}] $endpoint - $statusCode" -ForegroundColor Green
    }
    catch {
        Write-Host "[${i}/${Count}] $endpoint - ERROR: $($_.Exception.Message)" -ForegroundColor Red
    }

    if ($i -lt $Count) {
        Start-Sleep -Seconds $Interval
    }
}

Write-Host "`nTraffic generation complete. Check Prometheus/Grafana for updated metrics." -ForegroundColor Cyan
