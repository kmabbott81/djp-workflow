# Schema Versioning Guide

This document describes the schema versioning policy for DJP workflow artifacts and how to handle schema evolution over time.

## Overview

The DJP pipeline uses semantic versioning for schema evolution to ensure backward compatibility and provide clear migration paths when breaking changes are necessary.

## Versioning Format

Schema versions follow the format: `MAJOR.MINOR`

- **MAJOR**: Incremented for breaking changes that require migration
- **MINOR**: Incremented for backward-compatible additions

### Current Version: 1.0

The current schema version is `1.0`, established as the baseline for the operational hardening sprint.

## Version Increment Guidelines

### Minor Version Increment (e.g., 1.0 → 1.1)

Increment the minor version for **backward-compatible changes**:

- Adding new optional fields to existing objects
- Adding new optional properties to parameters
- Extending enum values (when consumers can handle unknown values gracefully)
- Adding new sections that don't affect existing structure

**Examples:**
```json
// Adding optional field to run_metadata
"run_metadata": {
  "timestamp": "...",
  "task": "...",
  "trace_name": "...",
  "parameters": {...},
  "environment": {  // NEW OPTIONAL FIELD
    "python_version": "3.11.0",
    "os": "windows"
  }
}

// Adding optional parameter
"parameters": {
  "max_tokens": 1200,
  "temperature": 0.3,
  "retry_count": 3  // NEW OPTIONAL PARAMETER
}
```

### Major Version Increment (e.g., 1.0 → 2.0)

Increment the major version for **breaking changes**:

- Removing existing fields
- Changing field types or formats
- Making optional fields required
- Restructuring existing data layouts
- Changing enum values in non-backward-compatible ways

**Examples:**
```json
// BREAKING: Changing field type
"temperature": 0.3  // Was number, now string
"temperature": "low"

// BREAKING: Removing field
"run_metadata": {
  "timestamp": "...",
  "task": "...",
  // "trace_name" REMOVED
  "parameters": {...}
}

// BREAKING: Restructuring
"debate": {
  "drafts": [...],
  "total_drafts": 3
}
// Changes to:
"debate": {
  "results": {  // RESTRUCTURED
    "drafts": [...],
    "metadata": {
      "total_drafts": 3
    }
  }
}
```

## Backward Compatibility Policy

### Consumer Requirements

- **MUST** handle unknown fields gracefully (ignore or log)
- **MUST** validate against schema version they support
- **SHOULD** warn when encountering newer minor versions
- **MUST** reject artifacts with newer major versions

### Producer Requirements

- **MUST** increment version appropriately for changes
- **MUST** maintain backward compatibility within major versions
- **SHOULD** provide migration tools for major version changes
- **MUST** update validation schemas when making changes

## Schema Evolution Process

### 1. Planning Changes

Before making schema changes:

1. Determine if the change is backward-compatible
2. Choose appropriate version increment
3. Document the change and its impact
4. Plan migration strategy (if breaking)

### 2. Making Changes

1. **Update Schema Files**:
   - Modify `schemas/artifact.json`
   - Update version in schema description
   - Update constant in code if needed

2. **Update Validation**:
   - Update `scripts/validate_artifacts.py`
   - Add version-specific validation logic
   - Update sample artifacts

3. **Update Code**:
   - Modify artifact creation code
   - Update version constants
   - Add compatibility handling

4. **Update Tests**:
   - Add tests for new schema features
   - Test backward compatibility
   - Update integration tests

### 3. Migration Support

For major version changes, provide:

1. **Migration Script**: `scripts/migrate_artifacts_v{old}_to_v{new}.py`
2. **Compatibility Layer**: Temporary support for reading old versions
3. **Documentation**: Clear migration guide for users

## Implementation Details

### Version Checking

The validation system checks schema versions:

```python
def validate_schema_version(artifact: Dict[str, Any]) -> bool:
    """Validate artifact schema version."""
    version = artifact.get("schema_version", "unknown")

    if version == "unknown":
        warnings.warn("Artifact missing schema_version field")
        return False

    major, minor = map(int, version.split('.'))
    current_major, current_minor = 1, 0  # Current version

    if major > current_major:
        raise ValueError(f"Unsupported major version {major}")

    if major == current_major and minor > current_minor:
        warnings.warn(f"Newer minor version detected: {version}")

    return True
```

### Artifact Creation

All artifacts include the current schema version:

```python
artifact = {
    "schema_version": "1.0",  # Always current version
    "run_metadata": {...},
    # ... rest of artifact
}
```

### Validation Updates

When schema changes occur, update validation:

```python
# In scripts/validate_artifacts.py
def create_sample_artifact() -> Dict[str, Any]:
    return {
        "schema_version": "1.1",  # Updated version
        # ... updated structure
    }

def validate_artifact_version(artifact: Dict[str, Any]) -> bool:
    version = artifact.get("schema_version", "unknown")
    if version == "unknown":
        print("[WARN] Artifact missing schema_version field")
        return False

    if version not in ["1.0", "1.1"]:  # Support both versions
        print(f"[WARN] Unknown schema version: {version}")

    return True
```

## Version History

### Version 1.0 (Current)
- **Release Date**: 2025-09-29
- **Description**: Initial schema version for operational hardening
- **Features**:
  - Complete artifact structure with metadata, debate, judge, publish, provenance
  - Schema versioning field
  - Preset name tracking
  - Comprehensive validation

### Future Versions

Document future versions here as they are released.

## Migration Examples

### Example: Adding Optional Field (1.0 → 1.1)

**Before (1.0)**:
```json
{
  "schema_version": "1.0",
  "run_metadata": {
    "timestamp": "2025-09-29T16:20:00Z",
    "task": "Example task",
    "trace_name": "example",
    "parameters": {...}
  }
}
```

**After (1.1)**:
```json
{
  "schema_version": "1.1",
  "run_metadata": {
    "timestamp": "2025-09-29T16:20:00Z",
    "task": "Example task",
    "trace_name": "example",
    "parameters": {...},
    "environment": {  // NEW OPTIONAL FIELD
      "python_version": "3.11.0",
      "platform": "win32"
    }
  }
}
```

**Migration**: None required - old consumers ignore new field.

### Example: Breaking Change (1.x → 2.0)

**Before (1.x)**:
```json
{
  "schema_version": "1.1",
  "provenance": {
    "duration_seconds": 45.2
  }
}
```

**After (2.0)**:
```json
{
  "schema_version": "2.0",
  "provenance": {
    "timing": {  // RESTRUCTURED
      "duration_seconds": 45.2,
      "start_time": "2025-09-29T16:20:00Z",
      "end_time": "2025-09-29T16:20:45Z"
    }
  }
}
```

**Migration**: Required script to restructure provenance section.

## Best Practices

1. **Plan Ahead**: Consider future needs when designing new fields
2. **Default Values**: Provide sensible defaults for new optional fields
3. **Graceful Degradation**: Ensure older consumers can still extract useful data
4. **Clear Communication**: Document all changes thoroughly
5. **Testing**: Test both new and old schema versions
6. **Progressive Rollout**: Consider gradual adoption for major changes

## Validation Commands

```bash
# Validate current schemas
python scripts/validate_artifacts.py

# Check specific artifact version
python scripts/validate_artifacts.py --artifact runs/example.json

# Migration validation (future)
python scripts/migrate_artifacts_v1_to_v2.py --validate-only
```

This versioning system ensures the DJP pipeline can evolve while maintaining compatibility and providing clear migration paths for users.
