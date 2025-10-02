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

## Creating Custom Templates

### Step 1: Clone Existing Template

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
