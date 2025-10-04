# Slack Connector Documentation

## Overview

The Slack connector provides integration with Slack workspaces via the Slack Web API. It supports:

- Channels (list, get)
- Messages (list, get, create, update, delete)
- Users (list, get)
- DRY_RUN (mock) and LIVE (real API) modes
- OAuth2 authentication with bot tokens
- Retry logic with exponential backoff
- Circuit breaker pattern for fault tolerance
- Metrics recording for observability

## Setup

### 1. Create a Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App"
3. Choose "From scratch"
4. Name your app and select your workspace
5. Click "Create App"

### 2. Configure Bot Token Scopes

Navigate to "OAuth & Permissions" and add the following Bot Token Scopes:

**Required scopes:**
- `channels:read` - View basic channel information
- `channels:history` - View messages in public channels
- `groups:read` - View basic private channel information
- `groups:history` - View messages in private channels
- `users:read` - View users in workspace
- `chat:write` - Send messages

**Optional scopes (for additional features):**
- `channels:manage` - Manage public channels
- `groups:write` - Manage private channels
- `users:read.email` - View email addresses
- `chat:write.customize` - Send messages with custom username/icon

### 3. Install App to Workspace

1. In "OAuth & Permissions", click "Install to Workspace"
2. Review permissions and click "Allow"
3. Copy the "Bot User OAuth Token" (starts with `xoxb-`)

### 4. Set Environment Variables

```bash
# Required for LIVE mode
export SLACK_BOT_TOKEN="xoxb-your-bot-token"

# Optional configuration
export SLACK_BASE_URL="https://slack.com/api"  # Default
export SLACK_DEFAULT_CHANNEL_ID="C1234567890"  # Default channel for operations
export DRY_RUN="false"  # Use "true" for offline testing
export LIVE="true"      # Use "false" for DRY_RUN mode

# RBAC
export USER_ROLE="Admin"  # Admin, Deployer, Operator, Viewer

# Resilience settings
export RETRY_MAX_ATTEMPTS="3"  # Max retry attempts
```

## Modes

### DRY_RUN Mode (Default)

In DRY_RUN mode, the connector operates offline using mock responses:

```bash
export DRY_RUN="true"
export LIVE="false"
```

- No real API calls are made
- Mock data is returned from `logs/connectors/slack_mock.jsonl`
- Useful for testing, development, and CI/CD
- Metrics are still recorded

### LIVE Mode

In LIVE mode, the connector makes real API calls to Slack:

```bash
export DRY_RUN="false"
export LIVE="true"
export SLACK_BOT_TOKEN="xoxb-your-token"
```

- Requires valid bot token
- All operations interact with real Slack workspace
- Rate limits apply (see below)
- Requires appropriate scopes

## Usage Examples

### Python API

```python
from src.connectors.slack import SlackConnector

# Initialize connector
slack = SlackConnector(
    connector_id="my-slack",
    tenant_id="tenant-1",
    user_id="user-1"
)

# Connect (validates token in LIVE mode)
if not slack.connect():
    raise Exception("Failed to connect to Slack")

# List channels
channels = slack.list_resources("channels")
for channel in channels:
    print(f"Channel: {channel['name']} ({channel['id']})")

# List messages in a channel
messages = slack.list_resources("messages", channel_id="C1234567890")
for msg in messages:
    print(f"Message: {msg['text']} at {msg['ts']}")

# Get specific channel
channel = slack.get_resource("channels", "C1234567890")
print(f"Channel members: {channel.get('num_members', 0)}")

# Create message (requires Admin role)
result = slack.create_resource(
    "messages",
    {"text": "Hello from the connector!"},
    channel_id="C1234567890"
)

# Update message
slack.update_resource(
    "messages",
    "1609459200.000100",  # Message timestamp
    {"text": "Updated message text"},
    channel_id="C1234567890"
)

# Delete message
slack.delete_resource("messages", "1609459200.000100", channel_id="C1234567890")

# List users
users = slack.list_resources("users")
for user in users:
    print(f"User: {user['real_name']} ({user['name']})")

# Disconnect (no-op for REST API)
slack.disconnect()
```

