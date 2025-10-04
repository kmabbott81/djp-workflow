## Compliance - Data Export, Deletion, Legal Holds, Retention

**Sprint 33A** introduces GDPR-style compliance hooks for tenant data lifecycle management. All operations are tenant-scoped, RBAC-enforced, and fully audited.

---

## Core Concepts

### Data Export
Deterministic export of all tenant-scoped data into timestamped bundles. Includes:
- Tiered storage artifacts (reference list, not full copies for CI efficiency)
- Orchestrator events and state
- Queue events and DLQ entries
- Approval/checkpoint records
- Cost tracking events
- Governance audit logs

### Data Deletion
Complete removal of tenant data from all stores. Protections:
- Dry-run mode shows what would be deleted
- Legal holds block deletion by default
- RBAC enforcement (Compliance+ role)
- Full audit trail of deletion events

### Legal Holds
Prevents deletion of tenant data for regulatory/legal purposes:
- Append-only JSONL log
- Apply/release operations fully audited
- Blocks tenant deletion by default
- Query active holds

### Retention Policies
Automated pruning of old data based on configurable windows:
- Different retention periods per data type
- Safe JSONL rewrite (temp + swap)
- Respects legal holds
- Can be scheduled (e.g., daily cron job)

---

## RBAC Roles

Role hierarchy for compliance operations:

| Role       | Level | Export | Delete | Holds | Retention |
|------------|-------|--------|--------|-------|-----------|
| Viewer     | 0     | ❌     | ❌     | ❌    | ❌        |
| Author     | 1     | ❌     | ❌     | ❌    | ❌        |
| Operator   | 2     | ❌     | ❌     | ❌    | ❌        |
| Auditor    | 3     | ✅     | ❌     | ❌    | ❌        |
| Compliance | 4     | ✅     | ✅     | ✅    | ✅        |
| Admin      | 5     | ✅     | ✅     | ✅    | ✅        |

**Environment Variables:**
```bash
COMPLIANCE_RBAC_ROLE=Compliance  # Required role for mutating ops
USER_RBAC_ROLE=Auditor           # Current user's role
```

---

## CLI Reference

### Export Tenant Data

Export all tenant data to bundle directory:

```bash
python scripts/compliance.py export \
  --tenant acme-corp \
  --out ./exports
```

**Output:**
```json
{
  "tenant": "acme-corp",
  "export_date": "2025-10-03T22:30:00Z",
  "export_path": "exports/acme-corp-export-2025-10-03",
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

**Exit codes:**
- `0` - Success
- `2` - RBAC denied (requires Auditor+)
- `1` - Other error

**Bundle structure:**
```
acme-corp-export-2025-10-03/
├── manifest.json              # Export summary
├── artifacts.json             # Artifact references (paths, not copies)
├── orchestrator_events.jsonl  # DAG execution logs
├── queue_events.jsonl         # Queue activity
├── cost_events.jsonl          # Cost tracking
├── approval_events.jsonl      # Approval/checkpoint records
└── governance_events.jsonl    # Governance audit logs
```

---

### Delete Tenant Data

**Dry-run** (recommended first):
```bash
python scripts/compliance.py delete \
  --tenant acme-corp \
  --dry-run
```

**Live deletion:**
```bash
python scripts/compliance.py delete \
  --tenant acme-corp
