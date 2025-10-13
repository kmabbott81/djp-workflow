# DJP Workflow

[![CI Status](https://github.com/yourusername/djp-workflow/workflows/DJP%20Pipeline%20CI/badge.svg)](https://github.com/yourusername/djp-workflow/actions)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

> Debate-Judge-Publish workflow pipeline with grounded mode, redaction, and observability.

## Quickstart

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/djp-workflow.git
cd djp-workflow

# Create virtual environment and install dependencies
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Install in development mode (optional)
pip install -e ".[dev,dashboards]"
```

### Basic Usage

Run a simple workflow:

```bash
python -m src.run_workflow --task "Explain the benefits of type hints in Python"
```

Run with a preset:

```bash
python -m src.run_workflow --preset thorough --task "Your question here"
```

Run with grounded mode (corpus-based citations):

```bash
python -m src.run_workflow \
  --task "Summarize machine learning best practices" \
  --grounded_corpus ./corpus \
  --grounded_required 2
```

View the dashboard:

```bash
streamlit run dashboards/observability_app.py
```

### Documentation

For detailed operational guidance, see [docs/OPERATIONS.md](docs/OPERATIONS.md).

## 🚀 Deployment Architecture

The project uses a **single-service Railway deployment** connected directly to GitHub for continuous deployment:

```
GitHub (main branch)
    ↓ (automatic on every push)
Railway Relay Service
    ↓ (builds Docker image)
Production API
    ↓
https://relay-production-f2a6.up.railway.app
```

### Key Features:
- ✅ **Automatic Deployments**: Every push to `main` triggers a new build
- ✅ **Docker-based**: Uses multi-stage Dockerfile for optimized builds
- ✅ **Health Monitoring**: `/_stcore/health` endpoint for uptime checks
- ✅ **GPT-4 AI Planning**: Natural language to structured action planning
- ✅ **Environment Variables**: Encrypted secrets (OPENAI_API_KEY, DATABASE_URL, etc.)

### Quick Deploy:
```bash
# Push to main branch triggers automatic deployment
git push origin main

# OR manually trigger deployment
railway up
```

For detailed deployment documentation, see:
- [docs/ops/INTEGRATIONS.md](docs/ops/INTEGRATIONS.md) - External systems integration overview
- [docs/ops/RAILWAY-SINGLE-SERVICE.md](docs/ops/RAILWAY-SINGLE-SERVICE.md) - Complete Railway setup guide
- [docs/ops/DEPLOYMENT-FAQ.md](docs/ops/DEPLOYMENT-FAQ.md) - Common deployment questions

---

# OpenAI Agents Workflows Project

**Project Folder:** `openai-agents-workflows-2025.09.28-v1`
**Created:** September 28, 2025
**SDK Version:** OpenAI Agents v0.3.2

## Quick Start for Claude Code

To resume this project with Claude Code:
1. `cd C:\Users\kylem\openai-agents-workflows-2025.09.28-v1`
2. Read the most recent log file for current state
3. Continue building workflows

## Project Structure

For a comprehensive guide to the project structure, naming conventions, and file organization patterns, see:
**[docs/PROJECT-STRUCTURE.md](docs/PROJECT-STRUCTURE.md)**

Quick overview:
```
openai-agents-workflows-2025.09.28-v1/
├── README.md                           # This file
├── docs/PROJECT-STRUCTURE.md           # Comprehensive structure guide
├── 2025.10.10-PHASE-3-OAUTH-COMPLETE.md # Phase 3 OAuth summary (latest)
├── PHASE3_STATUS.md                    # Current phase status
├── docs/
│   ├── evidence/sprint-54/             # Sprint 54 evidence
│   ├── specs/                          # Technical specifications
│   └── planning/                       # Sprint plans
├── scripts/                            # Automation and E2E tests
├── src/                                # Source code
├── tests/                              # Test suites
└── [additional files following YYYY.MM.DD-HHMM-NAME.md pattern]
```

## Log Files

Log files are created after each significant step using the naming pattern:
`YYYY.MM.DD-HHMM-DESCRIPTION.md`

Each log file contains:
- What was accomplished
- Current state
- Next steps
- Claude Code restoration instructions
