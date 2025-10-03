# Templates Catalog

Comprehensive guide to creating and using DJP Workflow templates.

## Overview

Templates enable you to define reusable workflows with type-safe inputs, validation, and structured outputs. The system supports:

- **JSON Schema validation** for inputs
- **Sandboxed Jinja2 rendering** for safety
- **Type-aware UI widgets** (string, int, email, enum, etc.)
- **Version control** and artifact tagging
- **Cost projection** and budget guards
- **Template cloning** to custom directory
- **Human-in-the-loop approvals**

## Built-in Templates

### 1. Simple Q&A Template
**File:** `templates/simple-qa.yaml`
**Purpose:** Basic question-answering with customizable context

**Inputs:**
- `question` (string, required)
- `context` (string, optional)

**Use Case:** Quick responses, FAQ handling

### 2. Research Summary Template
**File:** `templates/research-summary.yaml`
**Purpose:** Comprehensive research with citation requirements

**Inputs:**
- `topic` (string, required)
- `depth` (enum: shallow/moderate/deep)
- `citation_count` (integer, 3-10)

**Use Case:** Academic research, policy analysis

### 3. Content Generation Template
**File:** `templates/content-generation.yaml`
**Purpose:** Blog posts, articles, marketing copy

**Inputs:**
- `title` (string, required)
- `tone` (enum: formal/casual/technical)
- `word_count` (integer, 300-3000)

**Use Case:** Content marketing, documentation

### 4. Code Review Template
**File:** `templates/code-review.yaml`
**Purpose:** Automated code review with style checks

**Inputs:**
- `code_snippet` (text, required)
- `language` (enum: python/javascript/java/go)
- `focus` (enum: bugs/style/performance)

**Use Case:** Pull request reviews, code quality checks

## Example Templates

The `templates/examples/` directory contains three real-world workflow templates demonstrating professional, academic, and personal use cases.

### Weekly Report Template

**File:** `templates/examples/weekly_report.yaml`

**Purpose:** Generate professional weekly status reports for teams and stakeholders.

**Structure:**

```yaml
workflow_name: weekly_report
description: Generate weekly status report from team activities and metrics

prompt_template: |
  You are a professional business analyst. Generate a comprehensive weekly status report.

  **Report Period:** {start_date} to {end_date}
  **Context:** {context}

  **Required Sections:**
  1. Executive Summary (2-3 sentences)
  2. Key Accomplishments (bullet points)
  3. Metrics & KPIs (quantified where possible)
  4. Challenges & Blockers (with mitigation plans)
  5. Next Week Priorities (top 3-5 items)
  6. Action Items (owner, deadline)

parameters:
  max_tokens: 2000
  temperature: 0.5
  model: gpt-4o
```

**Variables:**
- `{start_date}` - Report start date (e.g., "2025-10-01")
- `{end_date}` - Report end date (e.g., "2025-10-07")
- `{context}` - Team activities, metrics, and updates

**Usage:**

```bash
# Command-line
python -m src.run_workflow \
  --template weekly_report \
  --inputs '{"start_date": "2025-10-01", "end_date": "2025-10-07", "context": "Sprint 25 completed..."}'

# Python API
from src.templates import load_template, render_template_inputs
from src.run_workflow import run_djp_workflow

template = load_template("weekly_report")
task = render_template_inputs(template, {
    "start_date": "2025-10-01",
    "end_date": "2025-10-07",
    "context": "Sprint 25 completed with 15 story points..."
})

artifact = run_djp_workflow(task=task, allowed_models=["openai/gpt-4o"])
```

**Output:** Structured Markdown report (800-1200 words) with executive summary, accomplishments, metrics, challenges, priorities, and action items.

**Best For:** Project managers, team leads, executives needing consistent weekly updates.

### Meeting Brief Template

**File:** `templates/examples/meeting_brief.yaml`

**Purpose:** Summarize meeting transcripts and extract actionable items for academic and professional settings.

**Structure:**

