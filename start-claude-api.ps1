# start-claude-api.ps1
# Purpose: Launch Claude Code in API-key mode reliably on Windows.
# - Loads .env (ANTHROPIC_API_KEY=...)
# - Mirrors to CLAUDE_API_KEY for builds that expect that name
# - Clears any stale OAuth session
# - Starts `claude` so it uses the API key (no subscription login)

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
      $v = $matches[2].Trim()
      [System.Environment]::SetEnvironmentVariable($k, $v, "Process")
    }
  }
}

# 1) Go to repo where .env lives (so tools inherit the same working dir)
Set-Location $Repo

# 2) Load .env into THIS shell
Load-DotEnv ".\.env"

# 3) Ensure ANTHROPIC_API_KEY exists and looks sane
if (-not $env:ANTHROPIC_API_KEY) { throw "ANTHROPIC_API_KEY missing in this shell." }
$env:ANTHROPIC_API_KEY = $env:ANTHROPIC_API_KEY.Trim()

# 4) Mirror to CLAUDE_API_KEY for compatibility (some builds look for this)
$env:CLAUDE_API_KEY = $env:ANTHROPIC_API_KEY

# 5) Clear any lingering OAuth state (ignore errors if not logged in)
try { claude logout | Out-Null } catch {}

# 6) Launch Claude Code (it should detect the API key and NOT open a browser)
claude
