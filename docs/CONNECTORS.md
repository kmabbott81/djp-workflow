# Connector Framework (Sprint 34B+)

**Status:** ✅ v1.0 Complete (Sprint 34B)

## Overview

The Connector Framework provides a standardized SDK for integrating external systems (Salesforce, Slack, email, webhooks, etc.) into DJP workflows. Connectors handle authentication, rate limiting, retries, error handling, and observability in a consistent manner.

## Goals

1. **Unified Interface**: Base `Connector` class with lifecycle hooks for all external integrations
2. **Template-Driven Configuration**: YAML-based connector definitions with variable substitution
3. **Built-in Resilience**: Automatic retry with exponential backoff, circuit breakers, rate limiting
4. **Security First**: Credential isolation per tenant, no secrets in code, audit logging
5. **Observability**: Health checks, metrics (latency/throughput/errors), structured logging

## Architecture

```
src/connectors/
├── base.py              # BaseConnector abstract class
├── registry.py          # Connector registration & discovery
├── lifecycle.py         # Lifecycle hooks (init, connect, disconnect, health_check)
├── auth/                # Authentication adapters (OAuth2, API key, JWT)
├── adapters/            # Concrete implementations
│   ├── salesforce.py
│   ├── slack.py
│   ├── email.py         # SMTP/IMAP
│   └── webhook.py
└── __init__.py

templates/connectors/    # Template definitions with connector bindings
```

## Environment Variables

(Sprint 34B will define specific env vars for each connector)

Placeholder examples:
- `CONNECTOR_RETRY_MAX_ATTEMPTS` - Max retry attempts (default: 3)
- `CONNECTOR_RETRY_BASE_DELAY_MS` - Base delay for exponential backoff (default: 100)
- `CONNECTOR_TIMEOUT_MS` - Default request timeout (default: 30000)
- `CONNECTOR_CIRCUIT_BREAKER_THRESHOLD` - Failures before circuit opens (default: 5)

## Testing Strategy

### Unit Tests
- Mock external services using `responses` library (HTTP) or test doubles
- Test retry logic, error handling, auth token refresh
- Verify rate limit enforcement

### Integration Tests
- Use sandbox/test environments provided by external services
- Validate end-to-end workflows with real API calls
- Test credential rotation and expiry scenarios

### Health Checks
- Periodic health checks via `/api/connectors/health`
- Connector status dashboard showing auth state, rate limits, error rates

## Development Roadmap

### Sprint 34B: Connector SDK v1 ✅
- [x] `Connector` abstract base class with lifecycle hooks (`src/connectors/base.py`)
- [x] `ConnectorResult` dataclass for structured responses
- [x] RBAC enforcement with role hierarchy
- [x] Connector registry with JSONL persistence (`src/connectors/registry.py`)
- [x] Sandbox connector for testing (`src/connectors/sandbox.py`)
- [x] Mock Outlook connector prototype (`src/connectors/mock_outlook.py`)
- [x] CLI toolkit (`scripts/connectors.py`)
- [x] Comprehensive test suite (5 test files, 70+ tests)
- [x] SDK documentation (`docs/CONNECTOR_SDK.md`)

### Sprint 34C: Connector Observability & Testing
- [ ] Connector health dashboard (`dashboards/connectors_tab.py`)
- [ ] Integration test suite with mock services
- [ ] Connector versioning and compatibility checks
- [ ] Automated credential rotation
- [ ] Performance metrics (latency, throughput, error rates)
- [ ] Circuit breaker dashboard

## Security Considerations

1. **Credential Storage**: Use environment variables or external secret managers (not JSONL logs)
2. **Tenant Isolation**: Each tenant's connector credentials are isolated
3. **Audit Logging**: All connector operations logged with tenant_id, user, timestamp
4. **Least Privilege**: Connectors request only required OAuth scopes
5. **Credential Rotation**: Support for zero-downtime credential updates

## Example Usage

### Sandbox Connector (In-Memory Testing)

```python
from src.connectors.sandbox import SandboxConnector

connector = SandboxConnector("sandbox", "tenant1", "user1")
connector.connect()

# Create
connector.create_resource("items", {"id": "item1", "name": "Test Item"})

# List
result = connector.list_resources("items")
print(result.data)  # [{"id": "item1", "name": "Test Item"}]

# Get
result = connector.get_resource("items", "item1")
print(result.data)

# Update
connector.update_resource("items", "item1", {"name": "Updated"})

# Delete
connector.delete_resource("items", "item1")
```

### Mock Outlook Connector (Email Simulation)

```python
from src.connectors.mock_outlook import MockOutlookConnector

connector = MockOutlookConnector("outlook", "tenant1", "user1")
connector.connect()

# Send email (dry-run mode by default)
result = connector.create_resource("messages", {
    "to": "alice@example.com",
    "subject": "Meeting Tomorrow",
    "body": "Don't forget our meeting at 10am"
})

# List inbox messages
result = connector.list_resources("messages", filters={"folder": "Inbox"})
print(f"Found {len(result.data)} messages")

# Get specific message
result = connector.get_resource("messages", "msg_12345")
```

### Using the Registry

```python
from src.connectors.registry import register_connector, load_connector

# Register connector
register_connector(
    connector_id="outlook",
    module="src.connectors.mock_outlook",
    class_name="MockOutlookConnector",
    enabled=True,
    scopes=["read", "write"]
)

# Load connector dynamically
connector = load_connector("outlook", tenant_id="tenant1", user_id="user1")
if connector:
    connector.connect()
    # Use connector...
```

## Documentation References

- **`docs/CONNECTOR_SDK.md`** - Complete SDK reference with examples
- `docs/SECURITY.md` - Credential management and tenant isolation
- `docs/OPERATIONS.md` - Connector troubleshooting and monitoring
- `docs/COLLABORATION.md` - Team-based connector access control

---

**Last Updated:** 2025-10-04 (Sprint 34B complete)
**Next Sprint:** Sprint 34C - Connector Observability & Testing