```yaml
workflow_name: meeting_brief
description: Summarize meeting transcript and extract actionable items

prompt_template: |
  You are an academic meeting facilitator. Analyze this meeting transcript and create a concise brief.

  **Meeting Title:** {meeting_title}
  **Date:** {meeting_date}
  **Attendees:** {attendees}
  **Transcript:** {transcript}

  **Required Sections:**
  1. Meeting Overview (1-2 sentences)
  2. Key Discussion Points (bullet points)
  3. Decisions Made (bullet points)
  4. Action Items (table format: Item | Owner | Deadline)
  5. Follow-up Questions (bullet points)

parameters:
  max_tokens: 1500
  temperature: 0.3
  model: gpt-4o-mini
```

**Variables:**
- `{meeting_title}` - Meeting name (e.g., "Sprint Planning")
- `{meeting_date}` - Date of meeting (e.g., "2025-10-02")
- `{attendees}` - Comma-separated attendee names
- `{transcript}` - Full meeting transcript text

**Usage:**

```bash
# Command-line
python -m src.run_workflow \
  --template meeting_brief \
  --inputs '{"meeting_title": "Sprint Planning", "meeting_date": "2025-10-02", "attendees": "Alice, Bob, Charlie", "transcript": "..."}'

# Python API
template = load_template("meeting_brief")
task = render_template_inputs(template, {
    "meeting_title": "Sprint Planning",
    "meeting_date": "2025-10-02",
    "attendees": "Alice, Bob, Charlie",
    "transcript": "Alice: Let's review the backlog..."
})
```

**Output:** Structured Markdown brief (500-800 words) with overview, discussion points, decisions, action items table, and follow-up questions.

**Best For:** Academic meetings, faculty discussions, research group syncs, professional team meetings.

### Inbox Sweep Template

**File:** `templates/examples/inbox_sweep.yaml`

**Purpose:** Prioritize tasks from email inbox and cloud drive files for personal productivity.

**Structure:**

```yaml
workflow_name: inbox_sweep
description: Prioritize tasks from email inbox and cloud drive files

prompt_template: |
  You are a personal productivity assistant. Analyze these inbox items and drive files, then prioritize them.

  **Inbox Items ({item_count} total):** {inbox_items}
  **Recent Drive Files ({file_count} total):** {drive_files}
  **User Context:**
  Current priorities: {user_priorities}
  Deadlines: {upcoming_deadlines}

  **Priority Levels:**
  - P0: Critical/Blocking (do today)
  - P1: High priority (do this week)
  - P2: Medium priority (do next week)
  - P3: Low priority (defer or delegate)

  **Required Sections:**
  1. Quick Summary (top 3 urgent items)
  2. P0 Tasks (critical items)
  3. P1 Tasks (high priority)
  4. P2 Tasks (medium priority)
  5. P3 Tasks (low priority/deferred)
  6. Suggested Automations
  7. Delegation Opportunities

parameters:
  max_tokens: 2500
  temperature: 0.4
  model: gpt-4o
```

**Variables:**
- `{inbox_items}` - List of email subjects and snippets
- `{drive_files}` - List of recent file names and modified dates
- `{user_priorities}` - Current focus areas (e.g., "Sprint 25, Q4 planning")
- `{upcoming_deadlines}` - Key deadlines to consider
- `{item_count}` - Number of inbox items (auto-calculated)
- `{file_count}` - Number of drive files (auto-calculated)

**Usage:**

```bash
# Command-line
python -m src.run_workflow \
  --template inbox_sweep \
  --inputs '{"inbox_items": "Email 1..., Email 2...", "drive_files": "Q4-plan.docx, budget.xlsx", "user_priorities": "Sprint 25", "upcoming_deadlines": "Q4 kickoff Oct 15"}'

# Python API
template = load_template("inbox_sweep")
task = render_template_inputs(template, {
    "inbox_items": "1. RE: Budget approval needed\n2. Invitation: Team sync",
    "drive_files": "1. Q4-plan.docx (modified 2 days ago)\n2. budget.xlsx (modified today)",
    "user_priorities": "Sprint 25 completion, Q4 planning",
    "upcoming_deadlines": "Q4 kickoff Oct 15, budget due Oct 10"
})
```

**Output:** Structured Markdown prioritization (1000-1500 words) with quick summary, P0-P3 task lists, automation suggestions, and delegation opportunities.

**Best For:** Knowledge workers, executives, academics managing email and document backlogs.