### CLI Examples

```bash
# Test connection
python -m src.connectors.slack connect

# List channels
python -m src.connectors.slack list channels

# List messages in channel
python -m src.connectors.slack list messages --channel-id C1234567890

# Post message
python -m src.connectors.slack create message \
  --channel-id C1234567890 \
  --text "Hello from CLI"

# List users
python -m src.connectors.slack list users
```

## Resource Types

### Channels

**Operations:** list, get

```python
# List all channels
channels = slack.list_resources("channels")

# Get specific channel
channel = slack.get_resource("channels", "C1234567890")
```

**Response fields:**
- `id` - Channel ID
- `name` - Channel name
- `is_channel` - True for public channels
- `is_member` - True if bot is a member
- `num_members` - Number of members

### Messages

**Operations:** list, get, create, update, delete

```python
# List messages in channel
messages = slack.list_resources("messages", channel_id="C1234567890")

# Get specific message
message = slack.get_resource("messages", "1609459200.000100", channel_id="C1234567890")

# Create message (Admin only)
result = slack.create_resource(
    "messages",
    {"text": "Hello, world!"},
    channel_id="C1234567890"
)

# Update message (Admin only)
result = slack.update_resource(
    "messages",
    "1609459200.000100",
    {"text": "Updated text"},
    channel_id="C1234567890"
)

# Delete message (Admin only)
slack.delete_resource("messages", "1609459200.000100", channel_id="C1234567890")
```

**Response fields:**
- `ts` - Message timestamp (ID)
- `text` - Message text
- `user` - User ID who sent message
- `type` - Message type

### Users

**Operations:** list, get

```python
# List all users
users = slack.list_resources("users")

# Get specific user
user = slack.get_resource("users", "U1234567890")
```

**Response fields:**
- `id` - User ID
- `name` - Username
- `real_name` - Full name
- `is_bot` - True for bot users
- `profile` - User profile data

## Rate Limits

Slack uses Tier-based rate limiting:

- **Tier 2 methods** (most read operations): 20+ requests/minute
- **Tier 3 methods** (posting messages): 50+ requests/minute
- **Tier 4 methods** (special cases): 100+ requests/minute

The connector automatically handles rate limiting:
- Detects `rate_limited` errors
- Retries with exponential backoff
- Respects `Retry-After` headers

**Rate limit headers:**
- `X-Rate-Limit-Limit` - Requests allowed per period
- `X-Rate-Limit-Remaining` - Remaining requests
- `Retry-After` - Seconds to wait before retry

## RBAC (Role-Based Access Control)

The connector enforces role-based permissions:

| Operation | Required Role |
|-----------|---------------|
| Read (list, get) | Operator or higher |
| Write (create, update, delete) | Admin |

**Role hierarchy:**
1. Admin (highest)
2. Deployer
3. Operator
4. Viewer (lowest)

Set user role via environment variable:

```bash
export USER_ROLE="Operator"
```

## Webhooks & Events

The connector supports Slack Events API webhooks for real-time notifications.

### Setup Events API

1. In your Slack app, go to "Event Subscriptions"
2. Enable Events
3. Set Request URL to your webhook endpoint
4. Subscribe to bot events:
   - `message.channels` - Messages in public channels
   - `message.groups` - Messages in private channels
   - `channel_created` - New channels
   - `user_change` - User profile changes

### Webhook Payload Example

```json
{
  "type": "event_callback",
  "event": {
    "type": "message",
    "channel": "C1234567890",
    "user": "U1234567890",
    "text": "Hello, world!",
    "ts": "1609459200.000100"
  }
}
```

### Webhook Verification

The connector includes documentation for signature verification (not enforced by default):

1. Set `SLACK_SIGNING_SECRET` environment variable
2. Verify `X-Slack-Signature` header
3. Compare HMAC SHA256 of request body
4. Ensure timestamp is within 5 minutes

