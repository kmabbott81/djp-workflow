# Start the NightShift Runner
# Edit the paths below if your repo lives elsewhere.
$ErrorActionPreference = "Stop"

$repo = "C:\Users\kylem\openai-agents-workflows-2025.09.28-v1"
$tasks = "$repo\tasks"

# Optional: load .env if present (python-dotenv will also load it)
# [System.Environment]::SetEnvironmentVariable("OPENAI_API_KEY", "sk-...", "Process")

# Ensure tasks directory exists
if (-not (Test-Path $tasks)) { New-Item -ItemType Directory -Path $tasks | Out-Null }

# Run once per minute; exit to let Task Scheduler re-launch on schedule
python "$repo\nightshift_runner.py" --repo "$repo" --tasks-dir "$tasks" --interval 60