## Template Structure Deep Dive

### YAML Format

All templates follow this structure:

```yaml
# Required fields
workflow_name: unique_template_name
description: Brief description of template purpose

# Prompt template with variable substitution
prompt_template: |
  Your instructions here.
  Use {variable_name} for substitution.

  **Section Headers** for structure
  - Bullet points
  - More structure

# Optional: Sections for structured output
sections:
  - section_name_1
  - section_name_2

# Optional: Parameters override defaults
parameters:
  max_tokens: 2000
  temperature: 0.5
  model: gpt-4o

# Optional: Metadata for cataloging
metadata:
  category: professional  # or academic, personal
  output_format: markdown  # or docx, html
  typical_length: 800-1200 words
```

### Required Fields

| Field | Type | Description |
|-------|------|-------------|
| `workflow_name` | string | Unique identifier (snake_case) |
| `description` | string | Brief description for UI display |
| `prompt_template` | string | Jinja2 template with variables |

### Prompt Template Variables

Variables use Jinja2 syntax: `{variable_name}`

**Built-in variables:**
- Standard substitution: `{variable_name}`
- Conditionals: `{% if condition %}...{% endif %}`
- Loops: `{% for item in list %}...{% endfor %}`
- Filters: `{variable|upper}`, `{variable|lower}`

**Example with conditionals:**

```yaml
prompt_template: |
  Task: {task_description}

  {% if include_citations %}
  Please include citations for all claims.
  {% endif %}

  {% if priority == "high" %}
  This is urgent - focus on speed over depth.
  {% else %}
  Take time to be thorough and detailed.
  {% endif %}
```

### Parameter Configuration

Override default workflow parameters:

```yaml
parameters:
  # Model selection
  model: gpt-4o              # or gpt-4o-mini, gpt-4

  # Token limits
  max_tokens: 2000           # Max output tokens

  # Sampling parameters
  temperature: 0.5           # 0.0 (deterministic) to 2.0 (creative)
  top_p: 1.0                 # Nucleus sampling threshold

  # Advanced
  presence_penalty: 0.0      # Discourage repetition
  frequency_penalty: 0.0     # Discourage token frequency
```

**Parameter guidelines:**
- **Temperature 0.0-0.3:** Factual, deterministic (reports, summaries)
- **Temperature 0.4-0.7:** Balanced creativity (emails, briefs)
- **Temperature 0.8-1.5:** Creative writing (brainstorming, fiction)
- **Max tokens 500-1000:** Short responses (briefs, Q&A)
- **Max tokens 1000-2000:** Medium responses (reports, analyses)
- **Max tokens 2000+:** Long-form content (articles, comprehensive reports)

## How to Create New Workflow Templates

### Method 1: Start from Example

Copy an existing template and modify:

```bash
# Copy an example template
cp templates/examples/weekly_report.yaml templates/custom/my_template.yaml

# Edit the template
# Windows:
notepad templates/custom/my_template.yaml
# macOS/Linux:
nano templates/custom/my_template.yaml
```

Edit these fields:
1. `workflow_name` - Change to unique name (e.g., `quarterly_review`)
2. `description` - Update to match your use case
3. `prompt_template` - Customize instructions and variables
4. `parameters` - Adjust model, tokens, temperature
5. `metadata` - Update category and output format

### Method 2: Start from Scratch

Create a new YAML file in `templates/custom/`:

```yaml
workflow_name: my_custom_workflow
description: Brief description of what this workflow does

prompt_template: |
  You are a [role]. [Task description].

  **Input:** {input_variable}

  **Instructions:**
  - Instruction 1
  - Instruction 2
  - Instruction 3

  **Required Sections:**
  1. Section 1
  2. Section 2
  3. Section 3

parameters:
  max_tokens: 1500
  temperature: 0.5
  model: gpt-4o-mini

metadata:
  category: professional
  output_format: markdown
```

### Method 3: Clone via UI (Coming Soon)

1. Navigate to Templates tab
2. Select a base template
3. Click "+ Clone Template"
4. Enter new name and description
5. Template saved to `templates/custom/{slug}.yaml`

### Step 2: Edit Template YAML

Template structure:

