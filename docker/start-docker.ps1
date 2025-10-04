# DJP Workflow Platform - Docker Quick Start Script (PowerShell)
# Launches the complete Docker stack with health checks

param(
    [switch]$Background,
    [switch]$Build,
    [int]$Workers = 1,
    [switch]$Clean,
    [switch]$Help
)

$ErrorActionPreference = "Stop"

# Script configuration
$ComposeFile = "docker-compose.yml"
$EnvFile = "../.env"
$EnvExample = ".env.example"

function Show-Help {
    Write-Host "DJP Workflow Platform - Docker Quick Start" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Usage: .\start-docker.ps1 [options]"
    Write-Host ""
    Write-Host "Options:"
    Write-Host "  -Background   Start services in background (detached mode)"
    Write-Host "  -Build        Build images before starting"
    Write-Host "  -Workers N    Number of worker instances (default: 1)"
    Write-Host "  -Clean        Clean up containers and volumes before starting"
    Write-Host "  -Help         Show this help message"
    Write-Host ""
    Write-Host "Examples:"
    Write-Host "  .\start-docker.ps1                    # Start in foreground"
    Write-Host "  .\start-docker.ps1 -Background        # Start in background"
    Write-Host "  .\start-docker.ps1 -Build -Workers 3  # Build and start with 3 workers"
    Write-Host "  .\start-docker.ps1 -Clean -Build      # Clean rebuild"
    Write-Host ""
}

function Test-Prerequisites {
    Write-Host "Checking prerequisites..." -ForegroundColor Yellow

    # Check Docker
    try {
        $dockerVersion = docker --version
        Write-Host "✓ Docker found: $dockerVersion" -ForegroundColor Green
    } catch {
        Write-Host "✗ Docker not found. Please install Docker Desktop." -ForegroundColor Red
        exit 1
    }

    # Check Docker Compose
    try {
        $composeVersion = docker-compose --version
        Write-Host "✓ Docker Compose found: $composeVersion" -ForegroundColor Green
    } catch {
        Write-Host "✗ Docker Compose not found. Please install Docker Compose." -ForegroundColor Red
        exit 1
    }

    # Check Docker is running
    try {
        docker ps | Out-Null
        Write-Host "✓ Docker daemon is running" -ForegroundColor Green
    } catch {
        Write-Host "✗ Docker daemon is not running. Please start Docker Desktop." -ForegroundColor Red
        exit 1
    }
}

function Test-EnvironmentFile {
    if (-not (Test-Path $EnvFile)) {
        Write-Host ""
        Write-Host "Warning: .env file not found at $EnvFile" -ForegroundColor Yellow
        Write-Host ""

        if (Test-Path $EnvExample) {
            $response = Read-Host "Copy from .env.example? (y/n)"
            if ($response -eq "y") {
                Copy-Item $EnvExample $EnvFile
                Write-Host "✓ Created .env from template" -ForegroundColor Green
                Write-Host ""
                Write-Host "IMPORTANT: Edit $EnvFile and add your API keys!" -ForegroundColor Red
                Write-Host ""
                $continue = Read-Host "Continue anyway? (y/n)"
                if ($continue -ne "y") {
                    exit 0
                }
            }
        } else {
            Write-Host "Error: $EnvExample not found either!" -ForegroundColor Red
            exit 1
        }
    } else {
        Write-Host "✓ Environment file found: $EnvFile" -ForegroundColor Green
    }
}

function Invoke-CleanUp {
    Write-Host ""
    Write-Host "Cleaning up existing containers and volumes..." -ForegroundColor Yellow
    docker-compose -f $ComposeFile down -v
    Write-Host "✓ Cleanup complete" -ForegroundColor Green
}

function Invoke-Build {
    Write-Host ""
    Write-Host "Building Docker images..." -ForegroundColor Yellow
    docker-compose -f $ComposeFile build
    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Build failed!" -ForegroundColor Red
        exit 1
    }
    Write-Host "✓ Build complete" -ForegroundColor Green
}

function Start-Services {
    param([bool]$Detached, [int]$NumWorkers)

    Write-Host ""
    Write-Host "Starting DJP Workflow Platform..." -ForegroundColor Yellow
    Write-Host "  Workers: $NumWorkers" -ForegroundColor Cyan
    Write-Host "  Mode: $(if ($Detached) { 'Background' } else { 'Foreground' })" -ForegroundColor Cyan
    Write-Host ""

    $scaleArg = "--scale worker=$NumWorkers"

    if ($Detached) {
        docker-compose -f $ComposeFile up -d $scaleArg.Split()
    } else {
        docker-compose -f $ComposeFile up $scaleArg.Split()
    }

    if ($LASTEXITCODE -ne 0) {
        Write-Host "✗ Failed to start services!" -ForegroundColor Red
        exit 1
    }

    if ($Detached) {
        Write-Host ""
        Write-Host "✓ Services started successfully!" -ForegroundColor Green
        Write-Host ""
        Write-Host "Access points:" -ForegroundColor Cyan
        Write-Host "  Dashboard:    http://localhost:8501" -ForegroundColor White
        Write-Host "  Health Check: http://localhost:8080/ready" -ForegroundColor White
        Write-Host "  Redis:        localhost:6379" -ForegroundColor White
        Write-Host ""
        Write-Host "Useful commands:" -ForegroundColor Cyan
        Write-Host "  docker-compose -f $ComposeFile logs -f      # View logs"
        Write-Host "  docker-compose -f $ComposeFile ps           # Service status"
        Write-Host "  docker-compose -f $ComposeFile down         # Stop services"
        Write-Host ""

        # Wait a moment and check health
        Write-Host "Checking service health in 5 seconds..." -ForegroundColor Yellow
        Start-Sleep -Seconds 5

        try {
            $health = Invoke-RestMethod -Uri "http://localhost:8080/health" -TimeoutSec 5
            Write-Host "✓ App health check passed" -ForegroundColor Green
        } catch {
            Write-Host "⚠ App health check failed (may still be starting)" -ForegroundColor Yellow
        }

        Write-Host ""
        Write-Host "View service status:" -ForegroundColor Cyan
        docker-compose -f $ComposeFile ps
    }
}

# Main script execution
if ($Help) {
    Show-Help
    exit 0
}

Write-Host ""
Write-Host "╔═══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║   DJP Workflow Platform - Docker Launcher    ║" -ForegroundColor Cyan
Write-Host "╚═══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

# Run checks
Test-Prerequisites
Test-EnvironmentFile

# Clean if requested
if ($Clean) {
    Invoke-CleanUp
}

# Build if requested
if ($Build) {
    Invoke-Build
}

# Start services
Start-Services -Detached $Background -NumWorkers $Workers

Write-Host ""
Write-Host "Done! 🚀" -ForegroundColor Green
Write-Host ""
