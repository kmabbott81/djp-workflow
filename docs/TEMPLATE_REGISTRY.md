# Template Registry (Sprint 32)

Versioned template system with parameter schemas for safe, repeatable workflow execution.

## Overview

The Template Registry provides:
- **Versioned templates** with semantic versioning (1.0.0, 1.1.0, 2.0.0)
- **Parameter schemas** with validation, defaults, and type checking
- **RBAC enforcement** for template authoring (Author/Admin roles)
- **Deprecation tracking** for safe template evolution
- **DAG integration** for template-based workflows

## Quick Start

### 1. Register a Template

```bash
python scripts/templates.py register \
  --name my_workflow \
  --version 1.0.0 \
  --file templates/registry/my_workflow_1.0.yaml \
  --schema templates/schemas/my_workflow_1.0.schema.json \
  --tags "productivity,automation"
```

**Required files:**

**Template YAML** (`my_workflow_1.0.yaml`):
```yaml
workflow_ref: inbox_drive_sweep
description: My workflow description

prompt_template: |
  Your instructions here with {variable} substitution.

parameters:
  max_tokens: 2000
  temperature: 0.5
  model: gpt-4o-mini
```

**Schema JSON** (`my_workflow_1.0.schema.json`):
```json
{
  "fields": {
    "variable": {
      "type": "string",
      "required": true,
      "description": "Variable description"
    },
    "optional_var": {
      "type": "int",
      "required": false,
      "default": 10,
      "min": 1,
      "max": 100
    }
  }
}
```

### 2. List Templates

```bash
# List all templates
python scripts/templates.py list

# Filter by owner
python scripts/templates.py list --owner Author

# Filter by tag
python scripts/templates.py list --tag productivity

# Filter by status
python scripts/templates.py list --status active
```

### 3. Show Template Details

```bash
# Show latest version
python scripts/templates.py show --name my_workflow

# Show specific version
python scripts/templates.py show --name my_workflow --version 1.0.0
```

### 4. Use in DAG

```yaml
tasks:
  - id: task1
    type: workflow
    workflow_ref: template
    params:
      template_name: my_workflow
      template_version: "1.0.0"
      variable: "user value"
      # optional_var will use default (10)
    depends_on: []
```

### 5. Deprecate Old Versions

```bash
python scripts/templates.py deprecate \
  --name my_workflow \
  --version 1.0.0 \
  --reason "Superseded by 2.0.0 with improved schema"
```

## Registry Concepts

### Versioning

Templates follow semantic versioning:
- **Major version** (1.0.0 → 2.0.0): Breaking schema changes
- **Minor version** (1.0.0 → 1.1.0): New optional fields, non-breaking
- **Patch version** (1.0.0 → 1.0.1): Bug fixes, no schema changes

### Ownership

Templates are owned by the user who registered them (based on `USER_RBAC_ROLE` at registration time).

### Tags

Templates can be tagged for categorization:
- `productivity` - Personal productivity workflows
- `professional` - Business/work workflows
- `academic` - Research and education workflows
- `automation` - Automated background tasks

### Status

Templates have two statuses:
- **active**: Available for use (default)
- **deprecated**: Marked for retirement (still usable but discouraged)

### JSONL Storage

Registry uses append-only JSONL format:
- **File**: `templates/registry/templates.jsonl`
- **Format**: One JSON record per line
- **Last-wins semantics**: Latest record for each template_id is authoritative
- **Audit trail**: All updates preserved in log

## Parameter Schemas

### Schema Format

```json
{
  "fields": {
    "field_name": {
      "type": "string|int|float|bool|enum",
      "required": true|false,
      "default": value,
      "description": "Help text",
      "enum": ["option1", "option2"],  // For enum type
      "min": number,  // For int/float
      "max": number   // For int/float
    }
  }
}
```

### Supported Types

| Type | Python Type | Validation | Example |
|------|-------------|------------|---------|
| `string` | str | Type check | "Hello" |
| `int` | int | Type + bounds | 42 |
| `float` | float | Type + bounds | 3.14 |
| `bool` | bool | Type check | true |
| `enum` | str | Must be in enum list | "option1" |

### Type-Specific Validation

**Integer bounds:**
```json
{
  "count": {
    "type": "int",
    "min": 1,
    "max": 100,
    "default": 10
  }
}
```

**Enum options:**
```json
{
  "priority": {
    "type": "enum",
    "enum": ["low", "medium", "high"],
    "default": "medium"
  }
}
```

**Optional with default:**
```json
{
  "timeout": {
    "type": "int",
    "required": false,
    "default": 30
  }
}
```

### Validation Flow

1. User provides params: `{"count": 5, "priority": "high"}`
2. Schema validator checks:
   - All provided params exist in schema
   - Required params are present
   - Types match (int, string, etc.)
   - Values within bounds (min/max)
   - Enum values in allowed list
3. Defaults applied for missing optional params
4. Resolved params returned: `{"count": 5, "priority": "high", "timeout": 30}`

## RBAC for Templates

### Roles

Template operations require specific roles:

| Operation | Required Role | Can Be Performed By |
|-----------|---------------|---------------------|
| Register | Author | Author, Admin |
| Deprecate | Author | Author, Admin |
| List | Viewer | Everyone |
| Show | Viewer | Everyone |
| Use in DAG | Viewer | Everyone |

### Setting User Role

```bash
# Set via environment variable
export USER_RBAC_ROLE=Author

# Or inline
USER_RBAC_ROLE=Author python scripts/templates.py register ...
```

### Role Hierarchy

```
Viewer (level 0) < Author (level 1) < Operator (level 2) < Admin (level 3)
```

Admin can perform all operations.

### Permission Errors

```bash
$ USER_RBAC_ROLE=Viewer python scripts/templates.py register --name test --version 1.0 --file test.yaml
Permission denied: Template registration requires Author role, but user has Viewer
```

Exit code 2 indicates permission error.

## Deprecation

### Why Deprecate?

- Superseded by newer version
- Schema changed incompatibly
- Workflow reference no longer valid
- Security or correctness issues

### Deprecation Process

1. Register new version (e.g., 2.0.0)
2. Deprecate old version (e.g., 1.0.0)
3. Update DAGs to use new version
4. Monitor usage (old version still works but discouraged)

### Example

```bash
# Register v2
python scripts/templates.py register \
  --name my_workflow \
  --version 2.0.0 \
  --file templates/registry/my_workflow_2.0.yaml \
  --schema templates/schemas/my_workflow_2.0.schema.json

# Deprecate v1
python scripts/templates.py deprecate \
  --name my_workflow \
  --version 1.0.0 \
  --reason "Use 2.0.0 with improved validation"

# Old DAGs using 1.0.0 still work
# New DAGs should use 2.0.0
```

### Latest Active Version

When no version specified, system returns latest **active** version:

```bash
# Returns 2.0.0 (latest active)
python scripts/templates.py show --name my_workflow

# Returns 1.0.0 (specific version, even if deprecated)
python scripts/templates.py show --name my_workflow --version 1.0.0
```

## Environment Variables

```bash
# Template registry path (default: templates/registry)
TEMPLATE_REGISTRY_PATH=templates/registry

# Schema storage path (default: templates/schemas)
TEMPLATE_SCHEMAS_PATH=templates/schemas

# RBAC role for write operations (default: Author)
TEMPLATE_RBAC_ROLE=Author

# User's current role (default: Viewer)
USER_RBAC_ROLE=Author
```

## Best Practices

### 1. Start with v1.0.0

Use semantic versioning from the start:
```bash
--version 1.0.0  # Good
--version v1     # Avoid
--version 1      # Avoid
```

### 2. Document Schema Fields

Always include descriptions:
```json
{
  "count": {
    "type": "int",
    "description": "Number of items to process (1-100)",
    "min": 1,
    "max": 100
  }
}
```

### 3. Use Defaults Generously

Provide sensible defaults for optional params:
```json
{
  "timeout": {
    "type": "int",
    "required": false,
    "default": 30,
    "description": "Timeout in seconds"
  }
}
```

### 4. Tag Consistently

Use consistent tags across templates:
- productivity, professional, academic (category)
- automation, manual (execution mode)
- experimental, stable (maturity)

### 5. Deprecate Gracefully

Include clear deprecation reasons:
```bash
--reason "Use 2.0.0 which adds required 'priority' field and fixes validation bug"
```

### 6. Version Schema Files

Name schema files with version:
```
templates/schemas/my_workflow_1.0.0.schema.json
templates/schemas/my_workflow_2.0.0.schema.json
```

### 7. Test Before Registering

Validate template and schema before registering:
```python
import yaml
import json

# Test template loads
with open("my_template.yaml") as f:
    template = yaml.safe_load(f)
    assert "workflow_ref" in template

# Test schema is valid JSON
with open("my_schema.json") as f:
    schema = json.load(f)
    assert "fields" in schema
```

## Troubleshooting

### Template Not Found

```
ValueError: Template my_workflow not found in registry
```

**Fix:** Register template first:
```bash
python scripts/templates.py list  # Check if registered
python scripts/templates.py register ...  # If missing
```

### Validation Failed

```
ValueError: Parameter validation failed:
Required parameter missing: start_date
count: expected int, got str
```

**Fix:** Provide correct parameters:
```yaml
params:
  start_date: "2025-10-01"  # Was missing
  count: 10  # Was "10" (string)
```

### Permission Denied

```
Permission denied: Template registration requires Author role, but user has Viewer
```

**Fix:** Set correct role:
```bash
export USER_RBAC_ROLE=Author
```

### Template Deprecated

```
ValueError: Template my_workflow:1.0.0 is deprecated: Use 2.0.0 instead
```

**Fix:** Update to latest version:
```yaml
params:
  template_version: "2.0.0"  # Was "1.0.0"
```

### Schema File Not Found

```
FileNotFoundError: Schema file not found: templates/schemas/my_schema.json
```

**Fix:** Ensure schema file exists and path is correct:
```bash
ls templates/schemas/my_schema.json
```

## Next Steps

- See [TEMPLATES.md](TEMPLATES.md) for general template documentation
- See [OPERATIONS.md](OPERATIONS.md) for rollback procedures
- See [SECURITY.md](SECURITY.md) for RBAC details
