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
- [Storage Lifecycle Management](#storage-lifecycle-management)

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

## Sample Workflows

The `templates/examples/` directory provides three production-ready workflow templates for common use cases.

### Running Sample Workflows

#### 1. Weekly Report Workflow

Generate professional status reports for team updates:

**Basic usage:**
```bash
# Windows
python -m src.run_workflow ^
  --template weekly_report ^
  --inputs "{\"start_date\": \"2025-10-01\", \"end_date\": \"2025-10-07\", \"context\": \"Sprint 25: Completed 15 story points, deployed v1.2.0\"}"

# macOS/Linux
python -m src.run_workflow \
  --template weekly_report \
  --inputs '{"start_date": "2025-10-01", "end_date": "2025-10-07", "context": "Sprint 25: Completed 15 story points, deployed v1.2.0"}'
```

**Dry-run mode (no API calls):**
```bash
python -m src.run_workflow --template weekly_report --dry-run
```

**With cost budget:**
```bash
python -m src.run_workflow ^
  --template weekly_report ^
  --inputs "{...}" ^
  --budget_usd 0.01
```

**Output:** Structured Markdown report (800-1200 words) with executive summary, accomplishments, metrics, challenges, next week priorities, and action items.

**Use cases:**
- Project status updates
- Team stand-ups
- Executive briefings
- Client progress reports

#### 2. Meeting Brief Workflow

Summarize meeting transcripts and extract action items:

**Basic usage:**
```bash
# Windows
python -m src.run_workflow ^
  --template meeting_brief ^
  --inputs "{\"meeting_title\": \"Sprint Planning\", \"meeting_date\": \"2025-10-02\", \"attendees\": \"Alice, Bob, Charlie\", \"transcript\": \"Alice: Let's review the backlog...\"}"

# macOS/Linux
python -m src.run_workflow \
  --template meeting_brief \
  --inputs '{"meeting_title": "Sprint Planning", "meeting_date": "2025-10-02", "attendees": "Alice, Bob, Charlie", "transcript": "Alice: Let's review the backlog..."}'
```

**With approval workflow:**
```bash
python -m src.run_workflow ^
  --template meeting_brief ^
  --inputs "{...}" ^
  --require_approval
```

**Output:** Structured brief (500-800 words) with meeting overview, discussion points, decisions, action items table, and follow-up questions.

**Use cases:**
- Academic meeting notes
- Faculty meetings
- Research group syncs
- Professional team meetings

#### 3. Inbox Sweep Workflow

Prioritize email and document backlogs:

**Basic usage:**
```bash
# Windows
python -m src.run_workflow ^
  --template inbox_sweep ^
  --inputs "{\"inbox_items\": \"1. RE: Budget approval\n2. Team sync invite\", \"drive_files\": \"Q4-plan.docx, budget.xlsx\", \"user_priorities\": \"Sprint 25 completion\", \"upcoming_deadlines\": \"Q4 kickoff Oct 15\"}"

# macOS/Linux
python -m src.run_workflow \
  --template inbox_sweep \
  --inputs '{"inbox_items": "1. RE: Budget approval\n2. Team sync invite", "drive_files": "Q4-plan.docx, budget.xlsx", "user_priorities": "Sprint 25 completion", "upcoming_deadlines": "Q4 kickoff Oct 15"}'
```

**Output:** Prioritized task list (1000-1500 words) with P0-P3 categorization, automation suggestions, and delegation opportunities.

**Use cases:**
- Email triage
- Task prioritization
- Productivity coaching
- Time management

### Monitoring Workflow Execution

#### Real-Time Monitoring

Track workflow progress in real-time:

```bash
# Run workflow with verbose output
python -m src.run_workflow --template weekly_report --inputs "{...}" --verbose

# Monitor logs in separate terminal
# Windows:
Get-Content logs\workflow.log -Wait -Tail 50

# macOS/Linux:
tail -f logs/workflow.log
```

#### Cost Tracking

Monitor costs for sample workflows:

```bash
# View cost breakdown
python -m src.run_workflow --template meeting_brief --inputs "{...}"

# Output includes:
# Costs: openai/gpt-4o-mini in=350 out=220 $0.0008 | Total $0.0008 (tokens=570)
```

**Cost expectations by template:**
- **Weekly Report:** $0.003-0.008 (gpt-4o, ~1500 tokens)
- **Meeting Brief:** $0.0005-0.002 (gpt-4o-mini, ~800 tokens)
- **Inbox Sweep:** $0.004-0.010 (gpt-4o, ~2000 tokens)

#### Performance Metrics

Track execution time and success rates:

```bash
# Run with metrics export
python -m src.run_workflow ^
  --template weekly_report ^
  --inputs "{...}" ^
  --metrics metrics.csv

# View metrics
# Windows: type metrics.csv
# macOS/Linux: cat metrics.csv
```

**Expected performance:**
- **Weekly Report:** 8-15 seconds
- **Meeting Brief:** 5-10 seconds
- **Inbox Sweep:** 12-20 seconds

### Artifact Management

#### Viewing Generated Artifacts

```bash
# List recent artifacts
# Windows:
dir /O-D runs\*.json | more

# macOS/Linux:
ls -lt runs/*.json | head -10

# View specific artifact
# Windows:
type runs\2025.10.02-1234.json

# macOS/Linux:
cat runs/2025.10.02-1234.json | jq .
```

#### Artifact Retention Policy

Configure automatic cleanup:

```bash
# In .env.local
ARTIFACT_RETENTION_DAYS=90

# Manual cleanup (delete artifacts older than 30 days)
# Windows PowerShell:
Get-ChildItem runs\*.json | Where-Object {$_.LastWriteTime -lt (Get-Date).AddDays(-30)} | Remove-Item

# macOS/Linux:
find runs/ -name "*.json" -mtime +30 -delete
```

#### Artifact Export

Export artifacts for analysis:

```bash
# Export all artifacts to CSV
python scripts/export_artifacts.py --output artifacts.csv

# Export specific date range
python scripts/export_artifacts.py --since 2025-10-01 --until 2025-10-07 --output weekly.csv
```

### Cost Budgeting Per Workflow

Set and enforce cost limits for each workflow:

#### Budget Configuration

```bash
# Per-workflow budget limits (in .env.local)
BUDGET_WEEKLY_REPORT_USD=0.01
BUDGET_MEETING_BRIEF_USD=0.005
BUDGET_INBOX_SWEEP_USD=0.015
```

#### Runtime Budget Enforcement

```bash
# Set budget at runtime
python -m src.run_workflow ^
  --template weekly_report ^
  --inputs "{...}" ^
  --budget_usd 0.01

# Budget exceeded error:
# BudgetExceededError: Projected cost $0.015 exceeds budget $0.010
```

#### Budget Monitoring

```bash
# View budget utilization in dashboard
streamlit run dashboards/observability_app.py

# Check budget alerts
python scripts/check_budgets.py --since 7d
```

### Performance Tuning

#### Timeout Configuration

Adjust timeouts for complex workflows:

```bash
# In .env.local
OPENAI_CONNECT_TIMEOUT_MS=15000  # Connection timeout
OPENAI_READ_TIMEOUT_MS=120000    # Read timeout (2 minutes)
```

For specific workflows:
```bash
python -m src.run_workflow ^
  --template inbox_sweep ^
  --inputs "{...}" ^
  --timeout 180  # 3 minutes
```

#### Retry Strategy

Configure retry behavior for transient failures:

```bash
# In .env.local
MAX_RETRIES=3
RETRY_BACKOFF_FACTOR=2  # Exponential backoff: 1s, 2s, 4s
```

**Retry conditions:**
- Network timeouts
- Rate limit errors (429)
- Temporary API unavailability (503)

**No retry on:**
- Invalid API key (401)
- Malformed requests (400)
- Budget exceeded errors

#### Batch Size Optimization

Process multiple workflows efficiently:

```bash
# Process batch of reports
python -m src.batch ^
  --template weekly_report ^
  --input batch.csv ^
  --output results/ ^
  --max-cost 0.50 ^
  --concurrency 5

# batch.csv format:
# start_date,end_date,context
# 2025-10-01,2025-10-07,"Sprint 25 summary"
# 2025-10-08,2025-10-14,"Sprint 26 summary"
```

**Performance tuning:**
- **Concurrency 1-3:** Low load, sequential processing
- **Concurrency 4-8:** Medium load, parallel processing
- **Concurrency 9+:** High load, requires rate limit management

### Scaling with Worker Pool Integration

#### Worker Pool Configuration

Configure autoscaling for production workloads:

```bash
# In .env.local
MIN_WORKERS=2
MAX_WORKERS=12
TARGET_QUEUE_DEPTH=50
TARGET_P95_LATENCY_MS=2000
SCALE_DECISION_INTERVAL_MS=2000
```

#### Submitting Workflows to Worker Pool

```python
from src.scale.worker_pool import WorkerPool, Job

pool = WorkerPool.get_instance()

# Submit workflow job
job = Job(
    job_id="weekly-report-001",
    task=lambda: run_workflow(
        template="weekly_report",
        inputs={"start_date": "2025-10-01", "end_date": "2025-10-07", "context": "..."}
    ),
    tenant_id="team-alpha"
)

result = pool.submit_job(job)
```

#### Monitoring Worker Pool Performance

```bash
# View worker pool stats
python -c "
from src.scale.worker_pool import WorkerPool
pool = WorkerPool.get_instance()
stats = pool.get_stats()
print(f'Total workers: {stats.total_workers}')
print(f'Active workers: {stats.active_workers}')
print(f'Queue depth: {stats.queue_depth}')
"
```

#### Per-Tenant Concurrency Limits

```bash
# In .env.local
PER_TENANT_MAX_CONCURRENCY=5  # Max 5 concurrent workflows per tenant

# Enforces fair resource allocation across teams
```

**Use cases:**
- Multi-team environments
- SaaS deployments
- Shared infrastructure
- Resource fairness

### Workflow Best Practices

#### 1. Use Dry-Run First

Always test workflows with dry-run before production:

```bash
# Validate inputs and check projected cost
python -m src.run_workflow --template weekly_report --dry-run

# Output:
# Dry run mode - no API calls made
# Projected cost: $0.005
# Projected tokens: ~1200
```

#### 2. Set Appropriate Budgets

Prevent cost overruns with budget limits:

```bash
# Development: Low budgets
--budget_usd 0.005

# Staging: Medium budgets
--budget_usd 0.02

# Production: Higher budgets with monitoring
--budget_usd 0.05
```

#### 3. Monitor Execution Logs

Review logs for errors and optimization opportunities:

```bash
# Check for errors
# Windows:
findstr /I "error" logs\workflow.log

# macOS/Linux:
grep -i error logs/workflow.log

# Check performance
grep "execution_time" logs/workflow.log
```

#### 4. Use Appropriate Models

Select models based on task complexity:

```yaml
# Simple tasks (summaries, briefs)
parameters:
  model: gpt-4o-mini  # $0.15 per 1M input tokens

# Complex tasks (analysis, reports)
parameters:
  model: gpt-4o  # $2.50 per 1M input tokens
```

#### 5. Enable Approval Workflows

Require human review for critical outputs:

```bash
python -m src.run_workflow ^
  --template weekly_report ^
  --inputs "{...}" ^
  --require_approval

# Output status: pending_approval
# Review in dashboard, then approve or reject
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

### Sample Workflow Failures

If sample workflows fail:

**Template not found:**
```bash
# Verify template exists
ls templates/examples/

# Expected: weekly_report.yaml, meeting_brief.yaml, inbox_sweep.yaml
```

**Input validation errors:**
```bash
# Check required inputs for template
python -c "
from src.templates import load_template
template = load_template('weekly_report')
print('Required inputs:', [i for i in template.inputs if i.required])
"
```

**Cost budget exceeded:**
```bash
# Check projected cost first
python -m src.run_workflow --template weekly_report --dry-run

# Increase budget if needed
python -m src.run_workflow --template weekly_report --budget_usd 0.02
```

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

### Cost Governance & Budget Guardrails (Sprint 30)

Sprint 30 introduces production-grade budget enforcement with per-tenant and global limits:

#### Budget Configuration

```bash
# Global budgets
GLOBAL_BUDGET_DAILY=25.0
GLOBAL_BUDGET_MONTHLY=500.0

# Per-tenant defaults
TENANT_BUDGET_DAILY_DEFAULT=5.0
TENANT_BUDGET_MONTHLY_DEFAULT=100.0

# Enforcement thresholds
BUDGET_SOFT_THRESHOLD=0.8  # Throttle at 80%
BUDGET_HARD_THRESHOLD=1.0  # Deny at 100%
```

For per-tenant customization, create `config/budgets.yaml`:

```yaml
global:
  daily: 100.0
  monthly: 2000.0

tenants:
  premium-tenant:
    daily: 20.0
    monthly: 400.0

  trial-tenant:
    daily: 1.0
    monthly: 10.0
```

#### Cost Reports

View budget status and spend breakdown:

```bash
# Global report (last 30 days)
python scripts/cost_report.py

# Tenant-specific report
python scripts/cost_report.py --tenant tenant-1

# Custom time window
python scripts/cost_report.py --days 7

# JSON output
python scripts/cost_report.py --json > report.json
```

#### Dashboard Monitoring

The observability dashboard includes a **Cost Governance** panel showing:

- Global and per-tenant budget status
- Daily/monthly spend vs budgets
- Cost anomalies (statistical baseline detection)
- Recent governance events (throttles, denials, anomalies)

Access via: `streamlit run dashboards/app.py` → Observability tab

#### Budget Breach Runbook

When a tenant exceeds their budget:

1. **Immediate**: Jobs are denied and sent to DLQ (if worker integration enabled)
2. **Alert**: Check dashboard or governance events log
3. **Investigate**: Run cost report for the tenant
   ```bash
   python scripts/cost_report.py --tenant tenant-1 --days 7
   ```
4. **Resolution**:
   - Increase budget in `config/budgets.yaml` if legitimate usage
   - Review workflow efficiency if costs are unexpected
   - Contact tenant about usage patterns
5. **Recovery**: Replay DLQ jobs after budget reset
   ```bash
   # Replay budget-denied jobs
   python scripts/dlq_replay.py --reason budget_exceeded --tenant tenant-1
   ```

#### Anomaly Detection

Sprint 30 automatically detects unusual spending patterns using statistical baselines:

```bash
# View anomalies
python scripts/cost_report.py | grep "Cost Anomalies"

# Configure detection sensitivity
ANOMALY_SIGMA=3.0           # Standard deviations threshold
ANOMALY_MIN_DOLLARS=3.0     # Minimum spend to flag
ANOMALY_MIN_EVENTS=10       # Minimum baseline events
```

Anomalies are logged to `logs/governance_events.jsonl` for auditing.

#### Monthly Budget Reset

At the start of each month:

1. Review previous month's governance events
2. Adjust budgets based on usage trends
3. Replay any budget-denied DLQ jobs if appropriate
4. Update tenant quotas in `config/budgets.yaml`

See [COSTS.md](COSTS.md) for complete budget governance documentation.

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

## Autoscaling Operations

### Overview

Sprint 24 introduces dynamic autoscaling for the worker pool to optimize throughput, latency, and cost. The autoscaler analyzes queue depth, P95 latency, and worker utilization to make scaling decisions.

For comprehensive configuration and tuning details, see `docs/AUTOSCALING.md`.

### Monitoring Scaling Behavior

#### Key Metrics

Track these metrics to understand autoscaling behavior:

1. **Worker Count**
   ```python
   from src.scale.worker_pool import WorkerPool

   pool = WorkerPool.get_instance()
   stats = pool.get_stats()

   print(f"Total workers: {stats.total_workers}")
   print(f"Active workers: {stats.active_workers}")
   print(f"Idle workers: {stats.idle_workers}")
   ```

2. **Queue Metrics**
   ```python
   print(f"Queue depth: {stats.queue_depth}")
   print(f"Queue wait time: {calculate_avg_wait_time()}ms")
   ```

3. **Latency Metrics**
   ```python
   print(f"P95 latency: {get_p95_latency()}ms")
   print(f"Target: {os.getenv('TARGET_P95_LATENCY_MS', '2000')}ms")
   ```

4. **Scaling Events**
   ```bash
   # Monitor scaling decisions in logs
   tail -f logs/autoscaler.log | grep "Scale decision"
   ```

#### Observability Dashboard

Add autoscaling metrics to your monitoring dashboard:

```python
# Prometheus metrics example
worker_count_gauge.set(stats.total_workers)
queue_depth_gauge.set(stats.queue_depth)
p95_latency_gauge.set(calculate_p95_latency())
scale_up_counter.inc()  # When scaling up
scale_down_counter.inc()  # When scaling down
```

### Common Scaling Incidents

#### Incident: Worker Pool Saturated

**Symptoms:**
- Workers stuck at MAX_WORKERS
- Queue depth growing
- P95 latency exceeding target

**Diagnosis:**
```bash
# Check current state
python -c "
from src.scale.worker_pool import WorkerPool
pool = WorkerPool.get_instance()
stats = pool.get_stats()
print(f'Workers: {stats.total_workers}')
print(f'Queue: {stats.queue_depth}')
print(f'Max: {os.getenv(\"MAX_WORKERS\", \"12\")}')
"
```

**Resolution:**
```bash
# Short-term: Increase MAX_WORKERS
export MAX_WORKERS=24
# Restart service to apply

# Long-term: Optimize job performance or add more hosts
```

#### Incident: Queue Not Draining

**Symptoms:**
- Queue depth growing despite available workers
- Jobs failing repeatedly
- High failure rate in stats

**Diagnosis:**
```bash
# Check failure rate
python -c "
from src.scale.worker_pool import WorkerPool
pool = WorkerPool.get_instance()
stats = pool.get_stats()
total = stats.jobs_completed + stats.jobs_failed
failure_rate = stats.jobs_failed / total if total > 0 else 0
print(f'Failure rate: {failure_rate:.2%}')
print(f'Failed: {stats.jobs_failed}')
"
```

**Resolution:**
```bash
# 1. Check retry configuration
export MAX_RETRIES=2  # Reduce if jobs failing consistently

# 2. Check downstream service health
curl -I https://downstream-api.example.com/health

# 3. Review job logs for errors
tail -f logs/worker.log | grep ERROR
```

#### Incident: Scaling Thrashing

**Symptoms:**
- Workers rapidly scaling up and down
- High frequency of scale decisions
- Unstable worker count

**Diagnosis:**
```bash
# Count scale decisions per minute
grep "Scale decision" logs/autoscaler.log |
  tail -100 |
  awk '{print $1, $2}' |
  uniq -c
```

**Resolution:**
```bash
# Increase cooldown period
export SCALE_DECISION_INTERVAL_MS=3000

# Widen thresholds
export TARGET_QUEUE_DEPTH=100
export TARGET_P95_LATENCY_MS=5000

# Reduce scaling steps
export SCALE_UP_STEP=1
export SCALE_DOWN_STEP=1
```

#### Incident: High Latency Despite Capacity

**Symptoms:**
- P95 latency high
- Workers idle
- Queue shallow

**Diagnosis:**
```bash
# Profile job execution time
python -m cProfile -o profile.stats your_job_script.py
python -m pstats profile.stats

# Check downstream latency
curl -w "@curl-format.txt" -o /dev/null -s https://api.example.com/endpoint
```

**Resolution:**
- Optimize slow job functions
- Add database indexes
- Cache expensive operations
- Check downstream service latency
- Increase host resources (CPU, memory)

#### Incident: Workers Not Scaling Down

**Symptoms:**
- Load drops but workers remain at peak
- High idle worker percentage
- Unnecessary cost

**Diagnosis:**
```bash
# Check scale-down blockers
python -c "
import os
print(f'Current workers: {get_current_workers()}')
print(f'Min workers: {os.getenv(\"MIN_WORKERS\", \"1\")}')
print(f'Utilization: {get_utilization():.1%}')
print(f'Queue depth: {get_queue_depth()}')
print(f'Queue threshold (30%): {int(os.getenv(\"TARGET_QUEUE_DEPTH\", \"50\")) * 0.3}')
"
```

**Resolution:**
```bash
# Lower minimum if safe
export MIN_WORKERS=1

# Make scale-down more aggressive
export SCALE_DOWN_STEP=2

# Ensure scale-down conditions can be met
# Queue < 30% of target, latency < 50% of target, utilization < 70%
```

### Tuning for Cost vs Latency

#### Cost-Optimized Configuration

Minimize costs by scaling down aggressively:

```bash
export MIN_WORKERS=1                    # Scale to zero when idle
export MAX_WORKERS=12                   # Cap burst capacity
export TARGET_QUEUE_DEPTH=100           # Allow deeper queue
export TARGET_P95_LATENCY_MS=5000       # Relaxed latency
export SCALE_DOWN_STEP=2                # Fast scale-down
export SCALE_DECISION_INTERVAL_MS=3000  # Slower reactions
```

**Trade-offs:**
- Lower cost during idle periods
- Higher latency during ramp-up
- May miss latency SLAs during spikes

**Best for:**
- Background batch jobs
- Development/testing environments
- Non-critical workloads

#### Latency-Optimized Configuration

Minimize latency with warm workers:

```bash
export MIN_WORKERS=5                    # Always warm
export MAX_WORKERS=30                   # High burst capacity
export TARGET_QUEUE_DEPTH=10            # Minimal queuing
export TARGET_P95_LATENCY_MS=500        # Strict latency
export SCALE_UP_STEP=5                  # Fast scale-up
export SCALE_DOWN_STEP=1                # Conservative scale-down
export SCALE_DECISION_INTERVAL_MS=1000  # Quick reactions
```

**Trade-offs:**
- Higher cost (idle workers during off-peak)
- Low latency even during spikes
- Meets strict SLAs

**Best for:**
- User-facing interactive features
- Real-time approvals
- Chat interfaces

#### Balanced Configuration (Default)

Balance cost and latency:

```bash
export MIN_WORKERS=2                    # Small warm pool
export MAX_WORKERS=12                   # Moderate ceiling
export TARGET_QUEUE_DEPTH=50            # Moderate queue
export TARGET_P95_LATENCY_MS=2000       # Reasonable latency
export SCALE_UP_STEP=2                  # Standard scale-up
export SCALE_DOWN_STEP=1                # Conservative scale-down
```

**Trade-offs:**
- Reasonable cost
- Acceptable latency
- Suitable for mixed workloads

**Best for:**
- Production environments
- Mixed realtime + batch workloads
- General purpose

### Load Testing Guidance

#### Preparation

1. **Define load profile**
   ```python
   # Example: Ramp up from 0 to 100 jobs/sec over 5 minutes
   load_profile = {
       "initial_rate": 0,
       "target_rate": 100,
       "ramp_duration": 300,  # seconds
       "sustain_duration": 600,  # 10 minutes at peak
   }
   ```

2. **Configure monitoring**
   ```bash
   # Enable detailed logging
   export LOG_LEVEL=DEBUG
   export AUTOSCALER_LOG_LEVEL=INFO

   # Set up metrics collection
   export METRICS_EXPORT=true
   export METRICS_INTERVAL=10  # seconds
   ```

3. **Set test environment variables**
   ```bash
   # Use realistic production settings
   export MIN_WORKERS=2
   export MAX_WORKERS=20
   export TARGET_P95_LATENCY_MS=2000
   export TARGET_QUEUE_DEPTH=50
   ```

#### Running Load Tests

```bash
# 1. Start monitoring
python scripts/monitor_autoscaler.py &
MONITOR_PID=$!

# 2. Run load test
python scripts/load_test.py \
  --profile ramp_and_sustain \
  --duration 900 \
  --max-rate 100

# 3. Collect metrics
python scripts/export_metrics.py --output load_test_results.csv

# 4. Stop monitoring
kill $MONITOR_PID
```

#### Analyzing Results

Key metrics to review:

1. **Scale-up speed**
   ```bash
   # Time to reach target capacity
   grep "Scale decision: up" logs/autoscaler.log |
     head -1 |
     awk '{print $1, $2}'
   ```

2. **Latency under load**
   ```python
   import pandas as pd
   df = pd.read_csv("load_test_results.csv")
   print(f"P95 latency: {df['latency_ms'].quantile(0.95)}ms")
   print(f"Max latency: {df['latency_ms'].max()}ms")
   ```

3. **Queue behavior**
   ```python
   print(f"Max queue depth: {df['queue_depth'].max()}")
   print(f"Avg queue depth: {df['queue_depth'].mean()}")
   ```

4. **Cost efficiency**
   ```python
   worker_hours = df['worker_count'].sum() / 3600  # Convert to hours
   cost_per_job = (worker_hours * WORKER_COST_PER_HOUR) / df['jobs_completed'].sum()
   print(f"Cost per job: ${cost_per_job:.4f}")
   ```

#### Load Test Scenarios

**Scenario 1: Sustained High Load**
```python
# Test MAX_WORKERS capacity
load_test(rate=150, duration=600)  # 10 minutes at 150 jobs/sec
# Verify: Workers reach MAX_WORKERS, queue stable, latency acceptable
```

**Scenario 2: Burst Traffic**
```python
# Test scale-up speed
load_test(spike_rate=200, spike_duration=30)  # 30-second spike
# Verify: Scale-up within SCALE_DECISION_INTERVAL_MS, queue drains quickly
```

**Scenario 3: Gradual Ramp**
```python
# Test scaling stability
load_test(ramp_from=0, ramp_to=100, ramp_duration=600)
# Verify: Smooth scaling, no thrashing, latency within target
```

**Scenario 4: Load Drop**
```python
# Test scale-down behavior
load_test(high_load_duration=300, idle_duration=300)
# Verify: Scale-down to MIN_WORKERS, no premature scale-down
```

### Autoscaling Runbook

#### Daily Checks

```bash
# 1. Check worker pool health
python scripts/check_worker_health.py

# 2. Review scaling events
grep "Scale decision" logs/autoscaler-$(date +%Y-%m-%d).log | tail -20

# 3. Check for alerts
python scripts/check_autoscaler_alerts.py --since 24h
```

#### Weekly Review

```bash
# 1. Export metrics
python scripts/export_metrics.py --since 7d --output weekly_metrics.csv

# 2. Analyze scaling efficiency
python scripts/analyze_autoscaling.py --input weekly_metrics.csv

# 3. Review cost trends
python scripts/cost_report.py --since 7d

# 4. Tune configuration if needed
# Edit based on analysis
```

#### Configuration Changes

When updating autoscaling parameters:

```bash
# 1. Document current configuration
python scripts/dump_autoscaler_config.py > config_backup.json

# 2. Update environment variables
export TARGET_QUEUE_DEPTH=100  # Example change

# 3. Restart service
systemctl restart worker-pool

# 4. Monitor for 1 hour
watch -n 30 'python scripts/check_worker_health.py'

# 5. Rollback if issues
# source config_backup.sh
```

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
11. **Load test autoscaling** before production deployment
12. **Tune autoscaler gradually** based on observed metrics

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

### CI Artifacts

The CI workflow (`.github/workflows/ci.yml`) automatically uploads sprint logs and test artifacts for review:

- **Artifact name:** `sprint-logs-and-artifacts-py{version}`
- **Contents:**
  - All sprint completion logs (`*-COMPLETE.md`)
  - Audit reports
  - Test run metadata (from `runs/` directory)
- **Retention:** 90 days (GitHub default)
- **Access:** Download from Actions tab → Workflow run → Artifacts section

This makes it easy to review sprint progress and test results without cloning the repository.

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

## Templates

### Template Schema & Validation

Templates are YAML files that conform to `schemas/template.json`. Each template must include:

**Required Fields:**
- `name` (string): Human-readable template name
- `version` (string): Semantic version in "major.minor" format (e.g., "1.0")
- `description` (string): Brief description of template purpose
- `context` (enum): Output context - one of: `markdown`, `docx`, `html`
- `inputs` (array): List of input field definitions
- `rendering.body` (string): Jinja2 template source

**Input Field Schema:**
```yaml
inputs:
  - id: field_name           # Snake_case identifier
    label: Display Label     # User-facing label
    type: string             # One of: string, text, int, float, bool, enum, date, email, url, multiselect
    required: true           # Optional, default: false
    default: "value"         # Optional default value
    help: "Help text"        # Optional help tooltip
    placeholder: "hint"      # Optional placeholder
    validators:              # Optional validators
      min: 0                 # Min value (int/float) or length (string/text)
      max: 100               # Max value (int/float) or length (string/text)
      regex: "^[A-Z]+"       # Regex pattern for validation
      choices: ["a", "b"]    # Required for enum/multiselect types
```

**Example Template:**
```yaml
name: Sales Follow-up
version: "1.0"
description: Friendly follow-up email template
context: markdown

inputs:
  - id: recipient
    label: Recipient Name
    type: string
    required: true
    default: "Taylor"

  - id: priority
    label: Priority Level
    type: enum
    validators:
      choices: ["low", "medium", "high"]

rendering:
  body: |
    Dear {{recipient}},
    Priority: {{priority|upper}}
```

### Validation Behavior

**Load-time Validation:**
- Templates are validated against `schemas/template.json` when loaded
- Invalid templates are skipped with warnings logged to console
- Validation errors show file path and specific field errors

**Runtime Validation:**
- Input values are validated before rendering
- Validation errors displayed inline in UI
- Run/Preview buttons disabled until all errors resolved

**Common Validation Patterns:**
```yaml
# Email validation
- id: email
  type: email  # Auto-validates format

# URL validation
- id: website
  type: url    # Requires http:// or https://

# String length
- id: title
  type: string
  validators:
    min: 5
    max: 100

# Number range
- id: quantity
  type: int
  validators:
    min: 1
    max: 1000

# Pattern matching
- id: code
  type: string
  validators:
    regex: "^[A-Z]{3}-\d{4}$"
```

### Jinja2 Sandbox & Safety

Templates use a **sandboxed Jinja2 environment** for security:

**Auto-escaping:**
- `html` context: Auto-escapes all variables
- `docx` context: Auto-escapes all variables
- `markdown` context: No auto-escape (use `{{var|e}}` explicitly)

**Allowed Filters:**
- String: `lower`, `upper`, `title`, `replace`, `join`
- Numeric: `round`, `length`
- Safety: `escape`, `e`, `safe`
- Custom: `to_slug`, `to_title`
- Iteration: `map`, `select`, `default`

**Blocked:**
- File system access
- Attribute access (e.g., `__class__`)
- Unsafe filters and methods

**Examples:**
```jinja2
{# Safe in all contexts #}
Hello {{name|upper}}!

{# HTML context - auto-escaped #}
<div>{{user_input}}</div>

{# Markdown - explicit escape #}
User input: {{user_input|e}}

{# Custom filters #}
Slug: {{title|to_slug}}
Title: {{name|to_title}}
```

### Widget Type Mapping

The UI automatically renders appropriate Streamlit widgets based on input type:

| Type | Widget | Notes |
|------|--------|-------|
| `string` | `text_input` | Single-line text |
| `text` | `text_area` | Multi-line text |
| `int` | `number_input` | Enforces min/max |
| `float` | `number_input` | Decimal precision |
| `bool` | `checkbox` | True/False toggle |
| `enum` | `selectbox` | Single choice from list |
| `multiselect` | `multiselect` | Multiple choices |
| `date` | `date_input` | Date picker |
| `email` | `text_input` | With email validation |
| `url` | `text_input` | With URL validation |

Required fields are marked with `*` in the UI.

### Creating Custom Templates

1. Create a new YAML file in `templates/` or `templates/custom/`
2. Follow the schema documented above
3. Test validation: `python -c "from src.templates import list_templates; list_templates()"`
4. Reload Templates tab in UI to see new template

**Tips:**
- Use semantic versioning (increment on changes)
- Provide helpful `help` text for each input
- Test with various input values
- Use validators to enforce data quality
- Keep Jinja2 templates simple and readable

### Testing Templates

Run template tests:
```bash
# Schema validation tests
pytest -q tests/test_templates_schema.py

# Render safety tests
pytest -q tests/test_templates_render_safety.py

# Widget validation tests
pytest -q tests/test_templates_widgets.py
```

## Storage Lifecycle Management

### Overview

The storage lifecycle system manages artifacts across three tiers (hot/warm/cold) with automated promotion and retention policies. This section covers operational procedures for managing the storage lifecycle.

### Nightly Lifecycle Job Setup

#### Setting Up Cron Job

For automated nightly lifecycle management:

```bash
# Edit crontab
crontab -e

# Add lifecycle job to run daily at 2 AM
0 2 * * * cd /path/to/openai-agents-workflows-2025.09.28-v1 && /path/to/python scripts/lifecycle_run.py --live >> logs/lifecycle_cron.log 2>&1
```

#### Alternative: systemd Timer (Linux)

Create `/etc/systemd/system/lifecycle.service`:

```ini
[Unit]
Description=Storage Lifecycle Job
After=network.target

[Service]
Type=oneshot
User=app_user
WorkingDirectory=/path/to/openai-agents-workflows-2025.09.28-v1
ExecStart=/path/to/python scripts/lifecycle_run.py --live
StandardOutput=append:/var/log/lifecycle.log
StandardError=append:/var/log/lifecycle.log
```

Create `/etc/systemd/system/lifecycle.timer`:

```ini
[Unit]
Description=Run Storage Lifecycle Job Daily
Requires=lifecycle.service

[Timer]
OnCalendar=daily
OnCalendar=02:00
Persistent=true

[Install]
WantedBy=timers.target
```

Enable and start:

```bash
sudo systemctl enable lifecycle.timer
sudo systemctl start lifecycle.timer
sudo systemctl status lifecycle.timer
```

### Manual Lifecycle Drills

#### Pre-Deployment Testing

Before deploying to production, test lifecycle operations:

```bash
# 1. Generate test artifacts
python src/workflows/stress/archive_rotation_demo.py --tenant test_drill --count 100

# 2. Force aging to simulate time passing
python -c "
import sys; sys.path.insert(0, 'src')
from workflows.stress.archive_rotation_demo import ArchiveRotationDemo
demo = ArchiveRotationDemo('test_drill', 'drill')
demo.force_artifact_age('hot', days_old=10)
"

# 3. Dry run lifecycle job
python scripts/lifecycle_run.py --dry-run --verbose

# 4. Review output and execute if satisfactory
python scripts/lifecycle_run.py --live --verbose

# 5. Verify promotions
python scripts/lifecycle_run.py --summary
```

#### Monthly Restoration Drill

Practice artifact restoration procedures monthly:

```bash
# 1. List artifacts in warm tier
python scripts/restore_artifact.py --tenant production_tenant --from-tier warm --list

# 2. Select artifact for drill
# 3. Restore artifact
python scripts/restore_artifact.py \
  --tenant production_tenant \
  --workflow critical_workflow \
  --artifact sample_document.pdf \
  --from-tier warm \
  --to-tier hot

# 4. Verify restoration
python -c "
import sys; sys.path.insert(0, 'src')
from storage.tiered_store import artifact_exists
assert artifact_exists('hot', 'production_tenant', 'critical_workflow', 'sample_document.pdf')
print('✓ Restoration drill successful')
"
```

### Accidental Purge Recovery

#### Prevention

**CRITICAL**: Purged artifacts cannot be recovered. Implement these safeguards:

1. **Always dry-run first**:
   ```bash
   python scripts/lifecycle_run.py --dry-run
   ```

2. **Review before executing**:
   ```bash
   # Check what will be purged
   python -c "
   import sys, time; sys.path.insert(0, 'src')
   from storage.lifecycle import scan_tier_for_expired
   expired = scan_tier_for_expired('cold', max_age_days=90)
   print(f'Will purge {len(expired)} artifacts:')
   for a in expired[:10]:
       print(f'  - {a[\"tenant_id\"]}/{a[\"workflow_id\"]}/{a[\"artifact_id\"]}')
   "
   ```

3. **Backup before purge**:
   ```bash
   # Backup cold tier before purging
   tar -czf backups/cold_tier_$(date +%Y%m%d).tar.gz artifacts/cold/
   ```

#### If Purge Occurred

If artifacts were accidentally purged:

1. **Check audit log immediately**:
   ```bash
   # Find purge events
   grep "purged_from_cold" logs/lifecycle_events.jsonl | tail -20
   ```

2. **Restore from backup** (if available):
   ```bash
   # Extract backup
   tar -xzf backups/cold_tier_YYYYMMDD.tar.gz -C /tmp/

   # Copy specific artifacts back
   cp -r /tmp/artifacts/cold/tenant_id artifacts/cold/
   ```

3. **Re-generate artifacts** (if source data available):
   ```bash
   # Re-run workflow that generated the artifacts
   python src/workflows/weekly_report.py --tenant tenant_id --workflow workflow_id
   ```

4. **Document incident**:
   ```bash
   # Log to incident file
   echo "$(date): Accidental purge of tenant_id/workflow_id - restored from backup" >> logs/incidents.log
   ```

### Monitoring Storage Usage

#### Disk Space Monitoring

Set up alerts for storage thresholds:

```bash
#!/bin/bash
# monitor_storage.sh

# Get storage statistics
STORAGE_STATS=$(python -c "
import sys, json; sys.path.insert(0, 'src')
from storage.tiered_store import get_all_tier_stats
print(json.dumps(get_all_tier_stats()))
")

# Check hot tier size
HOT_SIZE_GB=$(echo "$STORAGE_STATS" | jq -r '.hot.total_bytes / 1073741824')

if (( $(echo "$HOT_SIZE_GB > 100" | bc -l) )); then
    echo "ALERT: Hot tier storage is ${HOT_SIZE_GB}GB (threshold: 100GB)"
    # Send alert via email/Slack/PagerDuty
fi
```

Run hourly via cron:

```bash
0 * * * * /path/to/monitor_storage.sh >> logs/storage_monitor.log 2>&1
```

#### Lifecycle Job Health Check

Monitor lifecycle job completion:

```bash
#!/bin/bash
# check_lifecycle_health.sh

LAST_JOB=$(python -c "
import sys, json; sys.path.insert(0, 'src')
from storage.lifecycle import get_last_lifecycle_job
job = get_last_lifecycle_job()
if job:
    print(json.dumps(job))
else:
    print('{\"error\": \"no_job_found\"}')
")

# Check if job ran recently (within 26 hours)
TIMESTAMP=$(echo "$LAST_JOB" | jq -r '.timestamp // empty')

if [ -z "$TIMESTAMP" ]; then
    echo "ALERT: No lifecycle job found in audit log"
    exit 1
fi

# Check for errors
ERRORS=$(echo "$LAST_JOB" | jq -r '.total_errors // 0')

if [ "$ERRORS" -gt 0 ]; then
    echo "ALERT: Last lifecycle job had $ERRORS errors"
    exit 1
fi

echo "✓ Lifecycle job health check passed"
```

### Adjusting Retention Policies

#### Per-Environment Configuration

Different environments may require different retention:

**Development**:
```bash
export HOT_RETENTION_DAYS=1
export WARM_RETENTION_DAYS=7
export COLD_RETENTION_DAYS=14
```

**Staging**:
```bash
export HOT_RETENTION_DAYS=3
export WARM_RETENTION_DAYS=14
export COLD_RETENTION_DAYS=30
```

**Production**:
```bash
export HOT_RETENTION_DAYS=7
export WARM_RETENTION_DAYS=30
export COLD_RETENTION_DAYS=90
```

#### Emergency Retention Extension

If you need to temporarily prevent purges:

```bash
# Extend cold retention to 365 days
export COLD_RETENTION_DAYS=365

# Run lifecycle job
python scripts/lifecycle_run.py --live

# Revert after emergency
unset COLD_RETENTION_DAYS
```

### Troubleshooting Common Issues

#### Issue: Lifecycle Job Hanging

**Symptoms**: Job runs for hours without completing

**Solutions**:
1. Check for filesystem issues:
   ```bash
   df -h artifacts/
   ls -la artifacts/hot/ artifacts/warm/ artifacts/cold/
   ```

2. Look for permission errors in logs:
   ```bash
   tail -100 logs/lifecycle_events.jsonl | grep error
   ```

3. Kill and restart with smaller batch:
   ```bash
   pkill -f lifecycle_run.py
   # Process one tier at a time
   python -c "from src.storage.lifecycle import promote_expired_to_warm; promote_expired_to_warm()"
   ```

#### Issue: Excessive Storage Growth

**Symptoms**: Hot tier consuming too much space

**Solutions**:
1. Check largest tenants:
   ```bash
   du -sh artifacts/hot/*/ | sort -h | tail -10
   ```

2. Reduce retention temporarily:
   ```bash
   export HOT_RETENTION_DAYS=3
   python scripts/lifecycle_run.py --live
   ```

3. Manually promote large artifacts:
   ```python
   from src.storage.tiered_store import list_artifacts, promote_artifact

   artifacts = list_artifacts('hot', tenant_id='large_tenant')
   for a in sorted(artifacts, key=lambda x: x['size_bytes'], reverse=True)[:100]:
       promote_artifact(
           tenant_id=a['tenant_id'],
           workflow_id=a['workflow_id'],
           artifact_id=a['artifact_id'],
           from_tier='hot',
           to_tier='warm'
       )
   ```

### Best Practices

#### Pre-Flight Checklist

Before running lifecycle job in production:

- [ ] Dry-run completed successfully
- [ ] Reviewed list of artifacts to be purged
- [ ] Verified recent backups exist
- [ ] Checked disk space availability
- [ ] Reviewed retention policies
- [ ] Scheduled during low-traffic period
- [ ] Team notified of maintenance window

#### Post-Execution Validation

After lifecycle job completes:

- [ ] Check exit code: `echo $?` (should be 0)
- [ ] Review summary: `python scripts/lifecycle_run.py --summary`
- [ ] Verify no errors: `grep error logs/lifecycle_events.jsonl | tail -20`
- [ ] Confirm expected promotions occurred
- [ ] Check storage usage decreased as expected

#### Audit Trail

Maintain comprehensive audit trail:

```bash
# Archive lifecycle logs monthly
tar -czf archives/lifecycle_logs_$(date +%Y%m).tar.gz logs/lifecycle_events.jsonl
gzip logs/lifecycle_events.jsonl
mv logs/lifecycle_events.jsonl.gz archives/

# Start new log
touch logs/lifecycle_events.jsonl
```

### Emergency Procedures

#### Halting Lifecycle Job

If lifecycle job is causing issues:

```bash
# Find process
ps aux | grep lifecycle_run.py

# Kill gracefully (allows cleanup)
kill <pid>

# Force kill if necessary
kill -9 <pid>
```

#### Rolling Back Promotions

To recover from incorrect promotions:

```bash
# 1. Identify incorrectly promoted artifacts from audit log
grep "promoted_to_warm" logs/lifecycle_events.jsonl | tail -50

# 2. Restore artifacts back to hot tier
python scripts/restore_artifact.py \
  --tenant tenant_id \
  --workflow workflow_id \
  --artifact artifact_id \
  --from-tier warm \
  --to-tier hot
```

## Checkpoint Approvals & DAG Resumption (Sprint 31)

### Overview

Sprint 31 introduces human-in-the-loop approvals via checkpoint tasks that pause DAG execution. This section covers operational procedures for managing pending checkpoints, resuming paused DAGs, and handling stuck or expired checkpoints.

For comprehensive checkpoint documentation, see [ORCHESTRATION.md](./ORCHESTRATION.md).

### Runbook: Resume a Paused DAG

When a DAG pauses at a checkpoint task, follow these steps to review, approve, and resume execution:

#### 1. Identify Paused DAG

When a DAG pauses, the run output shows:

```
DAG PAUSED AT CHECKPOINT
DAG Run ID: abc123_def456
Checkpoint ID: abc123_def456_approval_checkpoint
Message: Awaiting approval: Approve weekly report draft?
```

**Important**: Save the `dag_run_id` for resumption.

#### 2. List Pending Checkpoints

View all pending checkpoints:

```bash
python scripts/approvals.py list
```

**Output:**
```
Pending Checkpoints
===================
abc123_def456_approval_checkpoint
  Prompt: Approve weekly report draft?
  Required Role: Operator
  Created: 2025-10-03 14:30:00 UTC
  Expires: 2025-10-06 14:30:00 UTC
  DAG Run: abc123_def456
```

Filter by tenant:
```bash
python scripts/approvals.py list --tenant tenant-a
```

#### 3. Review Checkpoint Details

Check the checkpoint's required role and inputs:

```bash
python scripts/approvals.py show abc123_def456_approval_checkpoint
```

Verify your user role allows approval:
```bash
echo $USER_RBAC_ROLE
# Should be Operator or Admin for Operator checkpoints
```

#### 4. Approve or Reject

**To approve:**

```bash
# Set role if not already set
export USER_RBAC_ROLE=Operator

# Approve with optional data
python scripts/approvals.py approve abc123_def456_approval_checkpoint \
  --kv signoff_text="Approved by manager" priority=high
```

**To reject:**

```bash
python scripts/approvals.py reject abc123_def456_approval_checkpoint \
  --reason "Budget concerns - needs revision"
```

#### 5. Resume DAG Execution

After approval, resume the DAG using the saved `dag_run_id`:

```bash
python scripts/run_dag_min.py \
  --dag configs/dags/weekly_ops_chain.approval.yaml \
  --resume abc123_def456
```

**Output:**
```
Resuming DAG run abc123_def456...
DAG RESUMED & COMPLETED
DAG Run ID: abc123_def456
Status: success
Tasks Succeeded: 3
Duration: 2.34s
```

#### 6. Verify Completion

Check orchestrator events log:

```bash
# View events for this DAG run
grep "abc123_def456" logs/orchestrator_events.jsonl | tail -10
```

Expected events:
- `checkpoint_pending` - Checkpoint created
- `checkpoint_approved` - Checkpoint approved
- `dag_done` - DAG completed successfully

#### Troubleshooting

**Resume fails with "Checkpoint not approved":**
- Verify checkpoint status: `python scripts/approvals.py list`
- Ensure checkpoint is in `approved` status
- Check if checkpoint expired

**Permission denied on approval:**
- Check current role: `echo $USER_RBAC_ROLE`
- Set appropriate role: `export USER_RBAC_ROLE=Admin`
- Verify role hierarchy: Viewer < Operator < Admin

**DAG run ID not found:**
- Verify exact spelling of run ID
- Check state store: `grep "resume_token" logs/orchestrator_state.jsonl`

### Runbook: Handle Stuck or Expired Checkpoints

Checkpoints may become stuck due to expiration or other issues. This runbook covers recovery procedures.

#### Automatic Expiration

Checkpoints automatically expire after `APPROVAL_EXPIRES_H` hours (default: 72).

**Check expiration setting:**
```bash
echo $APPROVAL_EXPIRES_H
# Default: 72 hours
```

**View recently expired checkpoints:**
```bash
python scripts/approvals.py list --status expired
```

#### Detecting Stuck Checkpoints

**List long-pending checkpoints:**

```bash
# Checkpoints pending for more than 48 hours
python -c "
import sys; sys.path.insert(0, 'src')
from datetime import datetime, timedelta, UTC
from src.orchestrator.checkpoints import list_checkpoints

pending = list_checkpoints(status='pending')
threshold = datetime.now(UTC) - timedelta(hours=48)

for cp in pending:
    created = datetime.fromisoformat(cp['created_at'])
    if created < threshold:
        age_hours = (datetime.now(UTC) - created).total_seconds() / 3600
        print(f'{cp[\"checkpoint_id\"]}: pending for {age_hours:.1f} hours')
"
```

#### Manual Expiration

Force expiration of specific checkpoints:

```bash
python -c "
import sys; sys.path.insert(0, 'src')
from datetime import datetime, UTC
from src.orchestrator.checkpoints import expire_pending

# Expire all checkpoints older than expiration threshold
now = datetime.now(UTC)
expired = expire_pending(now)

print(f'Expired {len(expired)} checkpoints:')
for cp in expired:
    print(f'  - {cp[\"checkpoint_id\"]}')
"
```

#### Recovering from Expired Checkpoints

When a checkpoint expires, the DAG cannot be resumed. Options:

**Option 1: Re-run DAG from start**

```bash
python scripts/run_dag_min.py \
  --dag configs/dags/weekly_ops_chain.approval.yaml
```

**Option 2: Override expiration (emergency only)**

```bash
# Temporarily disable expiration
export APPROVAL_EXPIRES_H=99999

# Approve checkpoint
python scripts/approvals.py approve <checkpoint_id>

# Resume DAG
python scripts/run_dag_min.py --dag <path> --resume <dag_run_id>

# Restore normal expiration
unset APPROVAL_EXPIRES_H
```

**Option 3: Manual checkpoint manipulation (last resort)**

```bash
# Edit checkpoints.jsonl to change status
# WARNING: Only use if other options fail

# 1. Backup checkpoint file
cp logs/checkpoints.jsonl logs/checkpoints.jsonl.backup

# 2. Find checkpoint event
grep "checkpoint_id_here" logs/checkpoints.jsonl

# 3. Manually append approval event
# (Requires understanding of JSONL format and event structure)
```

#### Monitoring Checkpoint Health

**Dashboard view:**

```bash
streamlit run dashboards/app.py
```

Navigate to **Observability** → **✅ Checkpoint Approvals** to view:
- Pending checkpoints count
- Expiring soon warnings (within 6 hours)
- Recent approvals/rejections/expirations

**CLI monitoring:**

```bash
# Count pending by status
python -c "
import sys; sys.path.insert(0, 'src')
from src.orchestrator.checkpoints import list_checkpoints

pending = list_checkpoints(status='pending')
approved = list_checkpoints(status='approved')
rejected = list_checkpoints(status='rejected')
expired = list_checkpoints(status='expired')

print(f'Pending: {len(pending)}')
print(f'Approved: {len(approved)}')
print(f'Rejected: {len(rejected)}')
print(f'Expired: {len(expired)}')
"
```

#### Preventing Stuck Checkpoints

**Best practices:**

1. **Set appropriate expiration**: Adjust `APPROVAL_EXPIRES_H` based on approval SLA
   ```bash
   export APPROVAL_EXPIRES_H=48  # 2 days for critical workflows
   ```

2. **Monitor pending checkpoints daily**: Add to daily ops checks
   ```bash
   python scripts/approvals.py list | grep "Pending Checkpoints"
   ```

3. **Set up alerts**: Alert if pending count exceeds threshold
   ```bash
   # Alert if more than 5 pending checkpoints
   PENDING_COUNT=$(python -c "
   import sys; sys.path.insert(0, 'src')
   from src.orchestrator.checkpoints import list_checkpoints
   print(len(list_checkpoints(status='pending')))
   ")

   if [ "$PENDING_COUNT" -gt 5 ]; then
       echo "ALERT: $PENDING_COUNT pending checkpoints"
       # Send notification
   fi
   ```

4. **Enable scheduler auto-expiration**: Ensure scheduler is running to auto-expire old checkpoints
   ```bash
   python -m src.orchestrator.scheduler --serve
   ```

### Runbook: Approvals Audit Trail

Maintain comprehensive audit of all checkpoint approval decisions for compliance and debugging.

#### Audit Log Location

All checkpoint events are logged to:
- **Checkpoints**: `logs/checkpoints.jsonl`
- **State store events**: `logs/orchestrator_state.jsonl`

#### Query Recent Approvals

**Last 20 approvals:**

```bash
grep "checkpoint_approved" logs/checkpoints.jsonl | tail -20
```

**Approvals by specific user/role:**

```bash
grep "checkpoint_approved" logs/checkpoints.jsonl | grep "Admin" | tail -10
```

**Approvals for specific tenant:**

```bash
grep "checkpoint_approved" logs/checkpoints.jsonl | grep "tenant-a" | tail -10
```

#### Query Rejections

**All rejections with reasons:**

```bash
grep "checkpoint_rejected" logs/checkpoints.jsonl | \
  jq -r '[.checkpoint_id, .rejected_by, .reject_reason] | @tsv'
```

**Recent rejections:**

```bash
grep "checkpoint_rejected" logs/checkpoints.jsonl | tail -10
```

#### Query Expirations

**Expired checkpoints:**

```bash
grep "checkpoint_expired" logs/checkpoints.jsonl | tail -20
```

**Expiration events from scheduler:**

```bash
grep "checkpoint_expired" logs/orchestrator_state.jsonl | tail -20
```

#### Generate Audit Report

Create summary report for specific date range:

```bash
python -c "
import sys, json
from datetime import datetime, timedelta

sys.path.insert(0, 'src')

# Load events
with open('logs/checkpoints.jsonl', 'r') as f:
    events = [json.loads(line) for line in f]

# Filter last 7 days
cutoff = datetime.now().timestamp() - (7 * 86400)
recent = [e for e in events if datetime.fromisoformat(e['timestamp']).timestamp() > cutoff]

# Count by event type
approved = [e for e in recent if e.get('event') == 'checkpoint_approved']
rejected = [e for e in recent if e.get('event') == 'checkpoint_rejected']
expired = [e for e in recent if e.get('event') == 'checkpoint_expired']

print(f'Checkpoint Audit Report (Last 7 Days)')
print(f'=====================================')
print(f'Approved: {len(approved)}')
print(f'Rejected: {len(rejected)}')
print(f'Expired: {len(expired)}')
print(f'Total: {len(recent)}')
print()
print(f'Approvals by Role:')
for role in set(e.get('approved_by') for e in approved if e.get('approved_by')):
    count = sum(1 for e in approved if e.get('approved_by') == role)
    print(f'  {role}: {count}')
"
```

#### Export Audit Log

Export to CSV for analysis:

```bash
python -c "
import sys, json, csv
sys.path.insert(0, 'src')

# Load checkpoint events
with open('logs/checkpoints.jsonl', 'r') as f:
    events = [json.loads(line) for line in f]

# Write to CSV
with open('audit_checkpoints.csv', 'w', newline='') as csvfile:
    fieldnames = ['timestamp', 'event', 'checkpoint_id', 'dag_run_id', 'tenant', 'approved_by', 'rejected_by', 'reject_reason']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames, extrasaction='ignore')

    writer.writeheader()
    for event in events:
        writer.writerow(event)

print('Exported to audit_checkpoints.csv')
"
```

#### Retention Policy

**Recommended retention:**
- **Hot logs** (current): 90 days
- **Archived logs**: 2 years
- **Compliance logs**: Per regulatory requirements (e.g., 7 years)

**Archive old logs:**

```bash
# Archive logs older than 90 days
python -c "
import json, gzip
from datetime import datetime, timedelta

cutoff = (datetime.now() - timedelta(days=90)).isoformat()

# Read all events
with open('logs/checkpoints.jsonl', 'r') as f:
    events = [json.loads(line) for line in f]

# Separate old and recent
old = [e for e in events if e['timestamp'] < cutoff]
recent = [e for e in events if e['timestamp'] >= cutoff]

# Archive old events
with gzip.open(f'logs/archives/checkpoints_{datetime.now().strftime(\"%Y%m%d\")}.jsonl.gz', 'wt') as f:
    for event in old:
        f.write(json.dumps(event) + '\n')

# Keep only recent in active log
with open('logs/checkpoints.jsonl', 'w') as f:
    for event in recent:
        f.write(json.dumps(event) + '\n')

print(f'Archived {len(old)} events, retained {len(recent)}')
"
```

#### Compliance Queries

**All approvals for specific DAG run:**

```bash
DAG_RUN_ID="abc123"
grep "$DAG_RUN_ID" logs/checkpoints.jsonl | \
  jq -r 'select(.event == "checkpoint_approved" or .event == "checkpoint_rejected")'
```

**Approval timeline for audit:**

```bash
CHECKPOINT_ID="abc123_approval"
grep "$CHECKPOINT_ID" logs/checkpoints.jsonl | \
  jq -r '[.timestamp, .event, .approved_by // .rejected_by // "system"] | @tsv'
```

**Approvers list (RBAC audit):**

```bash
grep "checkpoint_approved" logs/checkpoints.jsonl | \
  jq -r '.approved_by' | sort | uniq -c | sort -rn
```

### Emergency Contacts

For checkpoint approval issues requiring escalation:

- **Operator role**: Team lead or shift manager
- **Admin role**: Platform admin or on-call engineer
- **Expired checkpoints**: Re-run DAG or contact workflow owner
- **System issues**: Check scheduler health and logs

## Template Version Rollback (Sprint 32)

### When to Rollback

Rollback to a prior template version when:
- New version has validation bugs
- Schema changes break existing DAGs
- Performance regression detected
- Incorrect workflow logic introduced

### Rollback Procedure

**Scenario:** Template `weekly_report` v2.0.0 has issues, need to rollback to v1.0.0

#### Step 1: Verify Prior Version Exists

```bash
# Show all versions
python scripts/templates.py list | grep weekly_report

# Expected output:
# weekly_report        2.0.0      active       Author      ...
# weekly_report        1.0.0      deprecated   Author      ...
```

#### Step 2: Deprecate Bad Version

```bash
python scripts/templates.py deprecate \
  --name weekly_report \
  --version 2.0.0 \
  --reason "Validation bug in schema - rolling back to 1.0.0"
```

This marks v2.0.0 as deprecated but keeps it in registry for audit trail.

#### Step 3: Re-activate Prior Version

The registry doesn't have an "activate" command, but you can update DAGs to explicitly use v1.0.0:

**Option A:** Update DAGs to pin to v1.0.0

```yaml
# Before (used latest active = 2.0.0)
params:
  template_name: weekly_report
  # No version specified = latest active

# After (explicit version)
params:
  template_name: weekly_report
  template_version: "1.0.0"
```

**Option B:** Register v1.0.0 as v2.0.1 (recommended)

```bash
# Copy v1.0.0 files to v2.0.1
cp templates/registry/weekly_report_1.0.yaml templates/registry/weekly_report_2.0.1.yaml
cp templates/schemas/weekly_report_1.0.schema.json templates/schemas/weekly_report_2.0.1.schema.json

# Register as new version
python scripts/templates.py register \
  --name weekly_report \
  --version 2.0.1 \
  --file templates/registry/weekly_report_2.0.1.yaml \
  --schema templates/schemas/weekly_report_2.0.1.schema.json \
  --tags "professional,stable"
```

Now v2.0.1 (which is v1.0.0 logic) becomes latest active.

#### Step 4: Verify Rollback

```bash
# Check latest active version
python scripts/templates.py show --name weekly_report

# Should show v2.0.1 (or v1.0.0 if using Option A)

# Test with DAG
python scripts/run_dag_min.py --dag configs/dags/weekly_ops_chain.templates.yaml --dry-run
```

#### Step 5: Notify Users

If templates are shared across team:

```bash
# Email or Slack notification
Subject: Template Rollback - weekly_report v2.0.0 → v2.0.1

We've rolled back weekly_report to v2.0.1 due to a validation bug in v2.0.0.

Action Required:
- DAGs using explicit "template_version: 2.0.0" should update to "2.0.1"
- DAGs without version specified will automatically use v2.0.1

Issue: Schema validation was rejecting valid start_date values
Fixed: v2.0.1 restores v1.0.0 schema (known good)
```

## Compliance Operations (Sprint 33A)

Sprint 33A introduces GDPR-style compliance operations for tenant data lifecycle management.

### Runbook: Export Tenant Data

**Purpose**: Create complete export bundle of tenant data for audit, backup, or regulatory request

**Prerequisites**:
- User role: Auditor, Compliance, or Admin
- Tenant ID
- Output directory with write permissions

**Procedure**:

1. **Set environment**:
   ```bash
   export USER_RBAC_ROLE=Auditor  # Or Compliance/Admin
   ```

2. **Create export directory**:
   ```bash
   mkdir -p exports
   ```

3. **Run export**:
   ```bash
   python scripts/compliance.py export \
     --tenant acme-corp \
     --out ./exports
   ```

4. **Verify export bundle**:
   ```bash
   cd exports/acme-corp-export-2025-10-03
   cat manifest.json
   ls -lh
   ```

**Expected output**:
```
acme-corp-export-2025-10-03/
├── manifest.json              # Export summary with counts
├── artifacts.json             # Artifact references
├── orchestrator_events.jsonl  # DAG execution logs
├── queue_events.jsonl         # Queue activity
├── cost_events.jsonl          # Cost tracking
├── approval_events.jsonl      # Approvals/checkpoints
└── governance_events.jsonl    # Governance audit
```

**Troubleshooting**:
- **RBAC denied**: Check `USER_RBAC_ROLE` is Auditor+
- **Empty counts**: Verify tenant ID is correct
- **Missing files**: Check data paths in environment variables

**Retention**: Store export bundles securely for 2+ years (compliance)

---

### Runbook: Delete Tenant Data

**Purpose**: Permanently remove all tenant-scoped data for GDPR right-to-erasure or tenant offboarding

**Prerequisites**:
- User role: Compliance or Admin (NOT Auditor)
- Tenant ID
- **CRITICAL**: Export tenant data FIRST (backup)
- Verify no active legal hold

**Procedure**:

1. **Check for legal hold**:
   ```bash
   python scripts/compliance.py holds --list | jq -r '.holds[] | select(.tenant == "acme-corp")'
   ```
   - If hold exists, release first or contact legal team

2. **Export data (REQUIRED)**:
   ```bash
   python scripts/compliance.py export --tenant acme-corp --out ./exports
   ```

3. **Dry-run deletion** (verify scope):
   ```bash
   export USER_RBAC_ROLE=Compliance
   python scripts/compliance.py delete --tenant acme-corp --dry-run
   ```

4. **Review dry-run output**:
   ```json
   {
     "tenant": "acme-corp",
     "dry_run": true,
     "counts": {
       "artifacts": 45,
       "orch_events": 120,
       "queue_events": 80,
       "cost_events": 100,
       "approval_events": 15,
       "gov_events": 25
     },
     "total_items": 385
   }
   ```

5. **Confirm counts** match expected tenant footprint

6. **Execute deletion**:
   ```bash
   python scripts/compliance.py delete --tenant acme-corp
   ```

7. **Verify deletion**:
   ```bash
   # Check artifact directories
   ls artifacts/hot/ | grep acme-corp  # Should be empty

   # Check event logs
   grep "acme-corp" logs/orchestrator_events.jsonl | tail -1
   # Should show deletion timestamp
   ```

**Exit codes**:
- `0` - Success
- `2` - RBAC denied
- `3` - Legal hold active (must release first)
- `1` - Other error

**Troubleshooting**:
- **Exit code 3 (legal hold)**: Release hold first with `python scripts/compliance.py release --tenant acme-corp`
- **RBAC denied**: Requires Compliance or Admin role (Auditor cannot delete)
- **Partial deletion**: Re-run deletion command (idempotent)

**Post-deletion**:
1. Archive export bundle to secure storage
2. Document deletion in governance log
3. Notify stakeholders if required

---

### Runbook: Apply Legal Hold

**Purpose**: Prevent deletion of tenant data for litigation, audit, or regulatory investigation

**Prerequisites**:
- User role: Compliance or Admin
- Tenant ID
- Hold reason (case number, requestor, purpose)

**Procedure**:

1. **Set environment**:
   ```bash
   export USER_RBAC_ROLE=Compliance
   ```

2. **Apply hold with detailed reason**:
   ```bash
   python scripts/compliance.py hold \
     --tenant acme-corp \
     --reason "Litigation hold - Case #2025-1234, Filed 2025-10-03, Requestor: Legal Dept"
   ```

3. **Verify hold active**:
   ```bash
   python scripts/compliance.py holds --list
   ```

4. **Document hold in tracking system**:
   - Case management system
   - Legal hold register
   - Compliance database

5. **Notify relevant teams**:
   - Operations team (no deletions allowed)
   - Backup team (retain all backups)
   - Data team (freeze data modifications)

**Hold audit log**:
```json
{
  "timestamp": "2025-10-03T22:40:00Z",
  "event": "hold_applied",
  "tenant": "acme-corp",
  "reason": "Litigation hold - Case #2025-1234"
}
```

**Monitoring**:
```bash
# Active holds
tail -f logs/legal_holds.jsonl

# Deletion attempts while on hold
grep "legal hold" logs/governance_events.jsonl
```

---

### Runbook: Release Legal Hold

**Purpose**: Remove legal hold after case closure, investigation complete, or retention period expired

**Prerequisites**:
- User role: Compliance or Admin
- Tenant ID
- Authorization from legal/compliance team
- Hold release documentation

**Procedure**:

1. **Verify hold exists**:
   ```bash
   python scripts/compliance.py holds --list | jq -r '.holds[] | select(.tenant == "acme-corp")'
   ```

2. **Obtain release authorization**:
   - Legal counsel approval
   - Case closure documentation
   - Retention period verification

3. **Release hold**:
   ```bash
   export USER_RBAC_ROLE=Compliance
   python scripts/compliance.py release --tenant acme-corp
   ```

4. **Verify hold released**:
   ```bash
   python scripts/compliance.py holds --list | jq -r '.holds[] | select(.tenant == "acme-corp")'
   # Should return nothing
   ```

5. **Document release**:
   - Update case management system
   - Note in legal hold register
   - File release authorization

**Hold release audit log**:
```json
{
  "timestamp": "2025-11-15T14:00:00Z",
  "event": "hold_released",
  "tenant": "acme-corp"
}
```

**Post-release actions**:
- Resume normal retention policies
- Allow deletion if needed
- Archive hold documentation

---

### Runbook: Retention Enforcement

**Purpose**: Automated pruning of old data per retention policies

**Schedule**: Daily at 2 AM (recommended)

**Prerequisites**:
- User role: Compliance or Admin
- Configured retention policies (env vars)

**Procedure (Manual)**:

1. **Set environment**:
   ```bash
   export USER_RBAC_ROLE=Compliance
   ```

2. **Run retention enforcement**:
   ```bash
   python scripts/compliance.py retention
   ```

3. **Review output**:
   ```json
   {
     "enforced_at": "2025-10-03T22:45:00Z",
     "counts": {
       "RETAIN_ORCH_EVENTS_DAYS": 15,
       "RETAIN_QUEUE_EVENTS_DAYS": 8,
       "RETAIN_COST_EVENTS_DAYS": 3,
       "RETAIN_GOV_EVENTS_DAYS": 0,
       "RETAIN_CHECKPOINTS_DAYS": 2
     },
     "total_purged": 28
   }
   ```

4. **Verify purge**:
   ```bash
   # Check event log sizes
   wc -l logs/*.jsonl

   # Verify oldest remaining events
   head -1 logs/orchestrator_events.jsonl | jq -r '.timestamp'
   ```

**Automated Schedule (Cron)**:

```bash
# Add to crontab
crontab -e

# Daily at 2 AM
0 2 * * * cd /path/to/repo && USER_RBAC_ROLE=Compliance python scripts/compliance.py retention >> logs/retention.log 2>&1
```

**Automated Schedule (Windows Task Scheduler)**:

```powershell
$action = New-ScheduledTaskAction -Execute "python" -Argument "scripts\compliance.py retention" -WorkingDirectory "C:\path\to\repo"
$trigger = New-ScheduledTaskTrigger -Daily -At 2am
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable
Register-ScheduledTask -TaskName "ComplianceRetention" -Action $action -Trigger $trigger -Settings $settings
```

**Retention policy configuration**:

```bash
# In .env or environment
RETAIN_ORCH_EVENTS_DAYS=90      # Orchestrator events
RETAIN_QUEUE_EVENTS_DAYS=60     # Queue activity
RETAIN_DLQ_DAYS=30              # Dead letter queue
RETAIN_CHECKPOINTS_DAYS=90      # Approvals/checkpoints
RETAIN_COST_EVENTS_DAYS=180     # Cost tracking (6 months)
RETAIN_GOV_EVENTS_DAYS=365      # Governance (1 year)
```

**Monitoring retention**:

```bash
# Retention run history
grep "retention_enforced" logs/governance_events.jsonl | tail -10

# Alert on large purges (potential issue)
PURGED=$(python scripts/compliance.py retention | jq -r '.total_purged')
if [ "$PURGED" -gt 1000 ]; then
  echo "ALERT: Large retention purge - $PURGED items"
fi
```

**Troubleshooting**:
- **No items purged**: Retention windows may be too long
- **RBAC denied**: Requires Compliance or Admin role
- **File errors**: Check write permissions on log files

---

### Compliance Checklist

**Weekly**:
- [ ] Review active legal holds
- [ ] Monitor export requests
- [ ] Check deletion operations
- [ ] Review retention runs

**Monthly**:
- [ ] Audit compliance role assignments
- [ ] Review retention policies
- [ ] Archive old export bundles
- [ ] Test disaster recovery procedures

**Quarterly**:
- [ ] Legal hold audit
- [ ] Compliance report generation
- [ ] Policy review and updates
- [ ] Staff training on procedures

**Annually**:
- [ ] Full compliance audit
- [ ] Policy recertification
- [ ] Archive review and cleanup
- [ ] Disaster recovery test

---

## Encryption & Classification Operations (Sprint 33B)

### 6. Rotate Encryption Key

**When to run**:
- Every 90 days (per `KEY_ROTATION_DAYS` policy)
- Immediately after suspected key compromise
- Before major audit or compliance review

**Prerequisites**:
- Backup current keyring: `cp logs/keyring.jsonl logs/keyring.jsonl.bak`
- Verify backup exists and is valid

**Procedure**:

```bash
# 1. Check current key status
python scripts/keyring.py active

# 2. Note current key_id and age
KEY_AGE=$(python -c "from datetime import datetime; import json; k=json.loads(open('logs/keyring.jsonl').readlines()[-1]); print((datetime.now()-datetime.fromisoformat(k['created_at'].rstrip('Z'))).days)")
echo "Current key age: $KEY_AGE days"

# 3. Rotate key
python scripts/compliance.py rotate-key > rotation_result.json

# 4. Verify new key is active
python scripts/keyring.py list | grep active

# 5. Test encryption with new key
echo "test content" > /tmp/test_artifact.md
python -c "from pathlib import Path; from src.storage.secure_io import write_encrypted, read_encrypted; write_encrypted(Path('/tmp/test.md'), b'test', 'Internal', 'test-tenant'); print(read_encrypted(Path('/tmp/test.md'), 'Internal'))"

# 6. Verify old key can still decrypt
# (Read artifacts encrypted with previous key)

# 7. Update monitoring/alerts for new key rotation date
```

**Expected Output**:

```json
{
  "event": "key_rotated",
  "new_key": {
    "key_id": "key-002",
    "alg": "AES256-GCM",
    "status": "active",
    "created_at": "2025-10-03T12:00:00Z"
  }
}
```

**Troubleshooting**:

- **Rotation fails**: Check keyring file permissions, verify JSONL format
- **Old key still active**: Keyring append failed, check disk space
- **Cannot decrypt old artifacts**: Key retired incorrectly, restore from backup

**Post-rotation**:
- Monitor governance events for key usage
- Verify dashboard shows new key_id
- Schedule next rotation: `date -d "+90 days"`

### 7. Label Classification for Artifact

**When to run**:
- Before exporting tenant data with `REQUIRE_LABELS_FOR_EXPORT=true`
- When artifact sensitivity changes
- During compliance audit preparation

**Prerequisites**:
- Artifact exists in storage
- Appropriate clearance for labeling operation

**Procedure**:

```bash
# 1. View current label (if any)
python scripts/classification.py show \
  --path artifacts/hot/tenant-a/report.md

# 2. Determine appropriate label
# Review artifact content and sensitivity
# Consult classification guide (CLASSIFICATION.md)

# 3. Set label
python scripts/classification.py set-label \
  --path artifacts/hot/tenant-a/report.md \
  --label Confidential

# 4. Verify label applied
python scripts/classification.py show \
  --path artifacts/hot/tenant-a/report.md | jq .label
```

**Expected Output**:

```json
{
  "artifact": "artifacts/hot/tenant-a/report.md",
  "label": "Confidential",
  "sidecar": "artifacts/hot/tenant-a/report.md.json"
}
```

**Bulk Labeling**:

```bash
# Label all artifacts in a directory
for artifact in artifacts/hot/tenant-a/*.md; do
  python scripts/classification.py set-label \
    --path "$artifact" \
    --label Internal
done
```

### 8. Export with Classification Policies

**When to run**:
- GDPR data subject access request
- Compliance audit requiring tenant data
- Tenant offboarding

**Prerequisites**:
- Set appropriate `USER_CLEARANCE` for requester
- Configure `REQUIRE_LABELS_FOR_EXPORT` policy
- Configure `EXPORT_POLICY` (deny or redact)

**Procedure**:

```bash
# 1. Configure export policy
export USER_CLEARANCE=Confidential
export REQUIRE_LABELS_FOR_EXPORT=true
export EXPORT_POLICY=deny  # or redact

# 2. Check for legal hold (same as before)
python scripts/compliance.py holds --list | jq -r '.holds[] | select(.tenant == "acme-corp")'

# 3. Export tenant data
export USER_RBAC_ROLE=Auditor
python scripts/compliance.py export \
  --tenant acme-corp \
  --out ./exports \
  > export_result.json

# 4. Review export summary
cat export_result.json | jq .

# 5. Check governance log for denials
grep "export_denied" logs/governance_events.jsonl | \
  jq -r 'select(.tenant == "acme-corp")'

# 6. If denials occurred, review and escalate clearance if needed
```

**Expected Output**:

```json
{
  "tenant": "acme-corp",
  "export_date": "2025-10-03T12:00:00Z",
  "counts": {
    "artifacts": 42,
    "artifacts_denied": 3,
    "orch_events": 150,
    ...
  }
}
```

**Handling Denials**:

```bash
# Option 1: Increase clearance (requires authorization)
export USER_CLEARANCE=Restricted

# Option 2: Use redact policy (includes metadata)
export EXPORT_POLICY=redact

# Option 3: Review denied artifacts individually
grep "export_denied" logs/governance_events.jsonl | \
  jq -r 'select(.tenant == "acme-corp") | .artifact'
```

### 9. Recover from Lost Keyring

**When to run**:
- Keyring file corrupted or deleted
- Disaster recovery scenario
- Migration to new environment

**Prerequisites**:
- Recent backup of `logs/keyring.jsonl`
- List of encrypted artifacts requiring recovery

**Procedure**:

```bash
# 1. Verify keyring is missing or corrupted
cat logs/keyring.jsonl | jq . || echo "Keyring corrupted"

# 2. Restore from backup
cp backups/keyring.jsonl.$(date +%Y%m%d) logs/keyring.jsonl

# 3. Validate restored keyring
python scripts/keyring.py list | jq .

# 4. Test decryption with each key
for key_id in $(python scripts/keyring.py list | jq -r '.keys[].key_id'); do
  echo "Testing $key_id..."
  # Find artifacts encrypted with this key
  grep -r "\"key_id\": \"$key_id\"" artifacts/ | head -1
done

# 5. Verify current active key
python scripts/keyring.py active

# 6. If no backup available:
#    - Plaintext artifacts remain accessible
#    - Encrypted artifacts are unrecoverable
#    - Create new keyring and re-encrypt going forward
python scripts/keyring.py rotate  # Creates new keyring if missing
```

**Data Loss Prevention**:

- **Automated backups**: `crontab -e`
  ```cron
  0 0 * * * cp /path/to/logs/keyring.jsonl /path/to/backups/keyring.jsonl.$(date +\%Y\%m\%d)
  ```
- **Off-site backup**: Sync backups to S3, GCS, or Azure Blob
- **Monitoring**: Alert on keyring file changes or deletions

### 10. Re-encrypt Backlog (Optional)

**When to run**:
- After key compromise (rotate then re-encrypt)
- Migrating from plaintext to encrypted storage
- Upgrading encryption algorithm

**Note**: Bulk re-encryption tool not implemented in Sprint 33B (future enhancement).

**Manual Re-encryption**:

```bash
# For critical artifacts only
for artifact in artifacts/hot/tenant-a/*.md; do
  # Read with old key
  data=$(python -c "from pathlib import Path; from src.storage.secure_io import read_encrypted; print(read_encrypted(Path('$artifact'), 'Admin').decode())")

  # Write with new key (post-rotation)
  python -c "from pathlib import Path; from src.storage.secure_io import write_encrypted; write_encrypted(Path('$artifact'), b'$data', 'Confidential', 'tenant-a')"
done
```

---

### Encryption & Classification Checklist

**Weekly**:
- [ ] Review security dashboard for key rotation status
- [ ] Check governance log for unexpected export denials
- [ ] Verify keyring backups are current

**Monthly**:
- [ ] Audit artifact labeling completeness
- [ ] Review clearance assignments
- [ ] Test key rotation procedure (non-prod)
- [ ] Verify encryption enabled for new artifacts

**Quarterly**:
- [ ] Rotate encryption key (if policy requires)
- [ ] Review classification policy effectiveness
- [ ] Audit export denials and escalations
- [ ] Test keyring recovery from backup

**Annually**:
- [ ] Full encryption audit
- [ ] Review and update classification labels
- [ ] Test disaster recovery (key loss scenario)
- [ ] Recertify clearance levels for all users

---

## Connector Operations (Sprint 35A)

### Connector Health Monitoring

**Daily Health Check:**

```bash
# List all connectors with status
python scripts/connectors_health.py list
```

**Drill into specific connector:**

```bash
# Get detailed metrics and recent failures
python scripts/connectors_health.py drill <connector_id>
```

**Dashboard Review:**
- Navigate to **Observability → Connectors** panel
- Check for ⚠️ degraded or 🚨 down connectors
- Monitor circuit breaker states (🟢/🟡/🔴)

### Runbook: Connector Down

**Symptoms:**
- Error rate > 50%
- Circuit breaker open (🔴)
- Health CLI shows 🚨 down

**Procedure:**

1. **Identify Root Cause**
   ```bash
   python scripts/connectors_health.py drill <connector_id>
   tail -n 50 logs/connectors/metrics.jsonl | grep "<connector_id>"
   ```

2. **Check Circuit Breaker**
   ```bash
   cat logs/connectors/circuit_state.jsonl | grep "<connector_id>" | tail -1
   ```
   - Wait for cooldown (default: 60s)
   - Circuit auto-transitions to half-open
   - Monitor recovery

3. **OAuth Token Check** (if applicable)
   ```bash
   cat logs/connectors/tokens.jsonl | grep "<connector_id>" | tail -1
   ```
   - Verify token not expired
   - Trigger refresh if needed
   - See `docs/CONNECTOR_OBSERVABILITY.md` for details

4. **Retry Tuning** (if transient failures)
   ```bash
   export RETRY_MAX_ATTEMPTS=5
   export RETRY_CAP_MS=120000
   export RETRY_BASE_MS=1000
   ```

5. **Manual Circuit Reset** (emergency only)
   ```bash
   # Backup state
   cp logs/connectors/circuit_state.jsonl logs/connectors/circuit_state.jsonl.backup

   # Remove connector entries
   grep -v "<connector_id>" logs/connectors/circuit_state.jsonl > temp.jsonl
   mv temp.jsonl logs/connectors/circuit_state.jsonl
   ```

**Escalation:** If unresolved after 30 minutes, open incident and notify platform team.

### Alerting Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| P95 Latency | > 2000ms | > 5000ms |
| Error Rate | > 10% | > 50% |
| Circuit State | Half-Open | Open |
| Zero Calls | 15 min | 30 min |

### See Also

- [CONNECTOR_OBSERVABILITY.md](./CONNECTOR_OBSERVABILITY.md) - Metrics, health, circuit breaker
- [CONNECTOR_SDK.md](./CONNECTOR_SDK.md) - Connector development guide
- [COMPLIANCE.md](./COMPLIANCE.md) - Complete compliance documentation
- [CLASSIFICATION.md](./CLASSIFICATION.md) - Data classification guide
- [ENCRYPTION.md](./ENCRYPTION.md) - Envelope encryption guide
- [TEMPLATE_REGISTRY.md](./TEMPLATE_REGISTRY.md) - Template registry documentation
- [ORCHESTRATION.md](./ORCHESTRATION.md) - Complete checkpoint documentation
- [SECURITY.md](./SECURITY.md) - RBAC role hierarchy and permissions
- [STORAGE.md](./STORAGE.md) - Comprehensive storage documentation
