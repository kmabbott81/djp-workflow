# Unified Resource Graph (URG) - Architecture Documentation

**Sprint 38** | **Status:** Complete

## Overview

The Unified Resource Graph (URG) is a cross-connector indexing and search system that normalizes resources from all connectors (Teams, Outlook, Slack, Gmail) into a unified schema, enabling fast search, filtering, and cross-connector action execution.

## Key Features

- **Unified Schema**: All resources normalized to common format via CP-CAL
- **Fast Search**: In-memory inverted index for sub-second search
- **Tenant Isolation**: Complete data separation by tenant
- **JSONL Persistence**: Append-only shards for durability
- **Action Router**: Execute actions across connectors with RBAC
- **Cross-Connector Search**: Search Teams, Outlook, Slack, Gmail in one query

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Application Layer                         │
│  (CLI, Dashboard, API)                                       │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│              URG Search & Actions Layer                      │
│  • search(query, tenant, type, source)                       │
│  • execute_action(action, graph_id, payload)                 │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│              URG Index (In-Memory)                           │
│  • Inverted index (token → resource_ids)                     │
│  • Type index (type → resource_ids)                          │
│  • Source index (source → resource_ids)                      │
│  • Tenant index (tenant → resource_ids)                      │
└─────────────────┬───────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│         JSONL Shards (Persistent Storage)                    │
│  logs/graph/{tenant}/{YYYY-MM-DD}.jsonl                      │
└──────────────────────────────────────────────────────────────┘
                  │
┌─────────────────▼───────────────────────────────────────────┐
│              Connector Layer                                 │
│  • TeamsConnector                                            │
│  • OutlookConnector                                          │
│  • SlackConnector                                            │
│  • GmailConnector                                            │
└──────────────────────────────────────────────────────────────┘
```

## Data Model

### Unified Resource Schema

All resources indexed in URG have this schema:

```python
{
  "id": "urn:{source}:{type}:{original_id}",  # Graph ID (unique)
  "type": "message" | "contact" | "event" | "channel",
  "title": "Resource title/subject",
  "snippet": "Preview text (first 200 chars)",
  "timestamp": "ISO 8601 timestamp",
  "source": "teams" | "outlook" | "slack" | "gmail",
  "tenant": "tenant-id",
  "labels": ["tag1", "tag2"],
  "participants": ["user1@example.com", "user2@example.com"],
  "thread_id": "thread identifier",
  "channel_id": "channel identifier",
  "metadata": {
    "original_id": "original resource ID",
    "connector_resource_type": "messages",
    # ... connector-specific fields
  }
}
```

### Resource Types

- **message**: Email, chat message, channel post
- **contact**: User profile, contact entry
- **event**: Calendar event, meeting
- **channel**: Teams channel, Slack channel

### Graph ID Format

Graph IDs follow the pattern: `urn:{source}:{type}:{original_id}`

Examples:
- `urn:teams:message:msg-abc123`
- `urn:outlook:contact:contact-456`
- `urn:slack:message:1234567890.123456`
- `urn:gmail:message:18abc123def`

## Ingestion Process

### 1. Connector Snapshot

```python
from src.connectors.ingest import ingest_connector_snapshot

result = ingest_connector_snapshot(
    "teams",              # Connector ID
    "messages",           # Resource type
    tenant="acme-corp",   # Tenant for isolation
    user_id="user-123",   # User for RBAC
    limit=100             # Max resources
)

# Returns: {"count": 85, "errors": 0, "source": "teams", ...}
```

### 2. CP-CAL Normalization

Each resource is normalized via CP-CAL (Cross-Platform Connector Abstraction Layer):

```python
from src.connectors.cp_cal import SchemaAdapter

adapter = SchemaAdapter()

# Normalize Teams message
normalized = adapter.normalize_message("teams", raw_teams_message)

# Result: {"id", "subject", "body", "from", "timestamp", "metadata"}
```

### 3. URG Indexing

Normalized resources are upserted to URG:

```python
from src.graph.index import get_index

index = get_index()

graph_id = index.upsert(
    normalized_resource,
    source="teams",
    tenant="acme-corp"
)

# Returns: "urn:teams:message:msg-123"
```

### 4. Automatic Index Building

- **Inverted Index**: Tokenizes title, snippet, participants, labels
- **Type Index**: Groups by resource type
- **Source Index**: Groups by connector source
- **Tenant Index**: Enforces isolation by tenant

## Search Functionality

### Basic Search

```python
from src.graph.search import search

results = search(
    "quarterly planning",
    tenant="acme-corp",
    limit=50
)
```

### Filtered Search

```python
# Search only messages
results = search(
    "budget review",
    tenant="acme-corp",
    type="message",
    limit=20
)