**Note:** Signature verification is documented but not enforced. Implement in production environments.

## Error Handling

The connector implements comprehensive error handling:

### Retry Logic

Automatically retries on:
- HTTP 429 (rate limited)
- HTTP 5xx (server errors)
- Network timeouts

Does NOT retry on:
- HTTP 4xx (client errors, except 429)
- Slack API errors (e.g., `channel_not_found`)

### Circuit Breaker

Protects against cascading failures:
- **Closed:** Normal operation
- **Open:** Fails fast after N failures
- **Half-Open:** Tests recovery after timeout

Configure via environment:
```bash
export CIRCUIT_FAILURE_THRESHOLD="5"
export CIRCUIT_TIMEOUT_SECONDS="60"
```

### Error Examples

```python
try:
    channel = slack.get_resource("channels", "C_INVALID")
except Exception as e:
    if "channel_not_found" in str(e):
        print("Channel does not exist")
    elif "Circuit breaker open" in str(e):
        print("Service temporarily unavailable")
    else:
        print(f"Error: {e}")
```

## Metrics

All API calls are recorded with metrics:

```json
{
  "connector_id": "slack-1",
  "endpoint": "conversations.list",
  "status": "success",
  "duration_ms": 245.3,
  "timestamp": "2025-10-04T12:34:56Z"
}
```

View metrics:
```bash
tail -f logs/connectors/metrics.jsonl
```

## Troubleshooting

### "No Slack token found"

**Cause:** Missing `SLACK_BOT_TOKEN` environment variable

**Solution:**
```bash
export SLACK_BOT_TOKEN="xoxb-your-token"
```

### "missing_scope" error

**Cause:** Bot token lacks required OAuth scopes

**Solution:**
1. Go to app settings > "OAuth & Permissions"
2. Add required scopes
3. Reinstall app to workspace
4. Use new bot token

### "channel_not_found" error

**Cause:** Bot is not a member of the channel

**Solution:**
- Invite bot to channel: `/invite @YourBot`
- Or use public channels where bot is a member

### Rate limiting (429 errors)

**Cause:** Exceeding API rate limits

**Solution:**
- Connector automatically retries with backoff
- Reduce request frequency
- Use bulk operations when possible

### "Circuit breaker open"

**Cause:** Multiple consecutive failures

**Solution:**
- Wait for circuit breaker timeout (default 60s)
- Check Slack API status: https://status.slack.com
- Verify network connectivity

### DRY_RUN mode not working

**Cause:** `LIVE=true` overrides `DRY_RUN`

**Solution:**
```bash
export LIVE="false"
export DRY_RUN="true"
```

## Mock HTTP Transport for Testing

Sprint 36B introduced deterministic mock HTTP transport for comprehensive resilience testing.

### MockHTTPTransport

The `MockHTTPTransport` class enables scripted HTTP responses without real API calls:

```python
from src.connectors.http_mock import get_mock_transport, reset_mock_transport

# Enable mock transport
os.environ["SLACK_USE_HTTP_MOCK"] = "true"

# Get mock instance
mock = get_mock_transport()

# Script responses for (method, endpoint)
mock.script("GET", "conversations.list", [
    {"status_code": 429, "body": {"ok": False, "error": "rate_limited"}},
    {"status_code": 200, "body": {"ok": True, "channels": [{"id": "C123", "name": "test"}]}}
])

# Make API call (uses mock)
connector = SlackConnector("test", "tenant-1", "user-1")
result = connector.list_resources("channels")

# Verify call count
assert mock.get_call_count("GET", "conversations.list") == 2
```

### Environment Variables

- **SLACK_USE_HTTP_MOCK**: Enable mock transport (`true`/`false`, default: `false`)
- **SLACK_RETRY_STATUS**: HTTP status codes that trigger retry (default: `429,500,502,503,504`)
- **DRY_RUN**: Legacy JSONL-based mocks (`true`/`false`, default: `true`)

**Note:** `SLACK_USE_HTTP_MOCK=true` takes precedence over legacy `DRY_RUN` mode for deterministic testing.

