# Contributing to DJP-Workflow

Thank you for your interest in contributing to the Debate-Judge-Publish workflow project! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Development Setup](#development-setup)
- [Branch Strategy](#branch-strategy)
- [Commit Conventions](#commit-conventions)
- [Testing](#testing)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Release Process](#release-process)

## Development Setup

### Prerequisites

- Python 3.9 or higher
- pip and pip-tools
- Git

### Setup Instructions

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/djp-workflow.git
   cd djp-workflow
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv .venv
   ```

3. **Activate the virtual environment**
   - **Windows (PowerShell)**:
     ```powershell
     .\.venv\Scripts\Activate.ps1
     ```
   - **Windows (cmd)**:
     ```cmd
     .venv\Scripts\activate.bat
     ```
   - **macOS/Linux**:
     ```bash
     source .venv/bin/activate
     ```

4. **Install development dependencies**
   ```bash
   pip install --upgrade pip
   pip install -r requirements-dev.txt
   ```

5. **Install pre-commit hooks**
   ```bash
   pre-commit install
   ```

6. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

### Dependency Management

We use `pip-tools` to manage dependencies:

- **Update dependencies**:
  ```bash
  pip-compile requirements.in
  pip-compile requirements-dev.in
  ```

- **Upgrade all dependencies**:
  ```bash
  pip-compile --upgrade requirements.in
  pip-compile --upgrade requirements-dev.in
  ```

- **Install updated dependencies**:
  ```bash
  pip-sync requirements-dev.txt
  ```

## Branch Strategy

We follow a simplified Git Flow strategy:

### Branch Types

- **`main`**: Production-ready code. Protected branch.
- **`develop`**: Integration branch for features. Default branch for PRs.
- **`feature/<name>`**: New features or enhancements
- **`fix/<name>`**: Bug fixes
- **`docs/<name>`**: Documentation updates
- **`refactor/<name>`**: Code refactoring
- **`test/<name>`**: Test improvements

### Branch Naming

Use descriptive kebab-case names:
- `feature/grounded-mode`
- `fix/citation-validation`
- `docs/operations-guide`
- `refactor/debate-engine`

### Workflow

1. Create a branch from `develop`:
   ```bash
   git checkout develop
   git pull origin develop
   git checkout -b feature/your-feature-name
   ```

2. Make your changes and commit (see [Commit Conventions](#commit-conventions))

3. Push your branch:
   ```bash
   git push -u origin feature/your-feature-name
   ```

4. Open a Pull Request to `develop`

## Commit Conventions

We follow [Conventional Commits](https://www.conventionalcommits.org/) specification:

### Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### Types

- **feat**: New feature
- **fix**: Bug fix
- **docs**: Documentation changes
- **style**: Code style changes (formatting, no logic change)
- **refactor**: Code refactoring
- **test**: Adding or updating tests
- **chore**: Maintenance tasks (dependencies, build, etc.)
- **perf**: Performance improvements

### Scope (optional)

The scope should be the name of the module affected:
- `debate`
- `judge`
- `publish`
- `corpus`
- `redaction`
- `metrics`
- `cli`

### Examples

```bash
# Feature
feat(corpus): add TF-IDF search for grounded mode

Implements vector-based corpus search using sklearn's TfidfVectorizer.
Falls back to keyword search when sklearn is unavailable.

# Bug fix
fix(redaction): correct credit card Luhn validation

The Luhn algorithm implementation was incorrectly handling card numbers
with spaces. Updated to strip whitespace before validation.

# Documentation
docs: update OPERATIONS.md with redaction examples

# Chore
chore: bump dependencies to latest versions
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_corpus.py

# Run with coverage
pytest --cov=src --cov-report=html

# Run only fast tests (skip slow/integration)
pytest -m "not slow"
```

### Writing Tests

- Place tests in `tests/` directory
- Name test files `test_<module>.py`
- Name test functions `test_<functionality>()`
- Use descriptive test names that explain what is being tested
- Follow AAA pattern: Arrange, Act, Assert

Example:
```python
def test_corpus_search_returns_top_k_results():
    # Arrange
    corpus = CorpusLoader()
    corpus.load_directory("./test_corpus")

    # Act
    results = corpus.search("machine learning", top_k=3)

    # Assert
    assert len(results) == 3
    assert all(isinstance(r, CorpusDocument) for r in results)
```

## Code Style

### Python Style Guide

- **Line length**: 120 characters (enforced by Black)
- **Type hints**: Encouraged but not required
- **Docstrings**: Required for public functions/classes (Google style)
- **Imports**: Sorted with isort (handled by Ruff)

### Tools

- **Black**: Auto-formatting
  ```bash
  black src/ tests/ scripts/
  ```

- **Ruff**: Linting and import sorting
  ```bash
  ruff check src/ tests/ scripts/ --fix
  ```

- **Mypy**: Type checking (optional)
  ```bash
  mypy src/
  ```

### Pre-commit Hooks

Pre-commit hooks will automatically run Black, Ruff, and other checks:
```bash
pre-commit run --all-files
```

## Pull Request Process

### Before Submitting

1. Ensure all tests pass: `pytest`
2. Run code formatters: `black .` and `ruff check . --fix`
3. Update documentation if needed
4. Add/update tests for new functionality
5. Update CHANGELOG.md with your changes

### PR Guidelines

1. **Title**: Use conventional commit format
   - `feat: Add grounded mode support`
   - `fix: Resolve citation extraction bug`

2. **Description**: Include:
   - Summary of changes
   - Motivation and context
   - Screenshots (if UI changes)
   - Related issues (closes #123)

3. **Checklist**:
   - [ ] Tests added/updated
   - [ ] Documentation updated
   - [ ] CHANGELOG.md updated
   - [ ] All tests passing
   - [ ] Code formatted (Black + Ruff)

### Review Process

- At least one approval required
- All CI checks must pass
- No unresolved comments
- Maintainers will merge approved PRs

## Release Process

Releases are managed by maintainers following semantic versioning (SemVer).

### Version Bumping

```bash
# Patch release (1.0.0 -> 1.0.1)
python scripts/version.py --patch

# Minor release (1.0.0 -> 1.1.0)
python scripts/version.py --minor

# Major release (1.0.0 -> 2.0.0)
python scripts/version.py --major
```

### Release Steps

1. Update version with `scripts/version.py`
2. Update CHANGELOG.md with release notes
3. Commit: `git commit -m "chore: bump version to X.Y.Z"`
4. Tag: `git tag vX.Y.Z`
5. Push: `git push && git push --tags`
6. Create GitHub release with `scripts/release_notes.py`

## Questions or Need Help?

- Open an issue for bugs or feature requests
- Start a discussion for questions or ideas
- Check [docs/OPERATIONS.md](docs/OPERATIONS.md) for operational guidance

Thank you for contributing!
