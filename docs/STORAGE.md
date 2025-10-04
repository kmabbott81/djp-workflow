# Storage System Documentation

## Overview

The Sprint 26 storage system implements a three-tier architecture for managing workflow artifacts with automatic lifecycle management, tenant isolation, and audit logging.

## Three-Tier Architecture

### Hot Tier (0-7 days)
- **Purpose**: Recently created/accessed artifacts
- **Access Speed**: Fast (local filesystem)
- **Cost**: Highest storage cost
- **Default Retention**: 7 days
- **Location**: `artifacts/hot/{tenant_id}/{workflow_id}/{artifact_id}`

### Warm Tier (7-30 days)
- **Purpose**: Less frequently accessed artifacts
- **Access Speed**: Medium
- **Cost**: Medium storage cost
- **Default Retention**: 30 days
- **Location**: `artifacts/warm/{tenant_id}/{workflow_id}/{artifact_id}`

### Cold Tier (30-90 days)
- **Purpose**: Rarely accessed archive storage
- **Access Speed**: Slower but lower cost
- **Cost**: Lowest storage cost
- **Default Retention**: 90 days
- **Location**: `artifacts/cold/{tenant_id}/{workflow_id}/{artifact_id}`

### Purged (>90 days)
- Artifacts older than cold retention are permanently deleted
- All operations are audit logged for compliance
- Cannot be recovered after purging

## Environment Variables

Configure retention policies and storage paths via environment variables:

```bash
# Storage configuration
STORAGE_BASE_PATH=artifacts        # Base path for all tiers
LOG_DIR=logs                       # Lifecycle event log directory

# Retention policies (in days)
HOT_RETENTION_DAYS=7               # Default: 7 days
WARM_RETENTION_DAYS=30             # Default: 30 days
COLD_RETENTION_DAYS=90             # Default: 90 days
```

## Quick Start Guide

### 1. Run the Archive Rotation Demo

The easiest way to understand the system is to run the demo workflow:

```bash
# Generate 50 artifacts and demonstrate lifecycle
python src/workflows/stress/archive_rotation_demo.py --count 50

# With forced aging to see promotion
python src/workflows/stress/archive_rotation_demo.py --count 50 --force-age

# Dry run to test without changes
python src/workflows/stress/archive_rotation_demo.py --count 25 --dry-run

# Custom tenant
python src/workflows/stress/archive_rotation_demo.py --tenant acme_corp --count 100
```

### 2. Run Lifecycle Job

Execute the automated lifecycle job to promote and purge artifacts:

```bash
# Dry run to see what would happen
python scripts/lifecycle_run.py --dry-run

# Execute lifecycle job
python scripts/lifecycle_run.py --live

# Show summary without running
python scripts/lifecycle_run.py --summary

# Verbose output with details
python scripts/lifecycle_run.py --live --verbose
```

### 3. Restore an Artifact

Restore artifacts from warm or cold tiers back to hot:

```bash
# List restorable artifacts
python scripts/restore_artifact.py --tenant acme --from-tier warm --list

# Restore specific artifact
python scripts/restore_artifact.py \
  --tenant acme \
  --workflow wf1 \
  --artifact document.txt \
  --from-tier warm

# Auto-select and restore first artifact
python scripts/restore_artifact.py --tenant acme --from-tier warm --auto-select

# Dry run
python scripts/restore_artifact.py \
  --tenant acme \
  --workflow wf1 \
  --artifact document.txt \
  --from-tier warm \
  --dry-run
```

## Python API Usage

### Writing Artifacts

```python
from src.storage.tiered_store import write_artifact, TIER_HOT

# Write artifact with metadata
path = write_artifact(
    tier=TIER_HOT,
    tenant_id="acme_corp",
    workflow_id="weekly_report",
    artifact_id="report_2024_01.md",
    content=b"# Weekly Report\n...",
    metadata={
        "report_date": "2024-01-15",
        "author": "Alice",
        "version": "1.0"
    }
)

print(f"Artifact written to: {path}")
```

### Reading Artifacts

```python
from src.storage.tiered_store import read_artifact, TIER_HOT

# Read artifact and metadata
content, metadata = read_artifact(
    tier=TIER_HOT,
    tenant_id="acme_corp",
    workflow_id="weekly_report",
    artifact_id="report_2024_01.md"
)

print(f"Content: {content.decode()}")
print(f"Author: {metadata['author']}")
print(f"Created: {metadata['_created_at']}")
```