```

**Output:**
```json
{
  "tenant": "acme-corp",
  "dry_run": false,
  "deleted_at": "2025-10-03T22:35:00Z",
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

**Exit codes:**
- `0` - Success
- `2` - RBAC denied (requires Compliance+)
- `3` - Legal hold active (blocks deletion)
- `1` - Other error

---

### Legal Holds

**Apply hold:**
```bash
python scripts/compliance.py hold \
  --tenant acme-corp \
  --reason "Litigation hold - Case #2025-1234"
```

**Output:**
```json
{
  "timestamp": "2025-10-03T22:40:00Z",
  "event": "hold_applied",
  "tenant": "acme-corp",
  "reason": "Litigation hold - Case #2025-1234"
}
```

**Release hold:**
```bash
python scripts/compliance.py release \
  --tenant acme-corp
```

**List active holds:**
```bash
python scripts/compliance.py holds --list
```

**Output:**
```json
{
  "holds": [
    {
      "tenant": "acme-corp",
      "reason": "Litigation hold - Case #2025-1234",
      "applied_at": "2025-10-03T22:40:00Z"
    }
  ],
  "count": 1
}
```

**Exit codes:**
- `0` - Success
- `2` - RBAC denied (requires Compliance+ for apply/release)
- `1` - Error (e.g., no active hold to release)

---

### Retention Enforcement

Run retention pruning (typically scheduled daily):

```bash
python scripts/compliance.py retention
```

**Output:**
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

**Exit codes:**
- `0` - Success
- `2` - RBAC denied (requires Compliance+)
- `1` - Other error

---

## Retention Configuration

Retention windows (in days) configured via environment variables:

```bash
# Orchestrator and DAG execution events
RETAIN_ORCH_EVENTS_DAYS=90      # Default: 90 days

# Queue and task events
RETAIN_QUEUE_EVENTS_DAYS=60     # Default: 60 days

# Dead letter queue entries
RETAIN_DLQ_DAYS=30              # Default: 30 days

# Approval and checkpoint records
RETAIN_CHECKPOINTS_DAYS=90      # Default: 90 days

# Cost tracking events
RETAIN_COST_EVENTS_DAYS=180     # Default: 180 days

# Governance audit logs
RETAIN_GOV_EVENTS_DAYS=365      # Default: 365 days
```

**How it works:**
1. Reads JSONL event logs
2. Parses timestamps
3. Keeps entries within retention window
4. Writes to temp file
5. Swaps temp → original (atomic)

**Safety:**
- Malformed entries preserved (avoid data loss)
- Legal holds respected (for tenant-specific deletion)
- Temp file pattern prevents corruption

---

## Audit Surfaces

All compliance operations are fully audited:

### Legal Holds
**Log:** `LOGS_LEGAL_HOLDS_PATH` (default: `logs/legal_holds.jsonl`)

**Events:**
```jsonl
{"timestamp": "2025-10-03T22:40:00Z", "event": "hold_applied", "tenant": "acme-corp", "reason": "..."}
{"timestamp": "2025-10-03T23:00:00Z", "event": "hold_released", "tenant": "acme-corp"}
```

### Data Export
Export operations logged to governance events:
```jsonl
{"timestamp": "2025-10-03T22:30:00Z", "event": "export", "tenant": "acme-corp", "user": "compliance-officer", "item_count": 385}
```

### Data Deletion
Deletion operations logged to governance events:
```jsonl
{"timestamp": "2025-10-03T22:35:00Z", "event": "delete", "tenant": "acme-corp", "user": "compliance-officer", "item_count": 385, "dry_run": false}
```

### Retention Enforcement
Retention runs logged to governance events:
```jsonl
{"timestamp": "2025-10-03T22:45:00Z", "event": "retention_enforced", "purged_count": 28}
```

---

## Common Workflows

### Export → Delete Workflow

1. **Export data first** (for backup/audit):
   ```bash
   python scripts/compliance.py export --tenant acme-corp --out ./exports
   ```

2. **Dry-run deletion** (verify scope):
   ```bash
   python scripts/compliance.py delete --tenant acme-corp --dry-run
   ```

3. **Live deletion**:
   ```bash
   python scripts/compliance.py delete --tenant acme-corp
   ```

### Legal Hold Workflow

1. **Apply hold immediately**:
   ```bash
   python scripts/compliance.py hold \
     --tenant acme-corp \
     --reason "Litigation hold - Case #2025-1234"
   ```

2. **Verify hold active**:
   ```bash
   python scripts/compliance.py holds --list
   ```

3. **Attempt deletion** (should fail):
   ```bash
   python scripts/compliance.py delete --tenant acme-corp
   # Exit code: 3 (LEGAL_HOLD)
   ```

4. **Release hold when cleared**:
   ```bash
   python scripts/compliance.py release --tenant acme-corp
   ```

### Scheduled Retention

Add to cron/scheduler (example for daily 2 AM):

```bash
0 2 * * * cd /path/to/repo && USER_RBAC_ROLE=Compliance python scripts/compliance.py retention >> logs/retention.log 2>&1
```

**Note:** Scheduler integration commented for future implementation.

---

## Programmatic API

For integration with other tools:

```python
from src.compliance import (
    export_tenant,
    delete_tenant,
    apply_legal_hold,
    release_legal_hold,
    is_on_hold,
    current_holds,
    enforce_retention,
)

# Export
result = export_tenant("acme-corp", Path("./exports"))

# Check hold before delete
if is_on_hold("acme-corp"):
    print("Cannot delete: legal hold active")
else:
    delete_tenant("acme-corp", dry_run=False)

# Apply hold
apply_legal_hold("acme-corp", "Litigation hold")

# Enforce retention
enforce_retention()
```

---

## Troubleshooting

### Error: RBAC denied

**Cause:** User lacks required role (Auditor+ for export, Compliance+ for mutations)

**Fix:** Set `USER_RBAC_ROLE` environment variable:
```bash
export USER_RBAC_ROLE=Compliance
python scripts/compliance.py delete --tenant acme-corp
```

### Error: Legal hold active

**Cause:** Tenant has active legal hold

**Fix:** Release hold first (requires Compliance+ role):
```bash
python scripts/compliance.py release --tenant acme-corp
python scripts/compliance.py delete --tenant acme-corp
```

### Export bundle missing data

**Cause:** Data may be in different paths than defaults

**Fix:** Verify environment variables match your deployment:
```bash
STORAGE_BASE_PATH=./artifacts
ORCH_EVENTS_PATH=./logs/orchestrator_events.jsonl
# ... etc
```

### Retention not purging old data

**Cause:** Timestamps may be malformed or retention window too long

**Fix:**
1. Verify JSONL timestamps are ISO 8601 format
2. Check retention env vars (e.g., `RETAIN_ORCH_EVENTS_DAYS=90`)
3. Run with shorter window for testing

---

## Best Practices

1. **Always export before delete** - Provides backup and audit trail
2. **Use dry-run first** - Verify deletion scope before executing
3. **Document legal hold reasons** - Include case numbers, dates, requestor
4. **Schedule retention enforcement** - Daily cron job recommended
5. **Monitor audit logs** - Review legal_holds.jsonl and governance_events.jsonl regularly
6. **Test in non-production** - Verify export/delete work as expected before production use
7. **Backup exports** - Store export bundles in secure, durable storage

---

## Future Enhancements

- Automated export → delete workflow with approval gate
- Retention policies per tenant (override defaults)
- Email notifications for hold apply/release
- Web UI for compliance operations
- Encrypted export bundles
- Integration with external archival systems (S3, GCS, Azure Blob)
