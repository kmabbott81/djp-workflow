# Gmail Connector Documentation

**Sprint:** 37
**Status:** Production Ready
**Updated:** 2025-10-04

## Overview

The Gmail connector provides secure integration with Gmail via the Gmail REST API v1. It supports DRY_RUN (mock) and LIVE (production) modes, with comprehensive retry logic, circuit breaker protection, and metrics recording.

## Features

- **OAuth2 Authentication**: Secure token-based authentication with unified token store
- **Multi-Tenant Support**: Isolated operations per tenant via `gmail:{tenant_id}` token keys
- **Resource Types**: Messages, threads, labels
- **Operations**: List, get, create (send), update (modify labels), delete
- **Resilience**: Automatic retry on 429/5xx errors with exponential backoff
- **Circuit Breaker**: Automatic failover protection
- **Metrics**: Per-operation metrics recording for monitoring
- **RBAC**: Role-based access control (reads ≥ Operator, writes ≥ Admin)
- **CP-CAL Integration**: Unified schema normalization across platforms
- **Webhook Support**: Gmail Pub/Sub push notifications

## Prerequisites

### 1. Google Cloud Console Setup

1. Create a project in [Google Cloud Console](https://console.cloud.google.com)
2. Enable Gmail API:
   - Navigate to "APIs & Services" → "Library"
   - Search for "Gmail API"
   - Click "Enable"

### 2. OAuth2 Credentials

1. Go to "APIs & Services" → "Credentials"
2. Click "Create Credentials" → "OAuth client ID"
3. Application type: "Web application" (for server-side) or "Desktop app" (for testing)
4. Add authorized redirect URIs if using web app
5. Save the Client ID and Client Secret

### 3. OAuth2 Scopes

Required scopes for full functionality:

```
https://www.googleapis.com/auth/gmail.readonly      # Read messages, threads, labels
https://www.googleapis.com/auth/gmail.modify        # Modify labels, send messages
https://www.googleapis.com/auth/gmail.labels        # Manage labels
```

For read-only operations:

```
https://www.googleapis.com/auth/gmail.readonly
```

### 4. Generate Refresh Token

Use the OAuth2 flow to obtain a refresh token:

```bash
# Install Google OAuth2 library
pip install google-auth-oauthlib google-auth-httplib2

# Run OAuth2 flow (example)
python scripts/oauth2_gmail_setup.py
```

Or manually via OAuth2 playground:
1. Go to [OAuth2 Playground](https://developers.google.com/oauthplayground/)
2. Configure with your Client ID/Secret
3. Authorize Gmail API scopes
4. Exchange authorization code for refresh token

## Configuration

### Environment Variables

```bash
# Mode
DRY_RUN=false              # true for mock mode, false for live API
LIVE=false                 # true to force live mode

# Gmail API
GMAIL_API_BASE=https://gmail.googleapis.com/gmail/v1
GMAIL_USE_HTTP_MOCK=false  # true to use MockHTTPTransport (testing)

# OAuth2 Credentials
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
GOOGLE_REFRESH_TOKEN=your-refresh-token

# Retry Configuration
GMAIL_RETRY_STATUS=429,500,502,503,504
RETRY_MAX_ATTEMPTS=3

# RBAC
USER_ROLE=Admin            # Admin, Operator, Viewer
```

### Token Storage

Tokens are stored in the unified OAuth2 token store with key format:

```
gmail:{tenant_id}
```

Example:
- Tenant `acme-corp`: `gmail:acme-corp`
- Tenant `beta-test`: `gmail:beta-test`

## Usage

### Python API

#### Initialize Connector

```python
from src.connectors.gmail import GmailConnector

connector = GmailConnector(
    connector_id="gmail-prod",
    tenant_id="acme-corp",
    user_id="user@example.com"
)

# Connect
if connector.connect():
    print("Connected to Gmail")
```

#### List Messages

```python
# List recent messages
messages = connector.list_resources("messages", maxResults=10)

# List with query filter
messages = connector.list_resources("messages", q="from:boss@company.com subject:urgent")

# List by label
messages = connector.list_resources("messages", labelIds="INBOX")
```

#### Get Message

```python
# Get message with full details
message = connector.get_resource("messages", "18c8f123456789ab", format="full")

# Get message with metadata only
message = connector.get_resource("messages", "18c8f123456789ab", format="metadata")
```

#### Send Message

```python
import base64

# Create RFC 2822 message
raw_message = """From: sender@example.com
To: recipient@example.com
Subject: Test Message

Hello from Gmail API!
"""

# Encode as base64url
encoded = base64.urlsafe_b64encode(raw_message.encode()).decode()

# Send
result = connector.create_resource("messages", {"raw": encoded})
print(f"Message sent: {result['id']}")
```

#### Modify Message Labels

```python
# Add and remove labels
result = connector.update_resource(
    "messages",
    "18c8f123456789ab",
    {
        "addLabelIds": ["STARRED", "IMPORTANT"],
        "removeLabelIds": ["INBOX"]
    }
)
```

#### List Threads

```python
# List threads
threads = connector.list_resources("threads", maxResults=20)

# Get thread with all messages
thread = connector.get_resource("threads", "18c8f123456789ab")
```

#### Manage Labels

```python
# List all labels
labels = connector.list_resources("labels")

# Create label
new_label = connector.create_resource("labels", {
    "name": "Important Project",
    "labelListVisibility": "labelShow",
    "messageListVisibility": "show"
})

# Update label
connector.update_resource("labels", "Label_1", {"name": "Updated Name"})

# Delete label
connector.delete_resource("labels", "Label_1")
```

### CLI

#### Register Connector

```bash
python scripts/connectors.py register \
  --id gmail-prod \
  --module src.connectors.gmail \
  --class GmailConnector \
  --auth-type oauth \
  --scopes read,write \
  --user admin \
  --tenant acme-corp
```

#### Test Operations

```bash
# List messages
python scripts/connectors.py test gmail-prod \
  --action list \
  --resource-type messages \
  --user admin \
  --tenant acme-corp \
  --json

# Get specific message
python scripts/connectors.py test gmail-prod \
  --action get \
  --resource-type messages \
  --resource-id 18c8f123456789ab \
  --user admin \
  --tenant acme-corp

# Send message (requires JSON payload)
python scripts/connectors.py test gmail-prod \
  --action create \
  --resource-type messages \
  --payload '{"raw":"RnJvbTo..."}' \
  --user admin \
  --tenant acme-corp
```

## Resource Schemas

### Message (List Response)

```json
{
  "id": "18c8f123456789ab",
  "threadId": "18c8f123456789ab"
}
```

### Message (Get Full)

```json
{
  "id": "18c8f123456789ab",
  "threadId": "18c8f123456789ab",
  "labelIds": ["INBOX", "IMPORTANT"],
  "snippet": "Preview of message content...",
  "payload": {
    "headers": [
      {"name": "From", "value": "sender@example.com"},
      {"name": "To", "value": "recipient@example.com"},
      {"name": "Subject", "value": "Important Message"}
    ],
    "body": {
      "data": "SGVsbG8gd29ybGQ="  // base64-encoded content
    }
  },
  "internalDate": "1609459200000",
  "historyId": "123456"
}
```

### Thread

```json
{
  "id": "18c8f123456789ab",
  "snippet": "Conversation preview...",
  "historyId": "123456",
  "messages": [
    {
      "id": "18c8f123456789ab",
      "labelIds": ["INBOX"],
      "snippet": "Message 1..."
    }
  ]
}
```

### Label

```json
{
  "id": "Label_1",
  "name": "Important Project",
  "type": "user",
  "messageListVisibility": "show",
  "labelListVisibility": "labelShow",
  "messagesTotal": 42,
  "messagesUnread": 7,
  "threadsTotal": 15,
  "threadsUnread": 3
}
```

## Webhook Integration

### Setup Push Notifications

1. **Create Pub/Sub Topic**:
```bash
gcloud pubsub topics create gmail-notifications
```

2. **Grant Gmail Permission**:
```bash
gcloud pubsub topics add-iam-policy-binding gmail-notifications \
  --member=serviceAccount:gmail-api-push@system.gserviceaccount.com \
  --role=roles/pubsub.publisher
```

3. **Create Subscription**:
```bash
gcloud pubsub subscriptions create gmail-push-sub \
  --topic=gmail-notifications \
  --push-endpoint=https://your-app.com/api/webhooks/gmail
```

4. **Watch Mailbox** (via Gmail API):
```python
# Call this to start receiving notifications
POST /gmail/v1/users/me/watch
{
  "topicName": "projects/your-project/topics/gmail-notifications",
  "labelIds": ["INBOX"],
  "labelFilterAction": "include"
}
```

### Handle Push Notifications

```python
from src.connectors.webhooks import ingest_event

@app.route('/api/webhooks/gmail', methods=['POST'])
def gmail_webhook():
    payload = request.get_json()

    # Normalize event
    normalized = ingest_event("gmail", payload)

    # Process event
    if normalized["event_type"] == "message_received":
        history_id = normalized["data"]["historyId"]
        # Fetch changes since history_id

    return {"status": "ok"}
```

### Webhook Payload Example

```json
{
  "message": {
    "data": "eyJlbWFpbEFkZHJlc3MiOiJ1c2VyQGV4YW1wbGUuY29tIiwiaGlzdG9yeUlkIjoiMTIzNDU2In0=",
    "messageId": "2070443601311540",
    "publishTime": "2021-02-26T19:13:55.749Z"
  },
  "subscription": "projects/myproject/subscriptions/gmail-push"
}
```

Decoded `data` field:
```json
{
  "emailAddress": "user@example.com",
  "historyId": "123456"
}
```

## Rate Limits

Gmail API has generous quotas but still enforces limits:

### Quota Limits (per project, per day)

- **Messages.send**: 100 queries per second (QPS)
- **Messages.list**: 250 QPS
- **Messages.get**: 250 QPS
- **Users.watch**: 1,000 per day (lasts 7 days)

### Handling Rate Limits

The connector automatically:
1. Detects 429 responses
2. Retries with exponential backoff
3. Honors `Retry-After` header
4. Opens circuit breaker after repeated failures

### Best Practices

- Batch operations when possible
- Use query filters to reduce result sets
- Cache label IDs (rarely change)
- Use `format=metadata` or `format=minimal` for list operations
- Implement incremental sync with `historyId`

## Error Handling

### Common Errors

#### Authentication Errors

```
Error: No Gmail token found
Solution: Set GOOGLE_REFRESH_TOKEN or run OAuth2 setup
```

#### Insufficient Permissions

```
Gmail API error: Insufficient Permission
Solution: Verify OAuth2 scopes include required permissions
```

#### Invalid Message Format

```
Gmail API error: Invalid RFC 2822 message
Solution: Ensure message is properly formatted and base64url-encoded
```

#### Rate Limit Exceeded

```
Rate limited: Quota exceeded
Action: Automatic retry with backoff (3 attempts)
```

### Non-Retryable Errors

These errors do NOT trigger retry:
- 400 Bad Request
- 401 Unauthorized
- 403 Forbidden (non-rate-limit)
- 404 Not Found

### Retryable Errors

These errors trigger automatic retry:
- 429 Too Many Requests (rate limit)
- 500 Internal Server Error
- 502 Bad Gateway
- 503 Service Unavailable
- 504 Gateway Timeout

## Testing

### DRY_RUN Mode

```bash
export DRY_RUN=true
export LIVE=false

# Run tests
pytest tests/test_gmail_connector_dryrun.py -v
```

Mock data is stored in: `logs/connectors/gmail_mock.jsonl`

### Resilience Testing

```bash
# Test with MockHTTPTransport
export GMAIL_USE_HTTP_MOCK=true

pytest tests/test_gmail_connector_resilience.py -v
```

### Live Testing

```bash
export LIVE=true
export GOOGLE_CLIENT_ID=your-client-id
export GOOGLE_CLIENT_SECRET=your-client-secret
export GOOGLE_REFRESH_TOKEN=your-refresh-token

pytest tests/test_gmail_connector_dryrun.py -v -m live
```

## Monitoring

### Metrics

All operations record metrics via `record_call()`:

- `connector_id`: Gmail connector instance
- `endpoint`: API endpoint called
- `status`: success, error, rate_limited, etc.
- `duration_ms`: Operation duration
- `error`: Error message (if failed)

### Circuit Breaker

Monitor circuit state:

```python
from src.connectors.circuit import CircuitBreaker

circuit = CircuitBreaker("gmail-prod")
print(f"State: {circuit.state}")
print(f"Failures: {circuit.failure_count}")
print(f"Allows: {circuit.allow()}")
```

States:
- `closed`: Normal operation
- `open`: Failing, requests blocked
- `half_open`: Testing recovery

### Health Check

```python
# Test connection
if connector.connect():
    print("✓ Gmail API reachable")
    print(f"✓ Circuit breaker: {connector.circuit.state}")
else:
    print("✗ Gmail API unreachable")
```

## Security

### Token Security

- Tokens stored in encrypted OAuth2 token store
- Multi-tenant isolation via `gmail:{tenant_id}` keys
- Automatic token refresh (when implemented)
- Never log tokens or credentials

### RBAC Enforcement

| Operation | Minimum Role |
|-----------|--------------|
| list_resources | Operator |
| get_resource | Operator |
| create_resource | Admin |
| update_resource | Admin |
| delete_resource | Admin |

### Data Privacy

- Messages are not cached by default
- Mock mode uses synthetic data only
- Webhook payloads contain minimal PII (historyId only)
- Use `format=metadata` to avoid fetching message bodies

## Troubleshooting

### Connection Fails

1. Verify credentials:
   ```bash
   echo $GOOGLE_CLIENT_ID
   echo $GOOGLE_REFRESH_TOKEN
   ```

2. Test OAuth2 token:
   ```bash
   curl -X POST https://oauth2.googleapis.com/token \
     -d client_id=$GOOGLE_CLIENT_ID \
     -d client_secret=$GOOGLE_CLIENT_SECRET \
     -d refresh_token=$GOOGLE_REFRESH_TOKEN \
     -d grant_type=refresh_token
   ```

3. Check Gmail API enabled in Google Cloud Console

### Rate Limit Issues

1. Check quota usage in Google Cloud Console
2. Reduce request rate
3. Implement backoff in application logic
4. Consider upgrading quota limits

### Circuit Breaker Open

1. Check recent failures:
   ```python
   print(f"Failures: {connector.circuit.failure_count}")
   ```

2. Wait for cooldown period (default 60s)

3. Manually reset:
   ```python
   connector.circuit.state = "closed"
   connector.circuit.failure_count = 0
   ```

### Webhook Not Receiving Events

1. Verify watch is active:
   ```bash
   GET /gmail/v1/users/me/watch
   ```

2. Check Pub/Sub subscription exists

3. Verify webhook endpoint is publicly accessible

4. Check webhook logs for errors

5. Re-register watch (expires after 7 days)

## Migration Guide

### From Direct Gmail API

Replace direct API calls with connector:

**Before:**
```python
from googleapiclient.discovery import build

service = build('gmail', 'v1', credentials=creds)
results = service.users().messages().list(userId='me').execute()
messages = results.get('messages', [])
```

**After:**
```python
from src.connectors.gmail import GmailConnector

connector = GmailConnector("gmail-prod", "tenant-1", "user-1")
messages = connector.list_resources("messages")
```

Benefits:
- Automatic retry/backoff
- Circuit breaker protection
- Metrics recording
- RBAC enforcement
- Multi-tenant support

## References

- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Gmail API Reference](https://developers.google.com/gmail/api/reference/rest)
- [OAuth2 Scopes](https://developers.google.com/gmail/api/auth/scopes)
- [Push Notifications](https://developers.google.com/gmail/api/guides/push)
- [Rate Limits](https://developers.google.com/gmail/api/reference/quota)

## Support

For issues or questions:
1. Check this documentation
2. Review [OPERATIONS.md](./OPERATIONS.md) for runbooks
3. Check [SECURITY.md](./SECURITY.md) for security guidelines
4. Review Sprint 37 completion log

## Changelog

- **2025-10-04**: Initial release (Sprint 37)
  - OAuth2 authentication
  - Messages, threads, labels support
  - Retry/circuit breaker/metrics
  - Webhook integration
  - CP-CAL schema normalization
  - Full test coverage
