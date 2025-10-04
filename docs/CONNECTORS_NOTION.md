# Notion Connector Documentation

## Overview

The Notion connector provides integration with Notion's REST API, enabling read/write operations on pages, databases, and blocks. It supports both DRY_RUN (mock) and LIVE modes with OAuth2 authentication.

## Features

- Full CRUD operations on Notion resources (pages, databases, blocks)
- OAuth2 authentication with tenant isolation
- Retry logic with exponential backoff for transient errors
- Circuit breaker pattern for fault tolerance
- Metrics recording for observability
- RBAC enforcement (reads: Operator+, writes: Admin)
- CP-CAL schema normalization (pages→documents, databases→collections)
- URG integration for search and discovery

## Setup

### 1. Create Notion Integration

1. Go to https://www.notion.so/my-integrations
2. Click "+ New integration"
3. Give it a name (e.g., "My Workflow Integration")
4. Select the workspace
5. Set capabilities:
   - Read content: ✓
   - Update content: ✓
   - Insert content: ✓
6. Copy the "Internal Integration Token"

### 2. Share Pages/Databases with Integration

For each Notion page or database you want to access:

1. Open the page/database in Notion
2. Click "..." → "Add connections"
3. Search for your integration name
4. Click "Confirm"

### 3. Configure Environment Variables

```bash
# Authentication (choose one)
export NOTION_API_TOKEN="secret_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
# OR use OAuth2 token store (see OAuth2 section below)

# Mode
export DRY_RUN="false"  # Set to true for offline testing
export LIVE="true"      # Set to true for production use

# API Configuration
export NOTION_API_BASE="https://api.notion.com/v1"  # Default
export NOTION_VERSION="2022-06-28"                  # API version header

# Retry Configuration
export RETRY_MAX_ATTEMPTS="3"
export NOTION_RETRY_STATUS="429,500,502,503,504"

# RBAC
export CONNECTOR_RBAC_ROLE="Operator"  # Minimum role for reads
# Writes always require Admin role
```

## OAuth2 Authentication

For multi-tenant environments, use OAuth2 token storage:

```python
from src.connectors.oauth2 import save_token

# Save token for tenant
save_token(
    connector_id="notion",
    service_id="notion:tenant-123",
    token_data={
        "access_token": "secret_...",
        "token_type": "bearer",
        "expires_at": 0,  # Notion tokens don't expire
    }
)
```

Required OAuth Scopes:
- No specific scopes for internal integrations
- Public OAuth requires content read/write permissions

## DRY_RUN Mode

Test without hitting live API:

```bash
export DRY_RUN="true"
export LIVE="false"

python -c "
from src.connectors.notion import NotionConnector

conn = NotionConnector('test', 'tenant-1', 'user-1')
conn.connect()
result = conn.list_resources('pages')
print(result.data)
"
```

Mock responses are read from `logs/connectors/notion_mock.jsonl`.

## LIVE Mode

Connect to real Notion API:

```bash
export DRY_RUN="false"
export LIVE="true"
export NOTION_API_TOKEN="secret_your_token_here"

python -c "
from src.connectors.notion import NotionConnector

conn = NotionConnector('notion-prod', 'tenant-1', 'user-1')
result = conn.connect()
print(result.status, result.message)
"
```

## Usage Examples

### List Pages

```python
from src.connectors.notion import NotionConnector

conn = NotionConnector('notion-1', 'tenant-1', 'user-1')
conn.connect()

# List all pages
result = conn.list_resources('pages')
if result.status == 'success':
    for page in result.data:
        print(page['id'], page.get('properties', {}).get('Name'))

# Search pages by title
result = conn.list_resources('pages', filters={'query': 'Project'})
```

### Get Specific Page

```python
result = conn.get_resource('pages', 'page-abc-123')
if result.status == 'success':
    page = result.data
    print(page['id'], page['created_time'], page['properties'])
```

### Create Page