### Listing Artifacts

```python
from src.storage.tiered_store import list_artifacts, TIER_WARM

# List all artifacts in warm tier
artifacts = list_artifacts(TIER_WARM)

for artifact in artifacts:
    print(f"{artifact['tenant_id']}/{artifact['workflow_id']}/{artifact['artifact_id']}")
    print(f"  Size: {artifact['size_bytes']} bytes")
    print(f"  Modified: {artifact['modified_at']}")

# List artifacts for specific tenant
tenant_artifacts = list_artifacts(TIER_WARM, tenant_id="acme_corp")
```

### Promoting Artifacts

```python
from src.storage.tiered_store import promote_artifact, TIER_WARM, TIER_HOT

# Restore artifact from warm to hot
success = promote_artifact(
    tenant_id="acme_corp",
    workflow_id="weekly_report",
    artifact_id="report_2024_01.md",
    from_tier=TIER_WARM,
    to_tier=TIER_HOT,
    dry_run=False  # Set to True to test without moving
)

if success:
    print("Artifact promoted successfully")
```

### Running Lifecycle Job

```python
from src.storage.lifecycle import run_lifecycle_job

# Run lifecycle job programmatically
results = run_lifecycle_job(dry_run=False)

print(f"Promoted to warm: {results['promoted_to_warm']}")
print(f"Promoted to cold: {results['promoted_to_cold']}")
print(f"Purged: {results['purged']}")
print(f"Errors: {results['total_errors']}")
print(f"Duration: {results['job_duration_seconds']}s")
```

## Recovery & Restore Procedures

### Restoring Recently Archived Artifacts

If artifacts were prematurely promoted to warm/cold tiers:

```bash
# 1. List artifacts in warm tier
python scripts/restore_artifact.py --tenant acme --from-tier warm --list

# 2. Identify artifact to restore
# 3. Restore to hot tier
python scripts/restore_artifact.py \
  --tenant acme \
  --workflow important_project \
  --artifact critical_document.pdf \
  --from-tier warm \
  --to-tier hot
```

### Bulk Restoration

For restoring multiple artifacts:

```python
from src.storage.tiered_store import list_artifacts, TIER_WARM, TIER_HOT
from src.storage.lifecycle import restore_artifact

# List all artifacts for tenant in warm tier
artifacts = list_artifacts(TIER_WARM, tenant_id="acme_corp")

# Restore all artifacts from specific workflow
for artifact in artifacts:
    if artifact["workflow_id"] == "important_project":
        restore_artifact(
            tenant_id=artifact["tenant_id"],
            workflow_id=artifact["workflow_id"],
            artifact_id=artifact["artifact_id"],
            from_tier=TIER_WARM,
            to_tier=TIER_HOT
        )
        print(f"Restored: {artifact['artifact_id']}")
```

### Recovering from Accidental Purge

**IMPORTANT**: Purged artifacts cannot be recovered. To prevent accidental purges:

1. **Always dry-run first**: `python scripts/lifecycle_run.py --dry-run`
2. **Review audit logs**: Check `logs/lifecycle_events.jsonl` before live runs
3. **Backup critical data**: Keep backups outside the lifecycle system
4. **Adjust retention policies**: Increase `COLD_RETENTION_DAYS` for important tenants

## Tenant Isolation & Security

### Path Validation

All tenant IDs, workflow IDs, and artifact IDs are validated to prevent path traversal attacks:

```python
# ✓ Valid identifiers
tenant_id = "acme_corp"
workflow_id = "weekly_report"
artifact_id = "report.md"

# ✗ Invalid identifiers (will raise InvalidTenantPathError)
tenant_id = "../../../etc"        # Path traversal
workflow_id = "/tmp/exploit"      # Absolute path
artifact_id = "../../passwd"       # Path traversal
tenant_id = "acme:corp"           # Invalid characters (:*?"<>|)
```

### Tenant Directory Structure

Each tenant's artifacts are isolated in their own directory:

```
artifacts/
├── hot/
│   ├── acme_corp/
│   │   ├── workflow1/
│   │   │   ├── artifact1.txt
│   │   │   └── artifact1.txt.metadata.json
│   │   └── workflow2/
│   │       └── artifact2.pdf
│   └── globex_inc/
│       └── workflow1/
│           └── artifact1.txt
├── warm/
│   └── acme_corp/
│       └── workflow1/
│           └── old_artifact.txt
└── cold/
    └── acme_corp/
        └── workflow1/
            └── archived_artifact.txt
```

### Audit Logging

All storage operations are logged to `logs/lifecycle_events.jsonl`:

```json
{
  "timestamp": "2024-01-15T10:30:00.000000",
  "event_type": "promoted_to_warm",
  "tenant_id": "acme_corp",
  "workflow_id": "weekly_report",
  "artifact_id": "report.md",
  "age_days": 8.5,
  "dry_run": false
}
```

View recent events:

```python
from src.storage.lifecycle import get_recent_lifecycle_events

events = get_recent_lifecycle_events(limit=20)
for event in events:
    print(f"{event['timestamp']}: {event['event_type']}")
```

## Monitoring & Observability

### Storage Statistics

Get statistics for all tiers:

```python
from src.storage.tiered_store import get_all_tier_stats

stats = get_all_tier_stats()

for tier, tier_stats in stats.items():
    print(f"\n{tier.upper()} Tier:")
    print(f"  Artifacts: {tier_stats['artifact_count']}")
    print(f"  Total Size: {tier_stats['total_bytes'] / (1024*1024):.2f} MB")
    print(f"  Tenants: {tier_stats['tenant_count']}")
```

### Dashboard Integration

The observability dashboard (`dashboards/observability_tab.py`) includes a storage lifecycle section showing:

- Artifact counts per tier
- Last lifecycle job status
- Recent lifecycle events
- Quick action buttons

Access via Streamlit:

```bash
streamlit run app.py
# Navigate to Observability tab → Storage Lifecycle section
```

### Command Line Monitoring

```bash
# Show current state
python scripts/lifecycle_run.py --summary

# Check specific tier
python -c "from src.storage.tiered_store import get_tier_stats; import json; print(json.dumps(get_tier_stats('hot'), indent=2))"
```

## Troubleshooting

### Issue: Artifacts Not Being Promoted

**Symptoms**: Lifecycle job runs but no artifacts are promoted

**Solutions**:
1. Check artifact age: `get_artifact_age_days(tier, tenant_id, workflow_id, artifact_id)`
2. Verify retention policies: `get_retention_days()`
3. Check for errors in `logs/lifecycle_events.jsonl`
4. Run with verbose output: `python scripts/lifecycle_run.py --dry-run --verbose`

### Issue: Storage Growing Too Large

**Symptoms**: Hot tier consuming excessive disk space

**Solutions**:
1. Reduce retention policies: Set lower `HOT_RETENTION_DAYS`
2. Run lifecycle more frequently: Schedule hourly/daily cron jobs
3. Manually promote old artifacts:
   ```python
   from src.storage.lifecycle import promote_expired_to_warm
   results = promote_expired_to_warm(dry_run=False)
   ```

### Issue: Cannot Find Artifact

**Symptoms**: `ArtifactNotFoundError` when reading artifact

**Solutions**:
1. Check which tier it's in: `list_artifacts(tier, tenant_id=tenant_id)`
2. Search all tiers:
   ```python
   for tier in ['hot', 'warm', 'cold']:
       artifacts = list_artifacts(tier, tenant_id="acme")
       if any(a['artifact_id'] == 'missing.txt' for a in artifacts):
           print(f"Found in {tier} tier")
   ```
3. Check audit log for promotion/purge: `get_recent_lifecycle_events()`

### Issue: Checksum Verification Failure

**Symptoms**: Checksum mismatch when verifying artifacts

**Solutions**:
1. Content may have been corrupted during transfer
2. Check file permissions and disk errors
3. Restore from backup if available
4. Re-generate the artifact if it's derived from source data

### Issue: Permission Denied Errors

**Symptoms**: Cannot read/write artifacts

**Solutions**:
1. Check file permissions: `ls -la artifacts/hot/tenant_id/`
2. Ensure storage directories are writable: `chmod -R u+rw artifacts/`
3. Verify `STORAGE_BASE_PATH` environment variable points to correct location

## Best Practices

### 1. Use Dry-Run Mode First

Always test lifecycle operations with `--dry-run` before executing live:

```bash
# Test first
python scripts/lifecycle_run.py --dry-run

# Review output, then execute
python scripts/lifecycle_run.py --live
```

### 2. Schedule Regular Lifecycle Jobs

Set up cron job for automated lifecycle management:

```cron
# Run lifecycle job daily at 2 AM
0 2 * * * cd /path/to/project && python scripts/lifecycle_run.py --live >> logs/lifecycle_cron.log 2>&1
```

### 3. Monitor Storage Usage

Implement alerts for storage thresholds:

```python
from src.storage.tiered_store import get_tier_stats

stats = get_tier_stats('hot')
size_gb = stats['total_bytes'] / (1024**3)

if size_gb > 100:  # Alert if hot tier > 100GB
    send_alert(f"Hot tier storage: {size_gb:.2f}GB")
```

### 4. Backup Critical Artifacts

For business-critical data, maintain backups outside the lifecycle system:

```python
import shutil
from src.storage.tiered_store import read_artifact

# Backup critical artifacts before they age out
content, metadata = read_artifact('hot', 'acme', 'contracts', 'contract_2024.pdf')

with open('/backups/contract_2024.pdf', 'wb') as f:
    f.write(content)
```

### 5. Use Metadata Effectively

Store searchable metadata with artifacts:

```python
write_artifact(
    tier=TIER_HOT,
    tenant_id="acme",
    workflow_id="contracts",
    artifact_id="contract_2024.pdf",
    content=pdf_bytes,
    metadata={
        "document_type": "contract",
        "customer": "Acme Corp",
        "value": 50000,
        "signed_date": "2024-01-15",
        "retention_override": "7_years"  # Custom retention
    }
)
```

### 6. Test Recovery Procedures

Regularly test artifact restoration:

```bash
# Monthly drill: Restore sample artifacts
python scripts/restore_artifact.py --tenant acme --from-tier cold --auto-select
```

## Advanced Configuration

### Custom Retention Policies Per Tenant

Implement custom retention logic:

```python
from src.storage.lifecycle import scan_tier_for_expired, promote_artifact

def promote_with_custom_retention(tenant_id):
    """Custom retention: VIP tenants get 14 days in hot tier."""
    vip_tenants = ['acme_corp', 'globex_inc']

    retention_days = 14 if tenant_id in vip_tenants else 7

    expired = scan_tier_for_expired('hot', max_age_days=retention_days)

    for artifact in expired:
        if artifact['tenant_id'] == tenant_id:
            promote_artifact(
                tenant_id=artifact['tenant_id'],
                workflow_id=artifact['workflow_id'],
                artifact_id=artifact['artifact_id'],
                from_tier='hot',
                to_tier='warm'
            )
```

### Integration with External Storage

For production deployments, integrate with cloud storage:

```python
# Example: Archive cold tier to S3
import boto3
from src.storage.tiered_store import list_artifacts, read_artifact

s3 = boto3.client('s3')

artifacts = list_artifacts('cold', tenant_id='acme')

for artifact in artifacts:
    content, metadata = read_artifact(
        'cold',
        artifact['tenant_id'],
        artifact['workflow_id'],
        artifact['artifact_id']
    )

    # Upload to S3
    s3.put_object(
        Bucket='my-archive-bucket',
        Key=f"{artifact['tenant_id']}/{artifact['workflow_id']}/{artifact['artifact_id']}",
        Body=content,
        Metadata=metadata
    )
```

## Performance Considerations

### Large Artifact Sets

For tenants with thousands of artifacts:

1. **Batch operations**: Process artifacts in chunks
2. **Parallel processing**: Use multiprocessing for lifecycle jobs
3. **Index metadata**: Store artifact lists in database for fast queries

### High-Frequency Access

For frequently accessed artifacts:

1. **Keep in hot tier**: Adjust retention policies
2. **Cache checksums**: Avoid re-computing on every read
3. **Use memory-mapped files**: For very large artifacts

## Support

For issues or questions:

1. Check troubleshooting section above
2. Review audit logs: `logs/lifecycle_events.jsonl`
3. Run diagnostics: `python scripts/lifecycle_run.py --summary`
4. Contact system administrator with relevant log excerpts

## See Also

- [OPERATIONS.md](./OPERATIONS.md) - Operational procedures
- [SECURITY.md](./SECURITY.md) - Security considerations
- [API Documentation](../src/storage/) - Detailed API reference
