@echo off
REM Start OAuth server with environment variables

cd /d "C:\Users\kylem\openai-agents-workflows-2025.09.28-v1"

REM Set environment variables
set ACTIONS_ENABLED=true
set TELEMETRY_ENABLED=true
set PROVIDER_GOOGLE_ENABLED=true
set GOOGLE_CLIENT_ID=70455570373-o3l12k6gdokvpr87l66hh6jh7bvqpnbo.apps.googleusercontent.com
set GOOGLE_CLIENT_SECRET=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
set DATABASE_URL=postgresql://postgres:dw33GA0E7c!E8!imSJJW^xrz@switchyard.proxy.rlwy.net:39963/railway
set REDIS_URL=redis://default:zhtagqDujRcWQzETQOgHYLYYtiVduGTe@crossover.proxy.rlwy.net:22070
set OAUTH_ENCRYPTION_KEY=Mvwr_5P4VoevQaR7WcNUom56zII1QuECnErU0PfBSSE=

echo Starting OAuth server on http://localhost:8003...
echo.
echo Visit: http://localhost:8003/oauth/google/authorize?workspace_id=test-workspace-e2e
echo.

python -m uvicorn src.webapi:app --port 8003 --reload