# Search specific connector
results = search(
    "standup",
    tenant="acme-corp",
    source="slack",
    limit=10
)

# Combined filters
results = search(
    "meeting notes",
    tenant="acme-corp",
    type="message",
    source="teams",
    limit=30
)
```

### Search Algorithm

1. **Tokenization**: Query split into lowercase tokens (split on `\W+`)
2. **Matching**:
   - Title exact match: 10 points
   - Title word match: 5 points
   - Snippet match: 3 points
   - Participants match: 2 points
   - Labels match: 2 points
   - Any field match: 1 point
3. **Filtering**: Apply tenant (required), type, source filters
4. **Sorting**: By score descending, then timestamp descending
5. **Limiting**: Return top N results (max: URG_MAX_RESULTS env var)

### Empty Query Behavior

Empty query returns all resources (filtered by tenant/type/source), sorted by timestamp descending.

## Action Router

### Executing Actions

```python
from src.graph.actions import execute_action

result = execute_action(
    "message.reply",                    # Action (format: type.action)
    "urn:teams:message:msg-123",       # Graph ID
    {"body": "Thanks for the update!"}, # Payload
    user_id="admin",                    # User (for RBAC)
    tenant="acme-corp"                  # Tenant
)

# Returns: {"status": "success", "action": "message.reply", ...}
```

### Available Actions

#### Message Actions

- **message.reply**: Reply to message
  ```python
  payload = {"body": "Reply text"}
  ```

- **message.forward**: Forward message
  ```python
  payload = {"to": ["user@example.com"], "comment": "FYI"}
  ```

- **message.delete**: Delete message
  ```python
  payload = {}
  ```

#### Contact Actions

- **contact.email**: Send email to contact
  ```python
  payload = {"subject": "Hello", "body": "Message text"}
  ```

#### Event Actions

- **event.accept**: Accept calendar event (Outlook only)
  ```python
  payload = {"comment": "I'll be there"}
  ```

- **event.decline**: Decline calendar event (Outlook only)
  ```python
  payload = {"comment": "Can't make it"}
  ```

### Action Routing Flow

1. **Parse Action**: Split into `resource_type.action_name`
2. **Lookup Resource**: Get from URG index
3. **RBAC Check**: Verify user has Admin role
4. **Load Connector**: Instantiate appropriate connector (Teams, Outlook, etc.)
5. **Execute**: Call connector method with normalized payload
6. **Audit Log**: Record action execution (success/failure/denied)

### RBAC Requirements

All actions require **Admin** role. Checks are performed:
1. At action execution entry point
2. Re-verified at connector level (if connector enforces RBAC)

Denied actions return `RBACDenied` exception and log audit event.

## Storage & Persistence

### JSONL Shards

Resources stored in append-only JSONL files:

```
logs/graph/
  acme-corp/
    2025-01-15.jsonl
    2025-01-16.jsonl
  other-corp/
    2025-01-15.jsonl
```

Each line is a complete JSON resource.

### Shard Loading

On initialization, URG loads all shards:

```python
from src.graph.index import URGIndex

index = URGIndex(store_path="logs/graph")
# Automatically loads all shards into memory
```

### Index Rebuilding

Rebuild index from shards:

```python
index = get_index()
index.rebuild_index(tenant="acme-corp")  # Rebuild for one tenant

# Or rebuild all
index.rebuild_index()
```

## Tenant Isolation

URG enforces strict tenant isolation:

1. **Search**: Tenant parameter is required, filters all results
2. **Actions**: Tenant verified against resource before execution
3. **Storage**: Separate shard directories per tenant
4. **Indexes**: Tenant index tracks all resources by tenant

Cross-tenant access is **not possible** - resources from other tenants are completely hidden.

## CLI Usage

### Search

```bash
# Basic search
python scripts/graph.py search --q "planning meeting" --tenant acme-corp

# Filtered search
python scripts/graph.py search --q "budget" --type message --source outlook --tenant acme-corp --limit 20

# JSON output
python scripts/graph.py search --q "standup" --tenant acme-corp --json
```

### Execute Actions

```bash
# Reply to message
python scripts/graph.py act \
  --action message.reply \
  --id "urn:teams:message:msg-123" \
  --payload '{"body":"Thanks!"}' \
  --tenant acme-corp \
  --user admin

# Forward message
python scripts/graph.py act \
  --action message.forward \
  --id "urn:outlook:message:msg-456" \
  --payload '{"to":["user@example.com"],"comment":"FYI"}' \
  --tenant acme-corp \
  --user admin
```

### Rebuild Index

```bash
# Rebuild all
python scripts/graph.py rebuild-index

