# Microsoft Teams Connector

**Version:** 1.0 (Sprint 35B)
**Status:** Production Ready

---

## Overview

The Microsoft Teams connector integrates with Microsoft Graph API to manage teams, channels, and messages. It supports both **DRY_RUN** (offline mock) and **LIVE** (real API) modes.

**Features:**
- List/get teams, channels, messages
- Create/update/delete messages
- OAuth2 token management
- Circuit breaker, retry logic, metrics
- Rate limit handling (Graph API: 10,000 req/10min per app)

---

## Setup

### Azure App Registration & Permissions

1. **Azure Portal** → **App Registrations** → **New registration**
2. Note **Application (client) ID** and **Directory (tenant) ID**
3. Create client secret: **Certificates & secrets** → **New client secret**
4. Add **Microsoft Graph API** permissions: `Team.ReadBasic.All`, `Channel.ReadBasic.All`, `ChannelMessage.Read.All`, `ChannelMessage.Send`
5. Grant admin consent

### OAuth2 Token Setup

See `docs/CONNECTOR_OBSERVABILITY.md` for OAuth2 flow. Save token via:

```python
from src.connectors.oauth2 import save_token
save_token('teams', access_token='...', refresh_token='...', expires_at='2025-10-05T12:00:00')
```

---

## Environment Variables

### Required (LIVE mode)

| Variable | Description | Example |
|----------|-------------|---------|
| `MS_CLIENT_ID` | Azure application (client) ID | `12345678-1234-...` |
| `MS_TENANT_ID` | Azure directory (tenant) ID | `87654321-4321-...` |
| `MS_CLIENT_SECRET` | Client secret from Azure | `abc123...` |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `DRY_RUN` | `true` | Use mock responses (no API calls) |
| `LIVE` | `false` | Enable real API calls (forces DRY_RUN=false) |
| `TEAMS_DEFAULT_TEAM_ID` | `""` | Default team ID for operations |
| `TEAMS_DEFAULT_CHANNEL_ID` | `""` | Default channel ID for operations |
| `GRAPH_BASE_URL` | `https://graph.microsoft.com/v1.0` | Graph API base URL |
| `RETRY_MAX_ATTEMPTS` | `3` | Max retry attempts for failed calls |

---

## Modes

### DRY_RUN Mode (Default)

Offline mode using mock responses. Use for CI/CD testing, development without credentials, offline environments:

```bash
export DRY_RUN=true LIVE=false
```

### LIVE Mode

Real Graph API calls (requires OAuth2 token and Azure credentials):

```bash
export LIVE=true MS_CLIENT_ID=<ID> MS_TENANT_ID=<ID> MS_CLIENT_SECRET=<SECRET>
```

---

## CLI Usage Examples

```python
from src.connectors.teams import TeamsConnector
conn = TeamsConnector('teams', 'tenant1', 'user1')

# List teams
teams = conn.list_resources('teams')

# List channels
channels = conn.list_resources('channels', team_id='<TEAM_ID>')

# Send message
result = conn.create_resource(
    'messages',
    {'body': {'content': 'Hello!', 'contentType': 'text'}},
    team_id='<TEAM_ID>',
    channel_id='<CHANNEL_ID>'
)
```

---

## Rate Limits

**Microsoft Graph API Throttling:**
- **Per App**: 10,000 requests per 10 minutes
- **Per User**: 1,200 requests per 60 seconds (varies by workload)

**Handling:**
- Connector automatically retries on HTTP 429 (rate limit)
- Exponential backoff with jitter (see `docs/CONNECTOR_OBSERVABILITY.md`)
- Circuit breaker opens after repeated failures

**Best Practices:**
- Use batch operations when available
- Cache team/channel metadata
- Monitor metrics for rate limit errors

---

## RBAC

Write operations require **Admin** role:

```bash
export USER_ROLE=Admin  # Required for create/update/delete
```

Read operations require **Operator** role or higher:

```bash
export USER_ROLE=Operator  # Sufficient for list/get
```

---

## Observability

### Metrics

All operations are recorded to `logs/connectors/metrics.jsonl`:

```bash
# View health
python scripts/connectors_health.py drill teams
```

### Health Checks

```python
from src.connectors.metrics import health_status

health = health_status("teams", window_minutes=60)
print(health["status"])  # healthy, degraded, down, unknown
```

---

## Troubleshooting

| Error | Solution |
|-------|----------|
| "No OAuth2 token found" | Run OAuth2 flow and save token |
| "Token expired" | Re-run OAuth2 flow (refresh not yet implemented) |
| "Rate limited: 429" | Wait 10 minutes or reduce request rate |
| Circuit breaker stuck open | Wait for cooldown (60s), verify Graph API status |

---

## See Also

- `docs/CONNECTOR_OBSERVABILITY.md` - Metrics, health, OAuth2, retry, circuit breaker
- `docs/CONNECTOR_SDK.md` - Base connector interface
- `docs/CONNECTORS.md` - Connector framework overview
