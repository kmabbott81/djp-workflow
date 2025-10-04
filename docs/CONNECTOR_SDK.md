# Connector SDK Documentation

**Version:** 1.0 (Sprint 34B)
**Status:** ✅ Production Ready

---

## Overview

The Connector SDK provides a standardized interface for integrating external systems (Outlook, Slack, Salesforce, webhooks, etc.) into DJP workflows. All connectors implement the `Connector` base class and are managed via a JSONL registry.

## Base Connector Interface

### Class: `Connector` (Abstract)

Located in `src/connectors/base.py`

```python
from src.connectors.base import Connector, ConnectorResult

class MyConnector(Connector):
    def __init__(self, connector_id: str, tenant_id: str, user_id: str):
        super().__init__(connector_id, tenant_id, user_id)
        # Custom initialization

    def connect(self) -> ConnectorResult:
        # Establish connection

    def disconnect(self) -> ConnectorResult:
        # Close connection

    def list_resources(self, resource_type: str, filters=None) -> ConnectorResult:
        # List resources

    def get_resource(self, resource_type: str, resource_id: str) -> ConnectorResult:
        # Get single resource

    def create_resource(self, resource_type: str, payload: dict) -> ConnectorResult:
        # Create new resource

    def update_resource(self, resource_type: str, resource_id: str, payload: dict) -> ConnectorResult:
        # Update resource

    def delete_resource(self, resource_type: str, resource_id: str) -> ConnectorResult:
        # Delete resource
```

### ConnectorResult

All connector methods return `ConnectorResult`:

```python
@dataclass
class ConnectorResult:
    status: str  # "success", "error", "denied"
    data: Optional[Any] = None
    message: str = ""
```

**Status Values:**
- `success` - Operation completed successfully
- `error` - Operation failed (validation, network, etc.)
- `denied` - RBAC denied access

## RBAC Enforcement

All connectors enforce role-based access control via `check_rbac()`:

- Reads `CONNECTOR_RBAC_ROLE` (default: `Operator`)
- Compares user's role against required role
- Role hierarchy: Viewer(0) < Author(1) < Operator(2) < Auditor(3) < Compliance(4) < Admin(5)

```python
def connect(self) -> ConnectorResult:
    if not self.check_rbac():
        return ConnectorResult(
            status="denied",
            message=f"User {self.user_id} lacks {self.required_role} role"
        )
    # ... connection logic
```

## Connector Registry

Connectors are registered in a JSONL append-only log at `CONNECTOR_REGISTRY_PATH` (default: `logs/connectors.jsonl`).

### Registry Entry Format

```json
{
  "connector_id": "outlook",
  "module": "src.connectors.mock_outlook",
  "class_name": "MockOutlookConnector",
  "enabled": true,
  "auth_type": "env",
  "scopes": ["read", "write"],
  "created_at": "2025-10-03T12:00:00",
  "updated_at": "2025-10-03T12:00:00"
}
```

### Registry Operations

```python
from src.connectors.registry import (
    register_connector,
    load_connector,
    list_enabled_connectors,
    enable_connector,
    disable_connector
)

# Register
register_connector(
    connector_id="outlook",
    module="src.connectors.mock_outlook",
    class_name="MockOutlookConnector",
    enabled=True,
    auth_type="env",
    scopes=["read", "write"]
)

# Load
connector = load_connector("outlook", tenant_id="tenant1", user_id="user1")

# List enabled
connectors = list_enabled_connectors()

# Enable/disable
enable_connector("outlook")
disable_connector("outlook")
```

## Built-in Connectors

### Sandbox Connector

In-memory connector for testing and demos. No external dependencies.

**Features:**
- In-memory CRUD operations
- Configurable latency (`SANDBOX_LATENCY_MS`)
- Error injection (`SANDBOX_ERROR_RATE`)

**Usage:**
```python
from src.connectors.sandbox import SandboxConnector

connector = SandboxConnector("sandbox", "tenant1", "user1")
connector.connect()

# Create
connector.create_resource("items", {"id": "item1", "name": "Test"})

# List
result = connector.list_resources("items")
print(result.data)  # [{"id": "item1", "name": "Test"}]
```

### Mock Outlook Connector

Simulates Outlook/Exchange email operations using local JSONL storage.

**Features:**
- JSONL-based persistence
- Dry-run mode support
- Resource types: messages, folders, contacts

**Environment:**
- `OUTLOOK_TOKEN` - Placeholder token for config validation
- `DRY_RUN` - Enable dry-run mode (default: true)

**Usage:**
```python
from src.connectors.mock_outlook import MockOutlookConnector

connector = MockOutlookConnector("outlook", "tenant1", "user1")
connector.connect()

# Send email (dry-run)
result = connector.create_resource("messages", {
    "to": "alice@example.com",
    "subject": "Test Email",
    "body": "Hello World"
})
```