### Mock Features

1. **Scripted Responses**: Define exact sequence of responses per endpoint
2. **Call Tracking**: Track all HTTP calls made during test
3. **Latency Recording**: Optional `latency_ms` field (recorded but not slept)
4. **Deterministic**: No random behavior, fully reproducible tests
5. **CI-Safe**: No real API calls, no secrets required

### Usage in Tests

```python
import pytest
from src.connectors.http_mock import get_mock_transport, reset_mock_transport

@pytest.fixture
def slack_connector():
    os.environ["SLACK_USE_HTTP_MOCK"] = "true"
    reset_mock_transport()

    connector = SlackConnector("test", "tenant-1", "user-1")
    yield connector

    reset_mock_transport()

def test_rate_limit_retry(slack_connector):
    mock = get_mock_transport()

    # Script 429 then success
    mock.script("GET", "conversations.list", [
        {"status_code": 429, "body": {"ok": False, "error": "rate_limited"}},
        {"status_code": 200, "body": {"ok": True, "channels": []}}
    ])

    result = slack_connector.list_resources("channels")

    # Verify retry happened
    assert mock.get_call_count("GET", "conversations.list") == 2
```

## Resilience Patterns

### Retry Configuration

The connector supports configurable retry behavior:

```bash
# Retry settings
export RETRY_MAX_ATTEMPTS="3"           # Max retry attempts (default: 3)
export RETRY_BASE_MS="400"              # Base backoff delay (default: 400ms)
export RETRY_CAP_MS="60000"             # Max backoff cap (default: 60s)
export RETRY_JITTER_PCT="0.2"           # Jitter percentage (default: 0.2)

# Slack-specific retry codes
export SLACK_RETRY_STATUS="429,500,502,503,504"  # HTTP codes to retry
```

### Retryable vs Non-Retryable Errors

**Retryable (automatic retry with backoff):**
- HTTP 429 (rate limited) - uses `Retry-After` header if present
- HTTP 500, 502, 503, 504 (server errors)
- Network timeouts and connection errors
- Slack API `rate_limited` error

**Non-Retryable (fail immediately):**
- HTTP 4xx (except 429) - client errors
- Slack API errors: `channel_not_found`, `not_authed`, `invalid_auth`, etc.
- Circuit breaker open state

### Circuit Breaker States

The circuit breaker protects against cascading failures:

```bash
# Circuit breaker configuration
export CB_FAILURES_TO_OPEN="5"     # Failures before opening (default: 5)
export CB_COOLDOWN_S="60"           # Cooldown before half-open (default: 60s)
export CB_HALF_OPEN_PROB="0.2"     # Probability of allowing in half-open (default: 0.2)
```

**State Transitions:**

1. **Closed (normal)**:
   - All requests allowed
   - Failures increment counter
   - After N failures → Open

2. **Open (failing)**:
   - All requests blocked immediately
   - "Circuit breaker open" exception
   - After cooldown → Half-Open

3. **Half-Open (testing)**:
   - Probabilistic request gating
   - Success → Closed (recovery)
   - Failure → Open (still broken)

**Monitoring Circuit State:**

```python
from src.connectors.circuit import get_circuit_state

state = get_circuit_state("slack-connector-1")
print(f"Circuit state: {state}")  # "closed", "open", or "half_open"
```

### Webhook Signature Verification

