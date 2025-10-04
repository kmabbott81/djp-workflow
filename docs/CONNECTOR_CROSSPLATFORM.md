# Cross-Platform Connector Abstraction Layer (CP-CAL)

Unified abstraction for integrating multiple communication platforms (Teams, Outlook, Slack, etc.).

## Overview

CP-CAL provides:
1. **Endpoint Registry**: URL templates for service APIs
2. **Schema Adapters**: Normalize data across platforms
3. **Multi-Service Token Management**: Isolated tokens per tenant/service

## Architecture

### Endpoint Mapping

Each service + resource type combination has an `EndpointMap`:

```python
from src.connectors.cp_cal import EndpointMap, ENDPOINT_REGISTRY

# Teams messages
teams_messages = ENDPOINT_REGISTRY[("teams", "messages")]
print(teams_messages.list_url)
# Output: "teams/{team_id}/channels/{channel_id}/messages"

# Outlook messages
outlook_messages = ENDPOINT_REGISTRY[("outlook", "messages")]
print(outlook_messages.list_url)
# Output: "users/{user_id}/messages"
```

### Schema Normalization

Convert service-specific schemas to a unified format:

```python
from src.connectors.cp_cal import SchemaAdapter

# Normalize Teams message
teams_message = {
    "id": "msg-123",
    "subject": "Test",
    "body": {"content": "Body text"},
    "from": {"user": {"displayName": "John Doe"}},
    "createdDateTime": "2025-10-04T12:00:00Z"
}
normalized = SchemaAdapter.normalize_message("teams", teams_message)

# Normalized format:
# {
#   "id": "msg-123",
#   "subject": "Test",
#   "body": "Body text",
#   "from": "John Doe",
#   "timestamp": "2025-10-04T12:00:00Z",
#   "metadata": {...}
# }
```

### Denormalization

Convert unified format back to service-specific schema:

```python
normalized_message = {
    "subject": "Hello",
    "body": "Email body",
    "metadata": {"importance": "high"}
}

# Convert to Outlook format
outlook_format = SchemaAdapter.denormalize_message("outlook", normalized_message)
# {
#   "subject": "Hello",
#   "body": {"contentType": "text", "content": "Email body"},
#   "importance": "high"
# }
```

## Adding New Connectors

### Step 1: Define Endpoint Map

Add entry to `ENDPOINT_REGISTRY`:

```python
# In src/connectors/cp_cal.py
ENDPOINT_REGISTRY[("myservice", "messages")] = EndpointMap(
    list_url="myservice/v1/channels/{channel_id}/messages",
    get_url="myservice/v1/messages/{resource_id}",
    create_url="myservice/v1/channels/{channel_id}/messages",
    update_url="myservice/v1/messages/{resource_id}",
    delete_url="myservice/v1/messages/{resource_id}"
)
```

### Step 2: Implement Schema Adapters

Add normalization methods to `SchemaAdapter`:

```python
@staticmethod
def normalize_message(service: str, message: dict) -> dict:
    if service == "myservice":
        return {
            "id": message.get("messageId"),
            "subject": message.get("title"),
            "body": message.get("content"),
            "from": message.get("sender", {}).get("name"),
            "timestamp": message.get("sentAt"),
            "metadata": {}
        }
    # ... existing services
```

### Step 3: Create Connector Class

Inherit from `Connector` base class:

```python
from src.connectors.base import Connector
from src.connectors.cp_cal import get_endpoint_map

class MyServiceConnector(Connector):
    def __init__(self, connector_id: str, tenant_id: str, user_id: str):
        super().__init__(connector_id, tenant_id, user_id)
        self.token_service_id = f"myservice:{tenant_id}"

    def list_resources(self, resource_type: str, **kwargs):
        endpoint_map = get_endpoint_map("myservice", resource_type)
        url = endpoint_map.list_url.format(**kwargs)
        return self._call_api("GET", url)
```

### Step 4: Add Tests

Create test file following the pattern:

```python
# tests/test_myservice_connector_dryrun.py
def test_myservice_dryrun_list_messages(myservice_dryrun):
    messages = myservice_dryrun.list_resources("messages")
    assert isinstance(messages, list)
```

## Schema Normalization Patterns

### Message Schema

Unified message format:

```python
{
    "id": "unique-message-id",
    "subject": "Message subject (if applicable)",
    "body": "Plain text body",
    "from": "Sender name or email",
    "timestamp": "ISO 8601 timestamp",
    "metadata": {
        # Service-specific extras
    }
}
```