## CLI Usage

The `scripts/connectors.py` CLI provides management operations:

### List Connectors

```bash
python scripts/connectors.py list
python scripts/connectors.py list --json
```

### Register Connector

```bash
python scripts/connectors.py register \
  --id outlook \
  --module src.connectors.mock_outlook \
  --class MockOutlookConnector \
  --scopes read,write \
  --user admin \
  --tenant default
```

### Enable/Disable

```bash
python scripts/connectors.py enable outlook --user admin --tenant default
python scripts/connectors.py disable outlook --user admin --tenant default
```

### Test Connector

```bash
# List resources
python scripts/connectors.py test sandbox --action list --user admin --tenant default

# Get resource
python scripts/connectors.py test sandbox --action get \
  --resource-type items --resource-id item1 \
  --user admin --tenant default

# Create resource
python scripts/connectors.py test sandbox --action create \
  --resource-type items \
  --payload '{"id": "item1", "name": "Test"}' \
  --user admin --tenant default

# Delete resource
python scripts/connectors.py test sandbox --action delete \
  --resource-type items --resource-id item1 \
  --user admin --tenant default
```

## Error Handling

Connectors should handle errors gracefully:

```python
def get_resource(self, resource_type: str, resource_id: str) -> ConnectorResult:
    if not self.check_rbac():
        return ConnectorResult(status="denied", message="Insufficient permissions")

    if not self.connected:
        return ConnectorResult(status="error", message="Not connected")

    try:
        # ... fetch resource
        return ConnectorResult(status="success", data=resource)
    except KeyError:
        return ConnectorResult(status="error", message=f"Resource {resource_id} not found")
    except Exception as e:
        return ConnectorResult(status="error", message=f"Unexpected error: {e}")
```

## Tenant Isolation

Connectors must enforce tenant isolation:

- Accept `tenant_id` in constructor
- Scope all operations to tenant
- Prefix storage paths with tenant ID
- Include tenant ID in audit logs

Example:
```python
def __init__(self, connector_id: str, tenant_id: str, user_id: str):
    super().__init__(connector_id, tenant_id, user_id)
    # Tenant-isolated storage
    self.storage_path = Path("logs") / f"mock_outlook_{tenant_id}.jsonl"
```

## Best Practices

### 1. Always Check RBAC
```python
if not self.check_rbac():
    return ConnectorResult(status="denied", message="Insufficient role")
```

### 2. Require Connection
```python
if not self.connected:
    return ConnectorResult(status="error", message="Not connected")
```

### 3. Return Structured Results
```python
# Good
return ConnectorResult(status="success", data=items, message="Listed 10 items")

# Bad
return items  # No error handling
```

### 4. Handle Filters Gracefully
```python
def list_resources(self, resource_type, filters=None):
    resources = self._fetch_all(resource_type)

    if filters:
        resources = [r for r in resources if self._matches_filters(r, filters)]

    return ConnectorResult(status="success", data=resources)
```

### 5. Support Dry-Run Mode
```python
def create_resource(self, resource_type, payload):
    if self.dry_run:
        return ConnectorResult(
            status="success",
            data=payload,
            message=f"[DRY-RUN] Would create {resource_type}"
        )
    # ... actual creation
```

## Testing

All connectors should have comprehensive test coverage:

```python
def test_connector_create(connector):
    """Test resource creation."""
    connector.connect()

    payload = {"id": "item1", "name": "Test"}
    result = connector.create_resource("items", payload)

    assert result.status == "success"
    assert result.data["id"] == "item1"

def test_connector_rbac_denied(connector_no_role):
    """Test RBAC enforcement."""
    result = connector_no_role.connect()

    assert result.status == "denied"
    assert "lacks" in result.message
```

See `tests/test_connector_*.py` for examples.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `CONNECTOR_REGISTRY_PATH` | `logs/connectors.jsonl` | Connector registry location |
| `CONNECTOR_RBAC_ROLE` | `Operator` | Required role for operations |
| `SANDBOX_LATENCY_MS` | `0` | Sandbox latency simulation |
| `SANDBOX_ERROR_RATE` | `0.0` | Sandbox error injection rate |
| `OUTLOOK_TOKEN` | `placeholder` | Mock Outlook token |
| `DRY_RUN` | `true` | Enable dry-run mode |

---

**Next Steps:**
- Implement production connectors (Salesforce, Slack, etc.)
- Add OAuth2 authentication support
- Build connector health dashboard (Sprint 34C)

**See Also:**
- `docs/CONNECTORS.md` - Connector framework overview
- `docs/SECURITY.md` - RBAC and security
- `docs/OPERATIONS.md` - Deployment and troubleshooting