Slack webhooks support HMAC SHA256 signature verification per [Slack docs](https://api.slack.com/authentication/verifying-requests-from-slack):

```bash
# Enable signature verification (production)
export SLACK_SIGNING_SECRET="your_slack_signing_secret"
```

**Verification Process:**

1. Extract `X-Slack-Request-Timestamp` and `X-Slack-Signature` headers
2. Verify timestamp is within 5 minutes (replay attack prevention)
3. Compute HMAC SHA256: `v0={timestamp}:{body}`
4. Constant-time comparison of signatures

**Behavior:**

- **Secret present**: Full verification required
- **Secret missing/empty**: Verification disabled (dev mode, logs warning)
- **Invalid signature**: Request rejected (401)
- **Stale timestamp**: Request rejected (401)

**Usage in Code:**

```python
from src.webhooks import verify_slack_signature_headers

headers = {
    "X-Slack-Request-Timestamp": "1609459200",
    "X-Slack-Signature": "v0=a2114d57b48eac39b9ad189dd8316235a7b4a8d21a10bd27519666489c69b503"
}
body = b'{"type":"url_verification","challenge":"3eZbrw1aBm2rZgRNFdxV2595E9CY3gmdALWMmHkvFXO7tYXAYM8P"}'
secret = os.getenv("SLACK_SIGNING_SECRET")

if verify_slack_signature_headers(headers, body, secret):
    print("Valid Slack request")
else:
    print("Invalid signature")
```

## Testing

### Run DRY_RUN Tests

```bash
# All tests (offline, no API calls)
pytest tests/test_slack_connector_dryrun.py -v

# Specific test
pytest tests/test_slack_connector_dryrun.py::test_list_channels -v
```

### Run Resilience Tests

```bash
# Test retry/circuit breaker logic (uses MockHTTPTransport)
pytest tests/test_slack_connector_resilience.py -v

# Specific resilience test
pytest tests/test_slack_connector_resilience.py::test_rate_limit_429_retry -v
```

### Run Webhook Signature Tests

```bash
# Test HMAC SHA256 signature verification
pytest tests/test_slack_webhook_signature.py -v
```

### Run Webhook Tests

```bash
# Test event normalization
pytest tests/test_slack_webhooks.py -v
```

### Run LIVE Tests (requires real token)

```bash
export LIVE="true"
export SLACK_BOT_TOKEN="xoxb-your-token"
pytest tests/test_slack_connector_dryrun.py -v -m live
```

## Architecture

### Class Hierarchy

```
Connector (base)
  └── SlackConnector
       ├── _get_token()      # OAuth2 token management
       ├── _call_api()       # HTTP client with retry/circuit
       ├── _mock_response()  # DRY_RUN mock data
       ├── list_resources()  # List channels/messages/users
       ├── get_resource()    # Get specific resource
       ├── create_resource() # Create message
       ├── update_resource() # Update message
       ├── delete_resource() # Delete message
       └── _check_rbac()     # Role validation
```

### Dependencies

- `base.py` - Connector base class
- `circuit.py` - Circuit breaker implementation
- `http_client.py` - HTTP request wrapper
- `metrics.py` - Metrics recording
- `oauth2.py` - Token management
- `retry.py` - Backoff calculation
- `cp_cal.py` - Endpoint registry and schema normalization
- `webhooks.py` - Event normalization

## Best Practices

1. **Use DRY_RUN for development**
   - Test logic without API calls
   - Fast feedback loop
   - No rate limits

2. **Implement proper RBAC**
   - Restrict write operations to Admin role
   - Use service accounts with minimal scopes

3. **Monitor metrics**
   - Track API call patterns
   - Identify rate limit issues early
   - Alert on circuit breaker opens

4. **Handle errors gracefully**
   - Catch specific exceptions
   - Implement fallback behavior
   - Log errors with context

5. **Optimize API usage**
   - Batch operations when possible
   - Cache channel/user lists
   - Use pagination for large datasets

## Related Documentation

- [Slack API Documentation](https://api.slack.com/docs)
- [OAuth Scopes](https://api.slack.com/scopes)
- [Rate Limiting](https://api.slack.com/docs/rate-limits)
- [Events API](https://api.slack.com/apis/connections/events-api)
- [Block Kit](https://api.slack.com/block-kit)

## Changelog

### v1.0.0 (2025-10-04)

- Initial Slack connector implementation
- Support for channels, messages, users
- DRY_RUN and LIVE modes
- OAuth2 bot token authentication
- Retry logic with exponential backoff
- Circuit breaker pattern
- RBAC enforcement
- Webhook event normalization
- CP-CAL integration for endpoint mapping
- Comprehensive test suite
