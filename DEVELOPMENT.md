# Development Guide

Quick-start guide for local development on the DJP Workflow platform.

## Prerequisites

- **Python**: 3.9 or higher (3.11 recommended)
- **Git**: For version control
- **Docker** (optional): For containerized development
- **Redis** (optional): For queue functionality

## Quick Start

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/kmabbott81/djp-workflow.git
cd djp-workflow

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install --upgrade pip
pip install -e ".[dev,dashboards]"

# Install pre-commit hooks
pre-commit install
```

### 2. Configuration

```bash
# Copy example config
cp configs/.env.example .env

# Edit .env with your settings
# Minimal config for local dev:
ENV=development
TENANT_ID=dev-tenant
LOG_LEVEL=INFO
```

### 3. Validate Setup

```bash
# Run config validation
python -m src.config.validate

# Run bootstrap (creates initial admin)
python scripts/bootstrap.py
```

### 4. Run Tests

```bash
# Fast unit tests
pytest -v -m "not slow"

# Smoke tests
pytest -m e2e -v

# All tests
pytest -v
```

### 5. Start the Dashboard (Optional)

```bash
streamlit run dashboards/app.py
```

## Common Development Tasks

### Running Tests

```bash
# Unit tests only
pytest tests/ --ignore=tests_e2e -v

# Specific test file
pytest tests/test_audit.py -v

# With coverage
pytest --cov=src --cov-report=html

# Parallel execution
pytest -n auto
```

### Code Quality

```bash
# Format code
black .

# Lint
ruff check .

# Type check
mypy src/

# Run all pre-commit checks
pre-commit run --all-files
```

### Building Distribution

```bash
# Build wheel and sdist
python -m build

# Check dist
twine check dist/*
```

### Docker Development

```bash
# Build images
docker compose -f docker/docker-compose.yml build

# Start services
docker compose -f docker/docker-compose.yml up -d

# View logs
docker compose -f docker/docker-compose.yml logs -f

# Run tests in container
docker compose -f docker/docker-compose.yml exec app pytest -v

# Stop services
docker compose -f docker/docker-compose.yml down
```

Or use the Makefile:

```bash
make build    # Build images
make up       # Start services
make logs     # View logs
make test     # Run tests
make down     # Stop services
make clean    # Clean up
```

## Project Structure

```
djp-workflow/
├── src/                    # Core application code
│   ├── agents/            # Agent implementations
│   ├── connectors/        # Platform connectors (Slack, Teams, Gmail, etc.)
│   ├── cost/              # Budget and cost tracking
│   ├── nl/                # Natural language commanding
│   ├── orchestrator/      # Workflow orchestration
│   ├── security/          # RBAC, audit, encryption
│   └── urg/               # Unified Resource Graph
├── scripts/               # CLI utilities
├── dashboards/            # Streamlit UI
├── tests/                 # Unit and integration tests
├── tests_e2e/             # End-to-end smoke tests
├── docker/                # Docker configuration
├── docs/                  # Documentation
└── configs/               # Configuration examples
```

## Common Issues

### Issue: Module Not Found

**Solution**: Ensure you've installed the package in editable mode:
```bash
pip install -e .
```

### Issue: Tests Failing with Import Errors

**Solution**: Install dev dependencies:
```bash
pip install -e ".[dev]"
```

### Issue: Pre-commit Hooks Failing

**Solution**: Run hooks manually and commit fixes:
```bash
pre-commit run --all-files
git add -u
git commit -m "fix: pre-commit hook corrections"
```

### Issue: Docker Build Fails

**Solution**: Clean Docker cache and rebuild:
```bash
docker system prune -a
docker compose -f docker/docker-compose.yml build --no-cache
```

### Issue: Config Validation Errors

**Solution**: Check your `.env` file against `configs/.env.example`:
```bash
python -m src.config.validate --strict
```

## Environment Variables

See `configs/.env.example` for comprehensive list. Key variables:

- `ENV`: Environment (development/staging/production)
- `TENANT_ID`: Tenant identifier
- `LOG_LEVEL`: Logging level (DEBUG/INFO/WARNING/ERROR)
- `FEATURE_RBAC_ENFORCE`: Enable RBAC (true/false)
- `FEATURE_BUDGETS`: Enable budget enforcement (true/false)

## Running Specific Components

### Connector Tests (Isolated)

```bash
# Test specific connector
pytest tests/test_connector_slack.py -v

# DRY_RUN mode (no API calls)
DRY_RUN=true pytest tests/test_connector_slack.py -v
```

### URG Operations

```bash
# Index resources
python -c "from src.urg.index import URGIndex; idx = URGIndex(); idx.index_resource(...)"

# Search
python scripts/urg_search.py --query "meeting notes"
```

### Natural Language Commands

```bash
# Test NL parser
python -c "from src.nl.parser import parse_intent; print(parse_intent('send email to Alice'))"
```

## IDE Setup

### VS Code

Recommended extensions:
- Python
- Pylance
- Python Test Explorer
- GitLens
- Docker

Settings (`.vscode/settings.json`):
```json
{
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "python.testing.pytestEnabled": true,
  "editor.formatOnSave": true
}
```

### PyCharm

1. Mark `src/` as Sources Root
2. Set pytest as default test runner
3. Enable Black formatter
4. Configure Ruff as external tool

## Debugging

### Debug Tests

```bash
# Run single test with verbose output
pytest tests/test_audit.py::test_audit_log_event -vvs

# Drop into debugger on failure
pytest --pdb

# Start debugger at specific point in code
import pdb; pdb.set_trace()
```

### Debug Dashboard

```bash
# Run with debug mode
streamlit run dashboards/app.py --server.fileWatcherType=none --logger.level=debug
```

## Performance Profiling

```bash
# Profile tests
pytest --profile

# Profile specific code
python -m cProfile -o output.prof scripts/your_script.py
python -m pstats output.prof
```

## Documentation

- **Operations**: See [docs/OPERATIONS.md](docs/OPERATIONS.md)
- **Security**: See [docs/SECURITY.md](docs/SECURITY.md)
- **Contributing**: See [CONTRIBUTING.md](CONTRIBUTING.md)
- **Support**: See [SUPPORT.md](SUPPORT.md)

## Getting Help

- Check [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines
- Review [docs/OPERATIONS.md](docs/OPERATIONS.md) for operational procedures
- Open an issue for bugs or feature requests
- Join discussions for questions

---

**Happy coding!** 🚀