```python
payload = {
    'parent': {'database_id': 'database-xyz-789'},
    'properties': {
        'Name': {
            'title': [
                {
                    'type': 'text',
                    'text': {'content': 'New Project Plan'}
                }
            ]
        },
        'Status': {
            'select': {'name': 'In Progress'}
        }
    }
}

result = conn.create_resource('pages', payload)
if result.status == 'success':
    print('Created page:', result.data['id'])
```

### Update Page

```python
payload = {
    'properties': {
        'Status': {
            'select': {'name': 'Completed'}
        }
    }
}

result = conn.update_resource('pages', 'page-abc-123', payload)
```

### Delete (Archive) Page

```python
result = conn.delete_resource('pages', 'page-abc-123')
# Note: This archives the page, doesn't permanently delete
```

### List Databases

```python
result = conn.list_resources('databases')
if result.status == 'success':
    for db in result.data:
        print(db['id'], db.get('title', [{}])[0].get('plain_text', ''))
```

### Query Database

```python
# To query a database, use get_resource with filters
# (This is a simplified example; full query requires database_id in filters)
result = conn.list_resources('databases', filters={'query': 'Projects'})
```

### List Blocks

```python
# List blocks in a page
result = conn.list_resources('blocks', filters={'page_id': 'page-abc-123'})
if result.status == 'success':
    for block in result.data:
        print(block['type'], block['id'])
```

### Append Blocks to Page

```python
payload = {
    'parent_id': 'page-abc-123',
    'children': [
        {
            'object': 'block',
            'type': 'heading_2',
            'heading_2': {
                'rich_text': [
                    {
                        'type': 'text',
                        'text': {'content': 'New Section'}
                    }
                ]
            }
        },
        {
            'object': 'block',
            'type': 'paragraph',
            'paragraph': {
                'rich_text': [
                    {
                        'type': 'text',
                        'text': {'content': 'This is a new paragraph.'}
                    }
                ]
            }
        }
    ]
}

result = conn.create_resource('blocks', payload)
```

## CLI Usage

```bash
# List pages
python scripts/connectors.py notion list pages --tenant tenant-1

# Get specific page
python scripts/connectors.py notion get page-abc-123 --tenant tenant-1

# Create page (requires JSON payload file)
python scripts/connectors.py notion create pages payload.json --tenant tenant-1

# Update page
python scripts/connectors.py notion update page-abc-123 update.json --tenant tenant-1

# Delete (archive) page
python scripts/connectors.py notion delete page-abc-123 --tenant tenant-1
```

## URG Integration

Ingest Notion pages and databases into URG:

```python
from src.connectors.ingest import ingest_connector_snapshot

# Ingest pages
result = ingest_connector_snapshot(
    'notion',
    'pages',
    tenant='tenant-1',
    user_id='user-1',
    limit=100
)
print(f"Ingested {result['count']} pages")

# Ingest databases
result = ingest_connector_snapshot(
    'notion',
    'databases',
    tenant='tenant-1',
    user_id='user-1',
    limit=50
)
print(f"Ingested {result['count']} databases")
```

Schema normalization:
- **Pages** → URG `document` type (labeled "notion", "page")
- **Databases** → URG `collection` type (labeled "notion", "database")
- **Blocks** → URG `content` type (labeled "notion", "block")

## Rate Limits

Notion API rate limits:
- **Average rate**: 3 requests per second
- **Burst rate**: Higher for short periods
- **429 responses**: Include Retry-After header

The connector handles rate limits automatically with:
- Exponential backoff
- Retry-After header respect
- Circuit breaker (opens after 5 consecutive failures)

## Webhooks

### Setup Webhook Endpoint

Notion doesn't have native webhooks yet (as of API v1). To receive updates:

1. Use Notion's Change Log API (not yet public)
2. Or poll for changes using `last_edited_time` filter
3. Or use third-party webhook services (e.g., Zapier, Make)

### Webhook Event Normalization

If using custom webhook integration:

```python
from src.connectors.webhooks import ingest_event

payload = {
    'type': 'page.updated',
    'page': {
        'object': 'page',
        'id': 'page-abc-123',
        'last_edited_time': '2023-01-02T15:30:00.000Z',
        'properties': {...}
    },
    'timestamp': '2023-01-02T15:30:00.000Z'
}

normalized = ingest_event('notion', payload)
# Returns standardized event structure
```

