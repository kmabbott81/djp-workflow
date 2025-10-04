# Onboarding Guide

Get started with DJP Workflow in 5 minutes. This guide covers installation, configuration, and running your first workflow.

## Prerequisites

Before starting, ensure you have:

- **Python 3.10+** (verify with `python --version`)
- **pip** package manager
- **git** for cloning the repository
- **OpenAI API key** (sign up at https://platform.openai.com)
- **Windows, macOS, or Linux** operating system

## Quick Start (5 Steps)

### 1. Clone and Install

```bash
# Clone repository
git clone https://github.com/yourusername/djp-workflow.git
cd djp-workflow

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env.local` file in the project root (this file is git-ignored for security):

```bash
# Windows:
copy .env .env.local

# macOS/Linux:
cp .env .env.local
```

Edit `.env.local` and set your API key:

```bash
# Required
OPENAI_API_KEY=sk-proj-your-key-here

# Optional (with defaults)
OPENAI_CONNECT_TIMEOUT_MS=10000
OPENAI_READ_TIMEOUT_MS=60000
DEFAULT_MODEL=gpt-4o-mini
```

**IMPORTANT: Never commit `.env.local` or API keys to git!**

### 3. Verify Installation

Test that everything works:

```bash
# Run test suite
pytest tests/ -q

# Verify schemas
python scripts/validate_artifacts.py

# Check environment
python -c "import os; print('API Key configured:', bool(os.getenv('OPENAI_API_KEY')))"
```

Expected output:
```
API Key configured: True
```

### 4. Run Your First Workflow

**Interactive mode (with wizard):**

```bash
python -m src.onboarding.wizard
```

The wizard will guide you through:
- API key validation
- Model selection
- Task creation
- Workflow execution

**Non-interactive mode (command-line):**

```bash
# Simple question
python -m src.run_workflow --task "Explain Python decorators"

# With preset
python -m src.run_workflow --preset thorough --task "Compare REST vs GraphQL APIs"

# With cost limits
python -m src.run_workflow --task "Your question" --budget_usd 0.01
```

### 5. View Results

Check the generated artifacts:

```bash
# List recent runs
ls runs/

# View artifact
cat runs/2025.10.02-1234.json

# Or use the dashboard
streamlit run dashboards/observability_app.py
```

## Environment Variables Reference

### Required Variables

| Variable | Description | Example |
|----------|-------------|---------|
| `OPENAI_API_KEY` | Your OpenAI API key (starts with `sk-`) | `sk-proj-abc123...` |

### Optional Variables (with defaults)

| Variable | Default | Description |
|----------|---------|-------------|
| `OPENAI_CONNECT_TIMEOUT_MS` | `10000` | Connection timeout in milliseconds |
| `OPENAI_READ_TIMEOUT_MS` | `60000` | Read timeout in milliseconds |
| `DEFAULT_MODEL` | `gpt-4o-mini` | Default AI model to use |
| `MAX_TOKENS` | `1000` | Max tokens per completion |
| `TEMPERATURE` | `0.3` | Sampling temperature (0.0-2.0) |
| `FEATURE_RBAC_ENFORCE` | `false` | Enable RBAC enforcement |
| `DEFAULT_TENANT_ID` | `default` | Default tenant for multi-tenancy |
| `AUDIT_LOG_DIR` | `audit/` | Directory for audit logs |
| `REDACTION_ENABLED` | `true` | Enable PII/secrets redaction |

## Running the Wizard

The interactive wizard helps first-time users configure and run workflows.

### Interactive Mode

```bash
python -m src.onboarding.wizard
```

**Wizard steps:**
1. Welcome screen
2. API key validation
3. Model selection (gpt-4o vs gpt-4o-mini)
4. Task input
5. Advanced options (optional)
6. Execution confirmation
7. Results display

### Non-Interactive Mode

Skip the wizard for automated/scripted usage:

```bash
python -m src.run_workflow \
  --task "Your question" \
  --model gpt-4o-mini \
  --max_tokens 1000 \
  --quiet
```

## Setting Environment Variables Safely

### Windows (PowerShell)

```powershell
# Temporary (current session only)
$env:OPENAI_API_KEY = "sk-proj-your-key-here"

# Permanent (user-level)
[System.Environment]::SetEnvironmentVariable('OPENAI_API_KEY', 'sk-proj-your-key-here', 'User')

# Best practice: Use .env.local file
```

### Windows (Command Prompt)

```cmd
# Temporary (current session only)
set OPENAI_API_KEY=sk-proj-your-key-here

# Run workflow
python -m src.run_workflow --task "Your question"
```

### macOS/Linux (Bash/Zsh)

```bash
# Temporary (current session only)
export OPENAI_API_KEY="sk-proj-your-key-here"

# Permanent (add to ~/.bashrc or ~/.zshrc)
echo 'export OPENAI_API_KEY="sk-proj-your-key-here"' >> ~/.bashrc
source ~/.bashrc

# Best practice: Use .env.local file
```

### Best Practice: Use `.env.local`

Create a `.env.local` file (git-ignored):

```bash
# .env.local
OPENAI_API_KEY=sk-proj-your-key-here
DEFAULT_MODEL=gpt-4o-mini
MAX_TOKENS=1000
TEMPERATURE=0.3
```

The application automatically loads variables from `.env.local` on startup.

**Security checklist:**
- [ ] `.env.local` is in `.gitignore` (already configured)
- [ ] Never commit API keys to repository
- [ ] Use different keys for dev/staging/prod
- [ ] Rotate keys every 90 days
- [ ] Use read-only keys when possible

## Running Sample Workflows

The project includes three example workflow templates.

### 1. Weekly Report

Generate professional weekly status reports:

```bash
# Dry-run (preview only, no API calls)
python -m src.run_workflow \
  --template weekly_report \
  --dry-run

# Live mode
python -m src.run_workflow \
  --template weekly_report \
  --inputs '{"start_date": "2025-10-01", "end_date": "2025-10-07", "context": "Project X status"}'
```

### 2. Meeting Brief

Summarize meeting transcripts and extract action items:

```bash
# Dry-run
python -m src.run_workflow \
  --template meeting_brief \
  --dry-run

# Live mode
python -m src.run_workflow \
  --template meeting_brief \
  --inputs '{"meeting_title": "Sprint Planning", "meeting_date": "2025-10-02", "attendees": "Team", "transcript": "..."}'
```

### 3. Inbox Sweep

Prioritize email inbox and drive files:

```bash
# Dry-run
python -m src.run_workflow \
  --template inbox_sweep \
  --dry-run

# Live mode
python -m src.run_workflow \
  --template inbox_sweep \
  --inputs '{"inbox_items": "...", "drive_files": "...", "user_priorities": "Sprint 25", "upcoming_deadlines": "..."}'
```

### Dry-Run vs Live Modes

**Dry-run mode** (`--dry-run`):
- No API calls made
- No costs incurred
- Shows projected cost and token usage
- Validates inputs and template
- Useful for testing and debugging

**Live mode** (default):
- Makes actual API calls
- Incurs costs based on usage
- Generates real artifacts
- Saves results to `runs/` directory
- Use `--budget_usd` to set cost limits

## Verification Steps

### Test Workflows

Run the full test suite:

```bash
# All tests
pytest tests/ -v

# Specific test categories
pytest tests/test_policies.py -v
pytest tests/test_templates_schema.py -v
pytest tests/test_guardrails.py -v
```

Expected: All tests pass (green checkmarks).

### View Artifacts

Check generated workflow artifacts:

```bash
# List all artifacts
ls runs/

# View artifact contents (Windows)
type runs\2025.10.02-1234.json

# View artifact contents (macOS/Linux)
cat runs/2025.10.02-1234.json

# View with JSON formatting
python -m json.tool runs/2025.10.02-1234.json
```

Artifact structure:
```json
{
  "task": "Your question",
  "status": "published",
  "published_text": "Final answer...",
  "metadata": {
    "cost_usd": 0.002,
    "tokens_used": 350,
    "model": "gpt-4o-mini"
  }
}
```

### Dashboard Verification

Launch the observability dashboard:

```bash
streamlit run dashboards/observability_app.py
```

**Dashboard checklist:**
- [ ] Recent runs displayed
- [ ] Cost metrics accurate
- [ ] Status breakdown chart visible
- [ ] Can filter by date range
- [ ] Artifact details load correctly

## Troubleshooting Common Issues

### Issue: "OPENAI_API_KEY not found"

**Symptom:** Error message when running workflow

**Cause:** Environment variable not set

**Resolution:**
```bash
# Windows (PowerShell)
$env:OPENAI_API_KEY = "sk-proj-your-key-here"

# Windows (Command Prompt)
set OPENAI_API_KEY=sk-proj-your-key-here

# macOS/Linux
export OPENAI_API_KEY="sk-proj-your-key-here"
```

**Prevention:** Use `.env.local` file

### Issue: "Invalid API key format"

**Symptom:** API authentication fails

**Cause:** Wrong key format or typo

**Resolution:**
- Verify key starts with `sk-proj-` or `sk-`
- Check for spaces or hidden characters
- Generate new key at https://platform.openai.com/api-keys

**Prevention:** Copy key directly from OpenAI dashboard

### Issue: Import errors or module not found

**Symptom:** `ModuleNotFoundError` when running scripts

**Cause:** Dependencies not installed or virtual environment not activated

**Resolution:**
```bash
# Verify virtual environment is activated
# (You should see (.venv) in your prompt)

# If not activated:
# Windows:
.venv\Scripts\activate
# macOS/Linux:
source .venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

**Prevention:** Always activate virtual environment before running commands

### Issue: Permission denied when creating logs

**Symptom:** Error writing to `logs/` or `audit/` directories

**Cause:** Directory doesn't exist or insufficient permissions

**Resolution:**
```bash
# Create directories
mkdir logs
mkdir audit
mkdir runs

# Windows: Grant write permissions
icacls logs /grant %USERNAME%:F
icacls audit /grant %USERNAME%:F

# macOS/Linux: Grant write permissions
chmod 755 logs audit runs
```

**Prevention:** Run installation script that creates directories

### Issue: Workflow times out

**Symptom:** `TimeoutError` or connection reset

**Cause:** Network issues or timeout too short

**Resolution:**
```bash
# Increase timeouts (in .env.local)
OPENAI_CONNECT_TIMEOUT_MS=30000
OPENAI_READ_TIMEOUT_MS=120000
```

**Prevention:** Set generous timeouts for complex workflows

See [docs/ERRORS.md](ERRORS.md) for comprehensive error documentation.

## Next Steps

Now that you're up and running:

1. **Customize Workflows**
   - Edit template YAML files in `templates/`
   - Create custom templates using `templates/examples/` as reference
   - See [docs/TEMPLATES.md](TEMPLATES.md) for template documentation

2. **Integrate with Applications**
   - Use Web API (`src/webapi.py`) for HTTP endpoints
   - Set up webhooks for approval workflows
   - See [docs/APPROVALS.md](APPROVALS.md) for approval workflow setup

3. **Configure Security**
   - Enable RBAC for multi-user access
   - Set up tenant isolation
   - Configure audit logging
   - See [docs/SECURITY.md](SECURITY.md) for security best practices

4. **Monitor and Optimize**
   - Use the Streamlit dashboard for observability
   - Set cost budgets per workflow
   - Configure alerts for anomalies
   - See [docs/OPERATIONS.md](OPERATIONS.md) for operational guidance

5. **Scale for Production**
   - Configure autoscaling worker pools
   - Set up multi-region deployment
   - Implement blue-green deployments
   - See [docs/DEPLOYMENT.md](DEPLOYMENT.md) and [docs/AUTOSCALING.md](AUTOSCALING.md)

## Resources

- **Documentation:**
  - [Templates Guide](TEMPLATES.md) - Create and customize workflow templates
  - [Operations Guide](OPERATIONS.md) - Run and monitor workflows
  - [Security Guide](SECURITY.md) - RBAC, multi-tenancy, audit logging
  - [Errors Reference](ERRORS.md) - Common errors and solutions
  - [Deployment Guide](DEPLOYMENT.md) - Production deployment strategies

- **Support:**
  - GitHub Issues: https://github.com/yourusername/djp-workflow/issues
  - Documentation: https://github.com/yourusername/djp-workflow/tree/main/docs
  - API Reference: See docstrings in `src/` modules

- **Community:**
  - Contribute: See [CONTRIBUTING.md](../CONTRIBUTING.md)
  - Code of Conduct: Respect and professional behavior expected
  - License: MIT (see [LICENSE](../LICENSE))

## Quick Reference Commands

```bash
# Run workflow with preset
python -m src.run_workflow --preset thorough --task "Your question"

# Run with cost limit
python -m src.run_workflow --task "Question" --budget_usd 0.01

# Run with grounded mode (citations required)
python -m src.run_workflow --task "Question" --grounded_corpus ./corpus --grounded_required 2

# Launch dashboard
streamlit run dashboards/observability_app.py

# Run tests
pytest tests/ -q

# Validate schemas
python scripts/validate_artifacts.py

# List available presets
python -m src.run_workflow --list-presets

# Replay previous run
python scripts/replay.py --latest
```

Welcome to DJP Workflow! Happy building!
