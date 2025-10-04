# DJP Pipeline Operations Guide

This guide covers operational aspects of the Debate-Judge-Publish (DJP) workflow pipeline.

## Table of Contents

- [Schema Validation](#schema-validation)
- [Cost Visibility](#cost-visibility)
- [CLI Presets](#cli-presets)
- [Grounded Mode (Full)](#grounded-mode-full)
- [Redaction Layer](#redaction-layer)
- [Replay Functionality](#replay-functionality)
- [CI/CD Integration](#cicd-integration)

## Schema Validation

### Running Schema Validation

The pipeline includes comprehensive schema validation to ensure data integrity:

```bash
# Run schema validation
python scripts/validate_artifacts.py
```

**Expected Output:**
```
DJP Pipeline Schema Validation
========================================
Validating schemas...
[OK] Schema valid: schemas\artifact.json
[OK] Sample artifact validates against schema
[OK] Schema valid: schemas\policy.json
[OK] Policy validates: openai_only.json
[OK] Policy validates: openai_preferred.json

[SUCCESS] Schema validation passed!
```

### What It Validates

- **Artifact Schema**: Validates all JSON artifacts against `schemas/artifact.json`
- **Policy Schema**: Validates policy files against `schemas/policy.json`
- **Sample Data**: Tests schema compatibility with generated sample artifacts
- **Real Artifacts**: Validates existing artifacts in `runs/` directory (if any)

### Integration

Schema validation is automatically run in CI/CD pipelines and returns proper exit codes for automation.

## Cost Visibility

### Default Cost Display

By default, the workflow shows cost breakdown after completion:

```bash
python -m src.run_workflow --task "Example task"
```

**Cost Footer Example:**
```
Costs: openai/gpt-4o in=150 out=80 $0.0021 | openai/gpt-4o-mini in=100 out=50 $0.0001 | Total $0.0022 (tokens=380)
```

### Suppressing Cost Output

Use the `--quiet` flag to suppress cost and summary output:

```bash
python -m src.run_workflow --task "Example task" --quiet
```

### Cost Breakdown Format

The cost footer shows:
- **Per-provider costs**: `provider in=tokens_in out=tokens_out $cost`
- **Total cost**: Sum of all provider costs
- **Total tokens**: Combined input and output tokens across all providers

## CLI Presets

### Available Presets

The pipeline includes 4 built-in presets for common use cases:

#### Quick Preset
Fast workflow with minimal settings:
```bash
python -m src.run_workflow --preset quick --task "Your task"
```
- Max tokens: 800
- Temperature: 0.2
- Fast-path enabled
- 2 debaters maximum
- 60 second timeout

#### Thorough Preset
Comprehensive analysis with high-quality output:
```bash
python -m src.run_workflow --preset thorough --task "Your task"
```
- Max tokens: 1500
- Temperature: 0.3
- 4 debaters maximum
- 300 second timeout
- 2 citations required

#### Research Preset
Research-focused with high citation requirements:
```bash
python -m src.run_workflow --preset research --task "Your task"
```
- Max tokens: 1200
- Temperature: 0.4
- 5 debaters maximum
- 3 citations required
- All providers allowed

#### Deterministic Preset
Reproducible results with fixed seed:
```bash
python -m src.run_workflow --preset deterministic --task "Your task"
```
- Max tokens: 1000
- Temperature: 0.0
- Fixed seed: 12345
- 3 debaters maximum

### Listing Available Presets

```bash
python -m src.run_workflow --list-presets
```

### Overriding Preset Values

Preset values can be overridden by explicitly setting CLI arguments:

```bash
python -m src.run_workflow --preset quick --task "Your task" --max_tokens 1000
```

This uses the `quick` preset but overrides `max_tokens` to 1000.

## Grounded Mode (Full)

Grounded Mode enforces corpus-based citations to ensure factual accuracy and source attribution.

### Setting Up a Corpus

Create a directory with source documents in supported formats:

```bash
mkdir corpus
# Add .txt, .md, or .pdf files
echo "# Machine Learning Basics..." > corpus/ml_basics.md
echo "Data science combines..." > corpus/data_science.txt
```

### Running with Grounded Mode

```bash
# Basic grounded run
python -m src.run_workflow \
  --task "Summarize 3 key insights about machine learning" \
  --grounded_corpus ./corpus \
  --grounded_required 2

# With research preset
python -m src.run_workflow \
  --preset research \
  --task "Explain data science best practices" \
  --grounded_corpus ./corpus \
  --grounded_required 3
```

### How It Works

1. **Corpus Loading**: System loads and indexes all documents from the corpus directory
2. **Context Injection**: Relevant documents are searched and injected into debater prompts
3. **Citation Requirements**: Debaters must cite sources using `[Title]` format
4. **Validation**: Judge validates citation count; insufficient citations result in disqualification
5. **Metadata Capture**: Citations are extracted and stored in artifact for audit trail

### Citation Format

Debaters cite sources using square brackets:

```
According to [Machine Learning Basics], supervised learning requires labeled data.
As noted in [Data Science Best Practices], feature engineering is crucial.
```

### Corpus Requirements

- **Supported formats**: `.txt`, `.md`, `.pdf` (requires pypdf library)
- **Encoding**: UTF-8 text
- **Structure**: Flat directory or nested subdirectories
- **Performance**: TF-IDF indexing when sklearn available; falls back to keyword search

### Monitoring Grounded Runs

Dashboard KPIs:
- **Grounded Runs**: Count and percentage of runs with grounding enabled
- **Avg Citations/Run**: Average number of corpus citations per grounded run
- **Grounded Fail Reason**: Reason when citation requirements not met

Filter by:
- "Grounded Only" checkbox in dashboard sidebar

Metrics columns:
- `grounded`: Boolean indicating if grounded mode was enabled
- `grounded_required`: Minimum citations required
- `citations_count`: Number of citations extracted from published text

### Troubleshooting

**Corpus not loading:**
- Verify directory path exists and contains supported file types
- Check file permissions
- Look for warnings in console output about skipped files

**Insufficient citations:**
- Increase `--max_tokens` to give debaters more space
- Reduce `--grounded_required` value if too strict
- Verify corpus documents are relevant to task
- Check that debaters are using correct `[Title]` citation format

**Citations not extracted:**
- Ensure exact title match or close variant
- Use explicit `[Title]` format in text
- Check corpus stats: `from src.corpus import get_corpus_stats; print(get_corpus_stats())`

## Redaction Layer

The redaction system automatically sanitizes PII and secrets from published outputs.

### Redaction by Default

Redaction is **enabled by default** and applies to all published and advisory text:

```bash
# Redaction is ON by default
python -m src.run_workflow --task "Contact us at admin@company.com"
# Output: Contact us at [REDACTED:EMAIL]
```

### Disabling Redaction

```bash
# Explicitly disable (not recommended for production)
python -m src.run_workflow --task "Your task" --redact off
```

### What Gets Redacted

Built-in rules detect and redact:
- **API Keys**: OpenAI (`sk-...`), Anthropic (`sk-ant-...`)
- **AWS Credentials**: Access keys (`AKIA...`), secret keys
- **Email Addresses**: Standard email format
- **Phone Numbers**: US phone formats
- **SSN**: Social Security Numbers
- **Credit Cards**: Visa, MasterCard, Amex, Discover (with Luhn validation)
- **IP Addresses**: IPv4 addresses
- **URLs**: HTTP/HTTPS URLs
- **JWT Tokens**: JSON Web Tokens
- **Private Keys**: PEM-formatted private keys

### Redaction Strategies

Default strategy is **label** (recommended):
```
Original: Contact admin@company.com or call (555) 123-4567
Redacted: Contact [REDACTED:EMAIL] or call [REDACTED:PHONE]
```

Configured in `config/redaction_rules.json`:
- **label**: Replace with `[REDACTED:TYPE]`
- **mask**: Replace with asterisks `********`
- **partial**: Show first/last chars `ad***@co***`

### Custom Redaction Rules

Override rules with a custom JSON file:

```bash
python -m src.run_workflow \
  --task "Your task" \
  --redaction_rules ./custom_rules.json
```

Custom rules format (see `config/redaction_rules.json`):
```json
{
  "rules": [
    {
      "name": "custom_pattern",
      "pattern": "CUSTOM-[0-9]{6}",
      "type": "custom_id",
      "description": "Custom ID format"
    }
  ],
  "strategies": {
    "label": {"replacement": "[REDACTED:{type}]"}
  },
  "default_strategy": "label"
}
```

### Monitoring Redacted Content

Dashboard KPIs:
- **Redacted Runs**: Count and percentage of runs where redaction occurred
- **Redaction Events**: Total count of items redacted across all runs

In run details:
- **Redacted**: Yes/No indicator
- **Redaction Events**: Count of redacted items
- **Redaction Types**: Comma-separated list of PII/secret types found

Metrics columns:
- `redacted`: Boolean indicating if any redaction occurred
- `redaction_count`: Number of items redacted
- `redaction_types`: Types of sensitive data found (e.g., "email,phone,api_key")

### Alert Thresholds

Monitor redaction frequency to detect unusual patterns:

```bash
# Warn if >10% of runs contain redacted content
python scripts/alerts.py --since 7d --threshold-redacted 0.10
```

High redaction rates may indicate:
- PII or secrets appearing in source data
- Prompt injection attempts
- Corpus contamination with sensitive data
- Need to sanitize input tasks

### Important Notes

1. **Citations Preserved**: Redaction does not affect `[Source Title]` citations
2. **Advisory Text**: Redaction applies to both published and advisory outputs
3. **Artifact Storage**: Original unredacted drafts remain in memory but artifacts store only redacted text
4. **Idempotent**: Applying redaction twice has no additional effect
5. **No False Positives**: Credit cards validated with Luhn algorithm to reduce false matches

## Replay Functionality

### Basic Usage

The replay system allows exact reproduction of any past run:

```bash
# List recent runs
python scripts/replay.py --list

# Show details of a specific run
python scripts/replay.py --show runs/2025.09.29-1445.json

# Replay the most recent run
python scripts/replay.py --latest

# Replay a specific run
python scripts/replay.py --replay runs/2025.09.29-1445.json
```

### Advanced Replay Options

```bash
# Replay with different task
python scripts/replay.py --replay runs/2025.09.29-1445.json --task "New question"

# Replay with custom trace name
python scripts/replay.py --replay runs/2025.09.29-1445.json --trace-name "custom-replay"

# Dry run (show command only)
python scripts/replay.py --replay runs/2025.09.29-1445.json --dry-run
```

### Replay Output Example

```bash
$ python scripts/replay.py --latest --dry-run
Replaying run from: 2025.09.29-1445.json
Command: python -m src.run_workflow --task "Original task" --trace_name "debate-judge-replay" --max_tokens 1200 --temperature 0.3 --policy openai_only
(Dry run - command not executed)
```

## CI/CD Integration

### Local CI Checks

Use the provided scripts to run the same checks as CI/CD:

**PowerShell (Windows):**
```powershell
.\scripts\ci_check.ps1
```

**Bash (Linux/macOS):**
```bash
bash scripts/ci_check.sh
```

### CI Check Components

The CI validation includes:

1. **Policy Tests**: `pytest tests/test_policies.py -q`
2. **Schema Validation**: `python scripts/validate_artifacts.py`
3. **Guardrails Tests**: `pytest tests/test_guardrails.py -q`
4. **Performance Smoke Tests**: `pytest tests/test_perf_smoke.py -q`

### GitHub Actions

The pipeline includes a complete GitHub Actions workflow at `.github/workflows/ci.yml` that:

- Tests multiple Python versions (3.9-3.12)
- Runs all validation checks
- Provides clear pass/fail status for pull requests
- Includes integration test support (when available)

### CI Success Example

```
DJP Pipeline CI/CD Validation
=============================

Running policy tests...
[OK] Policy tests passed

Running schema validation...
[OK] Schema validation passed

Running guardrails tests...
[OK] Guardrails tests passed

Running performance smoke tests...
[OK] Performance smoke tests passed

=============================
[SUCCESS] All CI checks passed!
```

## Troubleshooting

### Schema Validation Failures

If schema validation fails:
1. Check the error message for specific field issues
2. Verify JSON syntax in policy files
3. Ensure artifact structure matches schema requirements
4. Run `python scripts/validate_artifacts.py` locally for detailed output

### Preset Loading Errors

If preset loading fails:
1. Verify preset name spelling
2. Check that preset file exists in `presets/cli/`
3. Validate JSON syntax in preset files
4. Use `--list-presets` to see available options

### Replay Issues

If replay fails:
1. Verify artifact file path exists
2. Check that artifact contains required metadata
3. Ensure original run parameters are still valid
4. Use `--dry-run` to debug command generation

### Performance Test Failures

If performance tests fail:
1. Check system load - tests may timeout under high load
2. Verify all dependencies are installed
3. Review test thresholds if consistently failing
4. Check for import issues in the codebase

## Observability & Budgets

### Streamlit Dashboard

Monitor workflow performance and costs with the interactive dashboard:

```bash
streamlit run dashboards/observability_app.py
```

The dashboard provides:
- **Real-time metrics**: Recent runs, advisory rates, costs, token usage
- **Trend analysis**: Cost over time, provider distribution, status breakdown
- **Filtering**: By date range, preset, provider
- **Artifact inspection**: Detailed view of individual runs

### Budget Controls

Prevent cost overruns with budget limits:

```bash
# Set USD budget limit
python -m src.run_workflow --task "Example" --budget_usd 0.01

# Set token budget limit
python -m src.run_workflow --task "Example" --budget_tokens 5000

# Combine both limits
python -m src.run_workflow --task "Example" --budget_usd 0.01 --budget_tokens 5000
```

Budget behavior:
- **90% threshold**: Shows warning but continues
- **100% threshold**: Blocks execution and exits with error code

### Cost Projection

All workflows show projected costs before execution:

```
Projected Cost Breakdown:
  Debate Stage:  $0.0290
  Judge Stage:   $0.0165
  Total Cost:    $0.0480
  Total Tokens:  5,600
```

### Automated Alerts

Monitor workflow health with the alerts system:

```bash
# Check last 7 days with default thresholds
python scripts/alerts.py --since 7d

# Custom thresholds
python scripts/alerts.py --since 24h \
  --threshold-advisory 0.4 \
  --threshold-cost 0.005 \
  --threshold-grounded 0.6 \
  --threshold-redacted 0.10

# Send to Slack webhook
export WEBHOOK_URL=https://hooks.slack.com/your/webhook/url
python scripts/alerts.py --since 7d
```

Alert thresholds:
- **Advisory rate**: > 30% (configurable)
- **Average cost**: > $0.01 per run (configurable)
- **Failure rate**: > 20% (configurable)
- **Grounded rate**: < 60% when grounding used (configurable)
- **Redacted rate**: > 10% (configurable)

### Metrics Export

Export workflow metrics for analysis:

```bash
python -m src.run_workflow --task "Example" --preset quick --metrics metrics.csv
```

The CSV includes:
- Run metadata (timestamp, preset, task)
- Performance metrics (tokens, cost, duration)
- Quality metrics (status, provider, citations)
- Failure analysis (advisory reasons, safety flags)

## Best Practices

1. **Always run CI checks** before committing code changes
2. **Use presets** for consistent workflow configurations
3. **Validate schemas** after making schema changes
4. **Test replay functionality** after significant workflow changes
5. **Monitor costs** using the cost visibility features
6. **Keep artifacts** for debugging and reproducibility
7. **Set budget limits** for cost control in production
8. **Monitor dashboards** regularly for performance insights
9. **Configure alerts** for proactive issue detection
10. **Export metrics** for long-term analysis and reporting

## Release & Packaging

This section covers building, versioning, and releasing the DJP workflow package.

### Building Packages

Build source distribution and wheel packages for distribution:

```bash
# Install build tool
pip install build

# Build packages (creates dist/ directory)
python -m build

# Verify the build
ls dist/
# Expected output:
#   djp_workflow-1.0.0-py3-none-any.whl
#   djp_workflow-1.0.0.tar.gz
```

The build process:
1. Reads configuration from `pyproject.toml`
2. Creates source distribution (`.tar.gz`)
3. Creates wheel distribution (`.whl`)
4. Places both in `dist/` directory

**Verify package integrity:**

```bash
pip install twine
python -m twine check dist/*
```

Expected output:
```
Checking dist/djp_workflow-1.0.0-py3-none-any.whl: PASSED
Checking dist/djp_workflow-1.0.0.tar.gz: PASSED
```

### Version Bumping

Use the version management script to update version numbers:

```bash
# Bump patch version (1.0.0 -> 1.0.1)
python scripts/version.py --patch

# Bump minor version (1.0.0 -> 1.1.0)
python scripts/version.py --minor

# Bump major version (1.0.0 -> 2.0.0)
python scripts/version.py --major
```

**What gets updated:**
- `src/__init__.py` - `__version__` attribute
- `pyproject.toml` - `version` field
- `CHANGELOG.md` - New version section with template

**Version bump workflow:**

```bash
# 1. Bump version
python scripts/version.py --minor

# 2. Edit CHANGELOG.md to add release notes
# Fill in the Added, Changed, Fixed sections

# 3. Commit changes
git add -A
git commit -m "Bump version to 1.1.0"

# 4. Tag release
git tag v1.1.0

# 5. Push to trigger release workflow
git push && git push --tags
```

### Dependency Management

The project uses `pip-tools` for reproducible dependency management:

**Update dependencies:**

```bash
# Install pip-tools
pip install pip-tools

# Compile production dependencies
pip-compile requirements.in -o requirements.txt

# Compile development dependencies
pip-compile requirements-dev.in -o requirements-dev.txt

# Upgrade all dependencies to latest compatible versions
pip-compile --upgrade requirements.in
pip-compile --upgrade requirements-dev.in
```

**Add new dependencies:**

1. Add to `requirements.in` (production) or `requirements-dev.in` (development)
2. Recompile: `pip-compile requirements.in`
3. Sync environment: `pip-sync requirements.txt requirements-dev.txt`

**Dependency files:**
- `requirements.in` - Top-level production dependencies
- `requirements-dev.in` - Top-level development dependencies
- `requirements.txt` - Locked production dependencies (committed)
- `requirements-dev.txt` - Locked development dependencies (committed)
- `pyproject.toml` - Package metadata and optional dependencies

### Release Workflow

The automated release process is triggered when you push a version tag:

**Manual release:**

```bash
# 1. Ensure all changes are committed
git status

# 2. Bump version
python scripts/version.py --minor

# 3. Update CHANGELOG.md with release notes

# 4. Commit and tag
git add -A
git commit -m "Release version 1.1.0"
git tag v1.1.0

# 5. Push to trigger GitHub Actions
git push origin main
git push origin v1.1.0
```

**What happens automatically (GitHub Actions):**

1. **Build Job** (`.github/workflows/release.yml`):
   - Checks out code with full history
   - Sets up Python 3.11 environment
   - Installs build dependencies (`build`, `twine`)
   - Installs project dependencies
   - Runs full test suite (`pytest tests/`)
   - Builds source and wheel distributions
   - Validates distributions with `twine check`
   - Uploads artifacts for download

2. **Release Creation**:
   - Extracts version from tag (e.g., `v1.1.0` -> `1.1.0`)
   - Generates release notes from CHANGELOG.md
   - Creates draft GitHub Release
   - Attaches distribution files (`.tar.gz`, `.whl`)
   - Provides summary in GitHub Actions output

3. **Manual Step**:
   - Review the draft release on GitHub
   - Edit release notes if needed
   - Publish the release when ready

**Release workflow features:**
- Automatic test execution before building
- Distribution validation
- Draft releases for review before publishing
- Artifact retention for 30 days
- Detailed build summaries

### Installing from Wheel

Install the packaged distribution:

**From local build:**

```bash
# Install from wheel (recommended)
pip install dist/djp_workflow-1.0.0-py3-none-any.whl

# Or install from source distribution
pip install dist/djp_workflow-1.0.0.tar.gz
```

**With optional dependencies:**

```bash
# Install with dashboard support
pip install "djp_workflow-1.0.0-py3-none-any.whl[dashboards]"

# Install with PDF support
pip install "djp_workflow-1.0.0-py3-none-any.whl[pdf]"

# Install with development tools
pip install "djp_workflow-1.0.0-py3-none-any.whl[dev]"

# Install all optional dependencies
pip install "djp_workflow-1.0.0-py3-none-any.whl[dashboards,pdf,dev]"
```

**From GitHub Release:**

```bash
# Download wheel from GitHub Releases page, then:
pip install djp_workflow-1.0.0-py3-none-any.whl
```

**Verify installation:**

```bash
# Check installed version
pip show djp-workflow

# Run the CLI
djp --help

# Or run as module
python -m src.run_workflow --help
```

### Pre-Release Checklist

Before creating a release:

- [ ] All tests passing: `pytest tests/`
- [ ] CI checks passing: `python scripts/ci_check.ps1` (Windows) or `bash scripts/ci_check.sh` (Linux/macOS)
- [ ] Schema validation: `python scripts/validate_artifacts.py`
- [ ] Version bumped: `python scripts/version.py --[major|minor|patch]`
- [ ] CHANGELOG.md updated with release notes
- [ ] Documentation updated (README.md, OPERATIONS.md, etc.)
- [ ] Local build successful: `python -m build`
- [ ] Package validation: `twine check dist/*`
- [ ] Changes committed and tagged

### Troubleshooting Releases

**Build fails:**
- Verify `pyproject.toml` syntax
- Check that all required files are present
- Ensure dependencies are installed: `pip install build`
- Check Python version compatibility (>=3.9)

**Tests fail during release:**
- Run tests locally: `pytest tests/ -v`
- Fix failing tests before proceeding
- Ensure all dependencies are in requirements.txt

**Tag already exists:**
```bash
# Delete local tag
git tag -d v1.0.0

# Delete remote tag
git push origin --delete v1.0.0

# Create new tag
git tag v1.0.0
git push origin v1.0.0
```

**Release workflow not triggered:**
- Verify tag format: `v*` (e.g., `v1.0.0`)
- Check GitHub Actions is enabled for the repository
- Review workflow file: `.github/workflows/release.yml`
- Check GitHub Actions logs for errors
