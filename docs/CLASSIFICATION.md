# Data Classification - Sprint 33B

## Overview

Label-based access control for tenant data with hierarchical clearances. All artifacts and logs can carry classification labels that determine who can access them.

## Classification Hierarchy

Labels are ordered from least to most sensitive:

```
Public < Internal < Confidential < Restricted
```

### Label Definitions

- **Public**: No restrictions, safe for external sharing
- **Internal**: Company-internal, not for external distribution
- **Confidential**: Sensitive business data, restricted access
- **Restricted**: Highly sensitive, requires highest clearance

## Clearances

User clearances follow the same hierarchy. A user with a given clearance can access data at their level or below:

```
User with Confidential clearance:
  ✅ Can access: Public, Internal, Confidential
  ❌ Cannot access: Restricted
```

## Configuration

### Environment Variables

```bash
# Classification labels (comma-separated, ordered)
CLASS_LABELS=Public,Internal,Confidential,Restricted

# Default label for unlabeled artifacts
DEFAULT_LABEL=Internal

# User clearance level
USER_CLEARANCE=Operator  # Maps to Internal by default

# Require labels for export (deny unlabeled exports)
REQUIRE_LABELS_FOR_EXPORT=true

# Export policy for insufficient clearance
EXPORT_POLICY=deny  # deny|redact
```

## Labeling Artifacts

### Manual Labeling

```bash
# Set label for artifact
python scripts/classification.py set-label \
  --path artifacts/hot/tenant-a/report.md \
  --label Confidential

# View artifact metadata
python scripts/classification.py show \
  --path artifacts/hot/tenant-a/report.md
```

### Programmatic Labeling

```python
from src.storage.secure_io import write_encrypted

# Write artifact with label
write_encrypted(
    path=Path("artifact.md"),
    data=b"sensitive content",
    label="Confidential",
    tenant="acme-corp"
)
```

### Label Inheritance

If no label is explicitly set:
1. Check artifact metadata
2. Fall back to `DEFAULT_LABEL` environment variable
3. Ultimate fallback: first label in hierarchy (Public)

## Access Control

### Read Access

```python
from src.storage.secure_io import read_encrypted

# User clearance checked automatically
try:
    data = read_encrypted(
        Path("artifact.md"),
        user_clearance="Internal"
    )
except PermissionError:
    # Insufficient clearance
    pass
```

### Export Access

During compliance export, artifacts are filtered by clearance:

```bash
export USER_CLEARANCE=Confidential

# Exports all artifacts up to Confidential
python scripts/compliance.py export \
  --tenant acme-corp \
  --out ./exports
```

Behavior based on `EXPORT_POLICY`:
- **deny**: Skip artifacts with insufficient clearance
- **redact**: Include artifact metadata but mark as redacted

## DAG and Task Defaults

### Workflow Classification

Set default labels for entire workflows:

```python
{
    "dag_id": "sensitive-analysis",
    "metadata": {
        "default_label": "Confidential"
    },
    "tasks": [...]
}
```

### Task-Level Labels

Override at task level:

```python
{
    "task_id": "generate-report",
    "metadata": {
        "label": "Restricted"
    }
}
```

Artifacts created by tasks inherit the task's label, falling back to workflow default, then system default.

## Governance Integration

### Audit Events

All access denials are logged to `logs/governance_events.jsonl`:

```json
{
  "timestamp": "2025-10-03T12:00:00Z",
  "event": "export_denied",
  "tenant": "acme-corp",
  "artifact": "artifacts/hot/acme-corp/sensitive.md",
  "label": "Restricted",
  "user_clearance": "Confidential",
  "reason": "insufficient_clearance",
  "policy": "deny"
}
```

### Export Summary

Export manifest includes denied counts:

```json
{
  "tenant": "acme-corp",
  "counts": {
    "artifacts": 45,
    "artifacts_denied": 3
  }
}
```

## Best Practices

1. **Label at creation**: Set labels when artifacts are created
2. **Principle of least privilege**: Use lowest clearance that meets needs
3. **Audit regularly**: Review governance events for unexpected denials
4. **Document classification**: Maintain mapping of data types to labels
5. **Training**: Ensure team understands label hierarchy

## Troubleshooting

### Artifact Denied on Export

**Symptom**: Artifact missing from export bundle

**Check**:
```bash
# View artifact metadata
python scripts/classification.py show --path <artifact>

# Check user clearance
echo $USER_CLEARANCE

# Review governance log
grep export_denied logs/governance_events.jsonl
```

### Unlabeled Artifacts

**Symptom**: Export fails with "unlabeled" error

**Solution**:
```bash
# Option 1: Label the artifact
python scripts/classification.py set-label \
  --path <artifact> \
  --label Internal

# Option 2: Allow unlabeled exports
export REQUIRE_LABELS_FOR_EXPORT=false
```

### Access Denied

**Symptom**: `PermissionError: Insufficient clearance`

**Solutions**:
- Increase user clearance: `export USER_CLEARANCE=Confidential`
- Reduce artifact sensitivity: Re-label with lower classification
- Request temporary elevated access from compliance team

## See Also

- [ENCRYPTION.md](ENCRYPTION.md) - Envelope encryption
- [COMPLIANCE.md](COMPLIANCE.md) - Export and deletion
- [SECURITY.md](SECURITY.md) - RBAC roles
- [OPERATIONS.md](OPERATIONS.md) - Compliance runbooks
