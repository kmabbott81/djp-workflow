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
# Test retry/circuit breaker logic (mocked)
pytest tests/test_slack_connector_resilience.py -v
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
