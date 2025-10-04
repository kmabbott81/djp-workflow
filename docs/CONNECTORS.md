# Connector Framework (Sprint 34B+)

**Status:** 🚧 In Development (Sprint 34B planned)

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

### Sprint 34B: Connector SDK v1
- [ ] `BaseConnector` abstract class with lifecycle hooks
- [ ] Authentication framework (OAuth2, API key, JWT)
- [ ] Retry/backoff logic with circuit breaker
- [ ] Connector registry and discovery
- [ ] Initial adapters: Salesforce, Slack, Email (SMTP/IMAP), Webhooks
- [ ] Template integration (connector bindings in YAML)
- [ ] Comprehensive error handling and logging

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

(Placeholder - Sprint 34B will implement)

```python
from src.connectors import get_connector

# Get Salesforce connector for tenant
sf = get_connector("salesforce", tenant_id="acme-corp")

# Query records
contacts = sf.query("SELECT Id, Name, Email FROM Contact LIMIT 10")

# Create record
new_lead = sf.create("Lead", {"FirstName": "Alice", "LastName": "Smith", "Company": "Example Inc"})
```

## Documentation References

- `docs/SECURITY.md` - Credential management and tenant isolation
- `docs/OPERATIONS.md` - Connector troubleshooting and monitoring
- `docs/COLLABORATION.md` - Team-based connector access control

---

**Last Updated:** 2025-10-03 (Sprint 34A complete)
**Next Review:** Sprint 34B kickoff
