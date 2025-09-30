# start-codex-api.ps1
# Purpose: Launch OpenAI Codex CLI in API mode reliably on Windows.
# - Loads .env from your repo (OPENAI_API_KEY=...)
# - Trims hidden whitespace
# - Auto-detects and exports OPENAI_PROJECT from /v1/me
# - Starts Codex fresh so it binds to your API project (no ChatGPT OAuth)

param(
  [string]$Repo = "C:\Users\kylem\openai-agents-workflows-2025.09.28-v1"
)

$ErrorActionPreference = "Stop"

function Load-DotEnv([string]$envFile) {
  if (-not (Test-Path $envFile)) {
    throw ".env not found at $envFile"
  }
  Get-Content $envFile | ForEach-Object {
    if ($_ -match "^(.*?)=(.*)$") {
      $k = $matches[1].Trim()
      $v = $matches[2].Trim()  # trim hidden newline/space
      [System.Environment]::SetEnvironmentVariable($k, $v, "Process")
    }
  }
}

# 1) Go to repo where .env lives
Set-Location $Repo

# 2) Load .env into THIS shell
Load-DotEnv ".\.env"

# 3) Ensure OPENAI_API_KEY exists and looks sane
if (-not $env:OPENAI_API_KEY) { throw "OPENAI_API_KEY missing in this shell." }
$env:OPENAI_API_KEY = $env:OPENAI_API_KEY.Trim()
if ($env:OPENAI_API_KEY -notmatch '^sk-[a-z0-9_\-]+') {
  Write-Warning "OPENAI_API_KEY format looks unusual. Continuing anyway..."
}

# 4) Fetch project id from /v1/me and export OPENAI_PROJECT (if not already set)
try {
  if (-not $env:OPENAI_PROJECT) {
    $headers = @{ "Authorization" = "Bearer $($env:OPENAI_API_KEY)" }
    $me = Invoke-RestMethod -Headers $headers -Uri "https://api.openai.com/v1/me"
    if ($me.project.id) {
      $env:OPENAI_PROJECT = $me.project.id
    }
  }
} catch {
  Write-Warning "Could not fetch project id from /v1/me. Codex may still work without OPENAI_PROJECT."
}

# 5) Start Codex clean (clear any old login state)
try { codex logout | Out-Null } catch { }

# 6) Launch Codex (inherits env from this shell)
codex