```yaml
name: My Custom Template
version: "1.0"
description: Brief description of template purpose
context: markdown  # or docx

inputs:
  - id: field_name
    label: Display Name
    type: string  # string, integer, email, url, enum, text
    required: true
    help: Optional help text

  - id: category
    label: Category
    type: enum
    required: true
    enum:
      - option1
      - option2
      - option3

rendering:
  body: |
    # {{field_name}}

    Your template content here using Jinja2 syntax.

    {% if category == "option1" %}
    Conditional content
    {% endif %}
```

### Step 3: Use Template

1. Select template from dropdown
2. Fill in required inputs (validation runs automatically)
3. Preview (optional) to see rendered output
4. Check "Require Approval" if needed
5. Click "Run via DJP"
6. Approve/reject if approval workflow enabled

## Input Types

| Type | Widget | Validation | Example |
|------|--------|------------|---------|
| `string` | Text input | Max length | Name, title |
| `integer` | Number input | Min/max range | Count, score |
| `email` | Email input | RFC 5322 | user@example.com |
| `url` | URL input | Valid URL | https://example.com |
| `enum` | Dropdown | Fixed options | Category, status |
| `text` | Text area | Max length | Long description |

## Advanced Features

### Versioning

Templates support semantic versioning:
- **Minor version bump** on clone (1.0 → 1.1)
- **Version tracking** in artifacts
- **Rollback support** (keep old template versions)

### Cost Guards

Set budget limits per run:

```yaml
cost_guards:
  max_cost_usd: 0.50
  warn_threshold_usd: 0.30
```

### Batch Processing

Process multiple inputs from CSV:

```bash
python -m src.batch \
  --template my-template \
  --input batch.csv \
  --output results/ \
  --max-cost 5.00
```

### Approval Workflow

Enable human review before publishing:

1. Check "Require Approval" in UI
2. Run completes with `pending_approval` status
3. Review output preview
4. Click "✅ Approve & Publish" or "❌ Reject"
5. Status updates to `published` or `advisory_only`

## Best Practices for Prompts

### 1. Be Specific and Structured

**Bad:**
```yaml
prompt_template: |
  Write a report about {topic}.
```

**Good:**
```yaml
prompt_template: |
  You are a business analyst. Write a professional report about {topic}.

  **Structure:**
  1. Executive Summary (2-3 sentences)
  2. Key Findings (3-5 bullet points)
  3. Recommendations (numbered list)
  4. Conclusion (1 paragraph)

  **Tone:** Professional, data-driven
  **Length:** 500-800 words
```

### 2. Provide Clear Role and Context

Start prompts with a clear role definition:
- "You are a professional business analyst..."
- "You are an academic researcher..."
- "You are a technical writer..."
- "You are a personal productivity assistant..."

### 3. Use Section Headers

Structure output with clear section requirements:
```yaml
**Required Sections:**
1. Overview
2. Analysis
3. Recommendations
```

### 4. Specify Output Format

Be explicit about formatting:
- "Format in Markdown with headers and bullet points"
- "Use table format: Column1 | Column2 | Column3"
- "Number all items and sub-items"

### 5. Set Constraints

Define boundaries:
- "Keep response under 500 words"
- "Include at least 3 examples"
- "Cite all sources using [Source Title] format"

### 6. Handle Edge Cases

Use conditionals for flexible behavior:
```yaml
{% if priority == "urgent" %}
Focus on speed over depth. Provide quick actionable insights.
{% else %}
Take time to provide thorough analysis with supporting data.
{% endif %}
```

## Testing Templates with Dry-Run Mode

### Basic Dry-Run

Test templates without making API calls:

```bash
# Test weekly report template
python -m src.run_workflow \
  --template weekly_report \
  --dry-run

# Expected output:
# Dry run mode - no API calls made
# Projected cost: $0.004
# Projected tokens: ~500
# Template renders successfully
```

### Test with Sample Inputs

```bash
# Test meeting brief with sample data
python -m src.run_workflow \
  --template meeting_brief \
  --inputs '{"meeting_title": "Test Meeting", "meeting_date": "2025-10-02", "attendees": "Alice, Bob", "transcript": "Sample transcript..."}' \
  --dry-run
```

### Validate Template Structure

