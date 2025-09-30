# create-dev-env.ps1
# Creates a local .env file for Claude Code, Codex CLI, and Aider

$repoPath = "C:\Users\kylem\openai-agents-workflows-2025.09.28-v1"
$envFile  = Join-Path $repoPath ".env"

$lines = @"
# ======================================
# Local API keys for developer agents
# Use only with Claude Code, Codex CLI, and Aider
# Do NOT commit this file to Git
# ======================================

# OpenAI key for Codex CLI + Aider
OPENAI_API_KEY=sk-openai-PASTE-YOUR-KEY-HERE

# Anthropic key for Claude Code
ANTHROPIC_API_KEY=sk-ant-PASTE-YOUR-KEY-HERE

# (Optional) Google key if you want Gemini debate support
GOOGLE_API_KEY=AIza-PASTE-YOUR-KEY-HERE

# (Optional) AWS Bedrock if you add Amazon Nova/Titan later
AWS_ACCESS_KEY_ID=PASTE-HERE
AWS_SECRET_ACCESS_KEY=PASTE-HERE
AWS_REGION=us-west-2
"@

Set-Content -Path $envFile -Value $lines -Encoding UTF8

Write-Host "Created .env at $envFile. Paste your keys in and save."