### Contact Schema

Unified contact format:

```python
{
    "id": "unique-contact-id",
    "name": "Display name",
    "email": "Primary email address",
    "phone": "Primary phone number",
    "metadata": {
        # Service-specific extras (job title, company, etc.)
    }
}
```

### Event Schema

Unified event format:

```python
{
    "id": "unique-event-id",
    "title": "Event title/subject",
    "start": "ISO 8601 start time",
    "end": "ISO 8601 end time",
    "location": "Location string",
    "metadata": {
        # Service-specific extras (organizer, meeting link, etc.)
    }
}
```

## Multi-Service Token Handling

CP-CAL supports isolated tokens per service and tenant:

### Token Key Format

```
{connector_id}:{service_id}
```

Examples:
- `outlook:outlook:tenant-abc`
- `teams:teams:tenant-xyz`
- `slack:slack:workspace-123`

### Saving Tokens

```python
from src.connectors.oauth2 import save_token

# Save Outlook token for tenant-abc
save_token(
    connector_id="outlook",
    access_token="token-abc",
    service_id="outlook:tenant-abc"
)

# Save Teams token for tenant-xyz
save_token(
    connector_id="teams",
    access_token="token-xyz",
    service_id="teams:tenant-xyz"
)
```

### Loading Tokens

```python
from src.connectors.oauth2 import load_token

# Load Outlook token for tenant-abc
token = load_token("outlook", "outlook:tenant-abc")

# Load Teams token for tenant-xyz
token = load_token("teams", "teams:tenant-xyz")
```

### Backward Compatibility

Old tokens without `service_id` default to `"default"`:

```python
# Old format (still supported)
token = load_token("outlook")  # Uses service_id="default"
```

## Supported Services

| Service | Messages | Folders | Contacts | Events |
|---------|----------|---------|----------|--------|
| Teams   | Yes      | No      | No       | No     |
| Outlook | Yes      | Yes     | Yes      | Yes*   |
| Slack   | Template | No      | No       | No     |

\* Events support via Calendar API (future sprint)

## Usage Examples

### Cross-Platform Message Search

```python
from src.connectors.teams import TeamsConnector
from src.connectors.outlook_api import OutlookConnector
from src.connectors.cp_cal import SchemaAdapter

# Search Teams
teams = TeamsConnector("teams", "tenant1", "user1")
teams_messages = teams.list_resources("messages", team_id="t1", channel_id="c1")
teams_normalized = [SchemaAdapter.normalize_message("teams", m) for m in teams_messages]

# Search Outlook
outlook = OutlookConnector("outlook", "tenant1", "user1")
outlook_messages = outlook.list_resources("messages")
outlook_normalized = [SchemaAdapter.normalize_message("outlook", m) for m in outlook_messages]

# Combine results
all_messages = teams_normalized + outlook_normalized
all_messages.sort(key=lambda m: m["timestamp"], reverse=True)
```

### Cross-Platform Contact Sync

```python
from src.connectors.outlook_api import OutlookConnector
from src.connectors.cp_cal import SchemaAdapter

# Fetch Outlook contacts
outlook = OutlookConnector("outlook", "tenant1", "user1")
outlook_contacts = outlook.list_resources("contacts")

# Normalize to unified format
unified_contacts = [
    SchemaAdapter.normalize_contact("outlook", c)
    for c in outlook_contacts
]

# Can now sync to other platforms using denormalize_contact()
```

## Testing

### Unit Tests

Test endpoint maps and schema adapters:

```bash
pytest tests/test_cp_cal.py -v
```

### Integration Tests

Test multiple connectors together:

```bash
pytest tests/test_outlook_connector_dryrun.py tests/test_teams_connector_dryrun.py -v
```

## Future Enhancements

1. **Calendar Events**: Outlook Calendar API integration
2. **Slack Full Support**: Complete Slack connector (beyond template)
3. **Google Workspace**: Gmail, Calendar, Contacts
4. **Zoom**: Meetings, webinars
5. **Unified Search**: Cross-platform semantic search

## See Also

- [CONNECTORS.md](CONNECTORS.md) - Connector overview
- [CONNECTORS_TEAMS.md](CONNECTORS_TEAMS.md) - Teams connector
- [CONNECTORS_OUTLOOK.md](CONNECTORS_OUTLOOK.md) - Outlook connector
- [CONNECTOR_SDK.md](CONNECTOR_SDK.md) - Building custom connectors