# Rebuild for tenant
python scripts/graph.py rebuild-index --tenant acme-corp
```

### Statistics

```bash
# Show index stats
python scripts/graph.py stats --tenant acme-corp

# JSON output
python scripts/graph.py stats --tenant acme-corp --json
```

### List Actions

```bash
# List all actions
python scripts/graph.py list-actions

# Filter by type
python scripts/graph.py list-actions --type message
```

## Dashboard Integration

The Observability dashboard includes URG panel:

```python
# Location: dashboards/observability_tab.py
# Section: Unified Resource Graph (URG)

Features:
- Index statistics (total, by type, by source)
- Quick search (top 10 results)
- Tenant selector
- Links to CLI and documentation
```

## Performance Considerations

### In-Memory Index

- **Pros**: Sub-second search, no database required
- **Cons**: Memory usage scales with resource count
- **Recommendation**: For 100K resources, expect ~200-500 MB RAM

### Shard Loading

- **Cold Start**: All shards loaded into memory on init
- **Time**: ~1-2 seconds per 10K resources
- **Optimization**: Keep shard files under 10K lines each

### Search Performance

- **Typical**: 1-10ms for queries on 10K resources
- **Scaling**: Linear with result set size
- **Optimization**: Use type/source filters to narrow search

## Security

### RBAC

- **Search**: Any authenticated user (filtered by their tenant)
- **Actions**: Admin role required
- **Ingestion**: Operator role required (via connector RBAC)

### Audit Logging

All action executions logged:

```python
# Location: audit/{YYYY-MM-DD}.jsonl

{
  "timestamp": "2025-01-15T10:30:00Z",
  "tenant_id": "acme-corp",
  "user_id": "admin",
  "action": "run_workflow",
  "resource_type": "message",
  "resource_id": "urn:teams:message:msg-123",
  "result": "success",
  "metadata": {"action": "message.reply", "payload": {...}}
}
```

### Data Sensitivity

- **No Encryption at Rest**: JSONL files stored unencrypted
- **Recommendation**: Enable filesystem encryption for `logs/graph/`
- **PII**: Resource snippets may contain PII - handle accordingly

## Environment Variables

```bash
# URG store path (default: logs/graph)
URG_STORE_PATH=logs/graph

# Max search results (default: 200)
URG_MAX_RESULTS=200

# Default tenant for CLI (default: local-dev)
GRAPH_DEFAULT_TENANT=local-dev
```

## Extension Points

### Custom Actions

Register custom actions:

```python
from src.graph.actions import register_action

@register_action("custom_type", "my_action")
def my_action_handler(resource: dict, payload: dict, *, user_id: str, tenant: str) -> dict:
    # Implement action logic
    return {"status": "custom_success", "data": {...}}
```

### Custom Normalization

Extend CP-CAL for new resource types:

```python
# In src/connectors/cp_cal.py

@staticmethod
def normalize_custom_type(service: str, resource: dict) -> dict:
    # Normalize custom resource type
    return {
        "id": resource["id"],
        "type": "custom_type",
        # ... other fields
    }
```

## Troubleshooting

### No Search Results

1. **Check tenant**: Ensure correct tenant parameter
2. **Verify ingestion**: Run `python scripts/graph.py stats --tenant <tenant>`
3. **Check shards**: List files in `logs/graph/<tenant>/`
4. **Rebuild index**: `python scripts/graph.py rebuild-index --tenant <tenant>`

### Action Execution Fails

1. **Check RBAC**: User must have Admin role
2. **Verify resource**: Ensure graph ID exists and has `original_id` in metadata
3. **Check connector**: Connector must be available and configured
4. **Review audit logs**: Check `audit/*.jsonl` for error details

### Index Performance Issues

1. **Shard Size**: Keep shards under 10K resources each
2. **Memory**: Monitor RAM usage, consider pruning old resources
3. **Token Count**: Reduce snippet length to decrease token count

## Future Enhancements

Potential improvements for future sprints:

- **Real-time Ingestion**: Webhook-based live updates
- **Full-Text Search**: Elasticsearch/OpenSearch backend
- **Graph Relationships**: Track reply chains, thread hierarchies
- **Smart Suggestions**: ML-based query completion
- **Batch Actions**: Execute actions on multiple resources
- **Export**: Export search results to CSV/JSON
- **Scheduled Ingestion**: Cron-based periodic snapshots

## References

- **CP-CAL Documentation**: See `src/connectors/cp_cal.py`
- **Connector SDK**: See `docs/CONNECTOR_SDK.md`
- **Security**: See `docs/SECURITY.md`
- **Operations**: See `docs/OPERATIONS.md`

---

**Last Updated**: 2025-10-04
**Sprint**: 38
**Status**: Production Ready