## Troubleshooting

### Connection Failed

```
Error: No Notion token found
```

**Solution**: Set `NOTION_API_TOKEN` environment variable or configure OAuth2 token.

### Permission Denied

```
Error: object_not_found
```

**Cause**: Page/database not shared with integration.

**Solution**:
1. Open the page in Notion
2. Click "..." → "Add connections"
3. Select your integration

### Rate Limited

```
Error: Rate limited
```

**Cause**: Exceeding 3 requests/second average.

**Solution**:
- Connector retries automatically
- Reduce request frequency if persistent
- Check RETRY_MAX_ATTEMPTS setting

### Invalid Request

```
Error: validation_error
```

**Cause**: Malformed API request.

**Solution**:
- Check payload matches Notion API schema
- Verify property types match database schema
- See https://developers.notion.com/reference for API docs

### Circuit Breaker Open

```
Error: Circuit breaker open for notion-tenant-1
```

**Cause**: Too many consecutive failures (5+).

**Solution**:
- Check Notion API status: https://status.notion.so
- Verify credentials are valid
- Wait 60 seconds for circuit to half-open and retry

## Security

### Token Storage

- Internal Integration Tokens are long-lived (don't expire)
- Store in secure secret manager (e.g., AWS Secrets Manager, HashiCorp Vault)
- Use OAuth2 token store for multi-tenant isolation
- Never commit tokens to version control

### RBAC

- Read operations require `Operator` role or higher
- Write operations require `Admin` role
- Configure via `CONNECTOR_RBAC_ROLE` environment variable
- Override per-operation with connector.required_role

### Audit Logging

All connector operations are logged:
- Metrics recorded to `logs/connectors_metrics.jsonl`
- Circuit breaker events logged
- DRY_RUN calls logged to `logs/connectors/notion_mock.jsonl`

## API Reference

### NotionConnector

```python
class NotionConnector(Connector):
    """Notion connector with OAuth2, retry, circuit breaker, metrics."""

    def __init__(self, connector_id: str, tenant_id: str, user_id: str)

    def connect(self) -> ConnectorResult
    def disconnect(self) -> ConnectorResult

    def list_resources(self, resource_type: str, filters: Optional[dict]) -> ConnectorResult
    def get_resource(self, resource_type: str, resource_id: str) -> ConnectorResult
    def create_resource(self, resource_type: str, payload: dict) -> ConnectorResult
    def update_resource(self, resource_type: str, resource_id: str, payload: dict) -> ConnectorResult
    def delete_resource(self, resource_type: str, resource_id: str) -> ConnectorResult
```

### Supported Resource Types

- `pages`: Notion pages (documents)
- `databases`: Notion databases (collections)
- `blocks`: Content blocks within pages

### ConnectorResult

```python
@dataclass
class ConnectorResult:
    status: str      # "success", "error", "denied"
    data: Any = None
    message: str = ""
```

## Resources

- Notion API Documentation: https://developers.notion.com/reference
- Notion API Status: https://status.notion.so
- Integration Setup: https://www.notion.so/my-integrations
- API Versioning: https://developers.notion.com/reference/versioning

## Testing

Run connector tests:

```bash
# DRY_RUN tests (offline, CI-safe)
pytest tests/test_notion_connector_dryrun.py -v

# Resilience tests (offline, uses MockHTTPTransport)
pytest tests/test_notion_connector_resilience.py -v

# Webhook tests
pytest tests/test_notion_webhooks.py -v

# All Notion tests
pytest tests/ -k notion -v
```

## Migration Notes

When upgrading Notion API versions:

1. Update `NOTION_VERSION` environment variable
2. Test in DRY_RUN mode first
3. Review API changelog: https://developers.notion.com/reference/changes-by-version
4. Update mock responses in notion_mock.jsonl if schema changed

## Support

For issues:
1. Check logs in `logs/connectors_metrics.jsonl`
2. Verify Notion API status
3. Review troubleshooting section above
4. Contact team via internal support channels