```bash
# Run schema validation
python -c "
from src.templates import load_template
template = load_template('my_custom_workflow')
print(f'Template loaded: {template.workflow_name}')
print(f'Parameters: {template.parameters}')
"
```

### Test Rendering

```bash
# Test template rendering with variables
python -c "
from src.templates import load_template, render_template_inputs

template = load_template('weekly_report')
task = render_template_inputs(template, {
    'start_date': '2025-10-01',
    'end_date': '2025-10-07',
    'context': 'Test context'
})
print(task[:200])  # Print first 200 chars
"
```

## Template Best Practices

### 1. Input Validation
- Always set `required: true` for critical fields
- Provide clear `help` text for complex inputs
- Use `enum` for fixed option sets
- Set reasonable min/max ranges for integers

### 2. Security
- Never include API keys or secrets in templates
- Use sandboxed Jinja2 filters only
- Validate all user inputs
- Enable redaction for PII-sensitive outputs

### 3. Performance
- Keep template complexity reasonable
- Use caching for repeated renders
- Set cost guards to prevent budget overruns
- Monitor metrics in Observability tab

### 4. Maintainability
- Use clear, descriptive names
- Document inputs in `help` fields
- Version templates semantically
- Archive old templates when superseded

### 5. Prompt Engineering
- Start with role definition
- Use section headers for structure
- Specify output format explicitly
- Set constraints (length, tone, style)
- Handle edge cases with conditionals
- Provide examples in the prompt

### 6. Cost Management
- Use `gpt-4o-mini` for simple tasks
- Reserve `gpt-4o` for complex analysis
- Set `max_tokens` appropriately
- Lower `temperature` for consistent output
- Test with dry-run before production use

## Template Gallery Features

### Search and Filter
- Search by name or description
- Filter by version
- Sort by creation date or usage

### Tags (Coming Soon)
- Categorize templates by use case
- Filter by tags in UI
- Auto-tag based on inputs

### Usage Metrics
- Track run count per template
- Monitor success/failure rates
- View average cost per run
- Identify most-used templates

## Troubleshooting

### Template Fails Validation
- Check YAML syntax (use yamllint)
- Verify all `required` fields have valid types
- Ensure `enum` values match exactly
- Validate Jinja2 syntax

### Rendering Errors
- Check variable names match input IDs
- Use safe Jinja2 filters only
- Handle missing optional fields with defaults
- Test with preview before running

### Cost Overruns
- Set `max_cost_usd` in cost guards
- Reduce `max_tokens` in template config
- Use faster models (gpt-4o-mini vs gpt-4o)
- Enable fastpath for simple queries

### Approval Workflow Issues
- Ensure template has approval checkbox
- Check artifact status in History tab
- Verify approver has UI access
- Review rejection reasons in artifacts

## API Usage

### Programmatic Template Execution

```python
from src.templates import list_templates, render_template_inputs
from src.run_workflow import run_djp_workflow

# List available templates
templates = list_templates()

# Select template
template = next(t for t in templates if t.name == "My Template")

# Render with inputs
result = render_template_inputs(template, {
    "field_name": "Example",
    "category": "option1"
})

# Run DJP workflow
artifact = run_djp_workflow(
    task=result,
    allowed_models=["openai/gpt-4o"],
    require_approval=False
)
```

### Batch Processing API

```python
from src.batch import process_batch_csv

# Process CSV with template
results = process_batch_csv(
    template_name="my-template",
    input_csv="inputs.csv",
    max_cost_usd=10.00,
    require_approval=False
)

# Save results
for result in results:
    print(f"Row {result['row_id']}: {result['status']}")
```

## Next Steps

1. Explore built-in templates in the Templates tab
2. Clone a template and customize for your use case
3. Test with preview before running at scale
4. Enable approval workflow for critical outputs
5. Monitor usage and costs in Observability tab
6. Share successful templates with your team

## Resources

- [Template Schema Reference](schemas/template.json)
- [Jinja2 Documentation](https://jinja.palletsprojects.com/)
- [Batch Processing Guide](OPERATIONS.md#batch-processing)
- [Approval Workflow Guide](2025.10.01-1200-TEMPLATES-S4-COMPLETE.md)
