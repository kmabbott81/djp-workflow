# Outlook Connector

Microsoft Outlook connector using Graph API for email, calendar, and contacts integration.

## Overview

The Outlook connector provides CRUD operations for:
- **Messages**: Send, read, update, and delete emails
- **Folders**: Manage mail folders
- **Contacts**: Manage contact information

## Setup

### Prerequisites

1. Microsoft Azure App Registration
2. Graph API permissions:
   - `Mail.Read`
   - `Mail.Send`
   - `Mail.ReadWrite`
   - `Contacts.Read`
   - `Contacts.ReadWrite`
   - `Calendars.Read` (for calendar events)

### Environment Variables

```bash
# Required
MS_CLIENT_ID=your-client-id
MS_TENANT_ID=your-tenant-id
MS_CLIENT_SECRET=your-client-secret

# Optional
GRAPH_BASE_URL=https://graph.microsoft.com/v1.0
OUTLOOK_DEFAULT_USER_ID=me
OAUTH_TOKEN_PATH=logs/connectors/tokens.jsonl

# Mode control
DRY_RUN=true          # Mock mode (default)
LIVE=false            # Real API mode (requires DRY_RUN=false)

# Observability
RETRY_MAX_ATTEMPTS=3
CONNECTOR_METRICS_PATH=logs/connectors/metrics.jsonl
```

### OAuth2 Token Setup

```python
from src.connectors.oauth2 import save_token

# Save token for Outlook (multi-tenant support)
save_token(
    connector_id="outlook",
    access_token="your-access-token",
    refresh_token="your-refresh-token",
    expires_at="2025-10-05T12:00:00Z",
    service_id="outlook:your-tenant-id"  # Unique per tenant
)
```

## Modes

### DRY_RUN Mode (Default)

Safe for CI/CD pipelines. No real API calls.

```bash
export DRY_RUN=true
export LIVE=false
```

### LIVE Mode

Real API calls to Microsoft Graph.

```bash
export DRY_RUN=false
export LIVE=true
```

## Resource Types

### Messages

List, read, send, update, and delete emails.

**List messages:**
```python
connector = OutlookConnector("outlook", "tenant1", "user1")
messages = connector.list_resources("messages")
# Optional: filter by folder
messages = connector.list_resources("messages", folder_id="inbox")
```

**Get specific message:**
```python
message = connector.get_resource("messages", "msg-123")
```

**Send message:**
```python
payload = {
    "message": {
        "subject": "Hello",
        "body": {
            "contentType": "text",
            "content": "Test email body"
        },
        "toRecipients": [
            {"emailAddress": {"address": "recipient@example.com"}}
        ]
    }
}
result = connector.create_resource("messages", payload)
```

**Update message (mark as read):**
```python
payload = {"isRead": True}
result = connector.update_resource("messages", "msg-123", payload)
```

**Delete message:**
```python
result = connector.delete_resource("messages", "msg-123")
```

### Folders

Manage mail folders.

**List folders:**
```python
folders = connector.list_resources("folders")
```

**Get folder:**
```python
folder = connector.get_resource("folders", "folder-id")
```

**Create folder:**
```python
payload = {"displayName": "Archive"}
result = connector.create_resource("folders", payload)
```

### Contacts

Manage contacts.

**List contacts:**
```python
contacts = connector.list_resources("contacts")
```

**Get contact:**
```python
contact = connector.get_resource("contacts", "contact-id")
```

**Create contact:**
```python
payload = {
    "givenName": "John",
    "surname": "Doe",
    "emailAddresses": [
        {"address": "john@example.com", "name": "John Doe"}
    ],
    "businessPhones": ["+1-555-0100"]
}
result = connector.create_resource("contacts", payload)
```

## CLI Examples

```bash
# List messages (DRY_RUN mode)
python -c "
from src.connectors.outlook_api import OutlookConnector
connector = OutlookConnector('outlook', 'tenant1', 'user1')
messages = connector.list_resources('messages')
print(f'Found {len(messages)} messages')
"

# Send email (requires Admin role)
export USER_ROLE=Admin
python -c "
from src.connectors.outlook_api import OutlookConnector
connector = OutlookConnector('outlook', 'tenant1', 'user1')
payload = {
    'message': {
        'subject': 'Test',
        'body': {'contentType': 'text', 'content': 'Test body'},
        'toRecipients': [{'emailAddress': {'address': 'test@example.com'}}]
    }
}
result = connector.create_resource('messages', payload)
print('Email sent:', result)
"
```

## RBAC

Write operations (create, update, delete) require **Admin** role:

```bash
export USER_ROLE=Admin
```

Role hierarchy:
- **Admin**: Full access
- **Deployer**: Read access
- **Operator**: Read access
- **Viewer**: Read access

## Error Handling

The connector includes:
- **Retry with exponential backoff** (rate limits, server errors)
- **Circuit breaker** (prevents cascading failures)
- **Metrics recording** (all operations logged)

## Multi-Tenant Support

The Outlook connector supports multiple tenants via the `service_id` parameter:

```python
# Token key format: "outlook:{tenant_id}"
connector = OutlookConnector("outlook", "tenant-abc", "user1")
# Internally uses token: "outlook:outlook:tenant-abc"
```

## Testing

Run tests in DRY_RUN mode (CI-safe):

```bash
pytest tests/test_outlook_connector_dryrun.py -v
```

Run LIVE tests (requires OAuth token):

```bash
export LIVE=true
pytest tests/test_outlook_connector_dryrun.py -v -m live
```

## Observability

Metrics are recorded to `logs/connectors/metrics.jsonl`:

```json
{
  "connector_id": "outlook",
  "endpoint": "users/me/messages",
  "status": "success",
  "duration_ms": 123.45,
  "timestamp": "2025-10-04T12:00:00Z"
}
```

## See Also

- [CONNECTORS.md](CONNECTORS.md) - Connector overview
- [CONNECTOR_SDK.md](CONNECTOR_SDK.md) - Building custom connectors
- [CONNECTOR_CROSSPLATFORM.md](CONNECTOR_CROSSPLATFORM.md) - Cross-platform abstraction
- [CONNECTOR_OBSERVABILITY.md](CONNECTOR_OBSERVABILITY.md) - Monitoring and metrics
