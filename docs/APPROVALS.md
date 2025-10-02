# Interactive Approvals Guide

Configure Slack and Teams to approve/reject DJP workflow outputs with interactive buttons.

## Overview

Interactive approvals let reviewers approve or reject pending artifacts directly in Slack or Teams without opening the web UI. Button clicks trigger webhooks that update artifact status automatically.

## Architecture

```
Template Run (require_approval=true)
  ↓
Artifact created with status="pending_approval"
  ↓
Notification sent to Slack/Teams with Approve/Reject buttons
  ↓
User clicks button
  ↓
Webhook receives action
  ↓
Artifact status updated (published or advisory_only)
  ↓
Confirmation message posted
```

## Setup

### 1. Start Webhooks Server

```bash
# Terminal: Start webhooks server
uvicorn src.webhooks:app --host 0.0.0.0 --port 8100 --reload
```

### 2. Expose Webhook Endpoint (Dev)

For local development, expose webhook endpoint to internet using a tunnel:

**Option A: Cloudflare Tunnel**

```bash
# Install cloudflared
# Windows: winget install cloudflare.cloudflared
# Mac: brew install cloudflare/cloudflare/cloudflared

# Start tunnel
cloudflared tunnel --url http://localhost:8100
```

Copy the generated URL (e.g., `https://abc123.trycloudflare.com`).

**Option B: ngrok**

```bash
# Install ngrok: https://ngrok.com/download
ngrok http 8100
```

Copy the forwarding URL (e.g., `https://xyz789.ngrok.io`).

**Option C: GitHub Codespaces**

Codespaces automatically expose ports. Use the forwarded URL.

### 3. Configure Environment Variables

```bash
# Webhook base URL (your tunnel URL)
export WEBHOOK_BASE_URL=https://abc123.trycloudflare.com

# Slack signing secret (for signature verification)
export SLACK_SIGNING_SECRET=your_slack_signing_secret

# Teams webhook token (for auth)
export TEAMS_WEBHOOK_TOKEN=your_teams_webhook_token

# Slack/Teams webhook URLs (for posting)
export SLACK_WEBHOOK_URL=https://hooks.slack.com/services/...
export TEAMS_WEBHOOK_URL=https://outlook.office.com/webhook/...
```

## Slack Configuration

### 1. Create Slack App

1. Go to https://api.slack.com/apps
2. Click "Create New App" → "From scratch"
3. Name: "DJP Workflow"
4. Pick workspace

### 2. Enable Incoming Webhooks

1. Features → Incoming Webhooks → Toggle On
2. Click "Add New Webhook to Workspace"
3. Select channel (e.g., `#approvals`)
4. Copy webhook URL → set as `SLACK_WEBHOOK_URL`

### 3. Enable Interactive Components

1. Features → Interactive Components → Toggle On
2. Request URL: `https://your-tunnel.com/webhooks/slack`
3. Save Changes

### 4. Get Signing Secret

1. Settings → Basic Information → App Credentials
2. Copy "Signing Secret" → set as `SLACK_SIGNING_SECRET`

### 5. Install App to Workspace

1. Settings → Install App → Install to Workspace
2. Authorize permissions

## Teams Configuration

### 1. Create Incoming Webhook

1. Teams channel → ⋯ → Connectors
2. Configure "Incoming Webhook"
3. Name: "DJP Approvals"
4. Copy webhook URL → set as `TEAMS_WEBHOOK_URL`

### 2. Configure Webhook Token (Optional)

For production, generate a secret token:

```bash
openssl rand -hex 32
```

Set as `TEAMS_WEBHOOK_TOKEN` and include in webhook headers.

## Testing

### Test Slack Approval

```python
from src.connectors.slack import post_approval_notification

post_approval_notification(
    template_name="Test Template",
    preview_text="This is a test approval notification",
    artifact_id="test-123",
    channel="#approvals",
    interactive=True
)
```

1. Message appears in Slack with Approve/Reject buttons
2. Click "✅ Approve"
3. Webhook receives action at `/webhooks/slack`
4. Artifact status updated to "published"
5. Confirmation message posted

### Test Teams Approval

```python
from src.connectors.teams import post_approval_notification

post_approval_notification(
    template_name="Test Template",
    preview_text="This is a test approval notification",
    artifact_id="test-456",
    interactive=True
)
```

1. Adaptive Card appears in Teams with buttons
2. Click "✅ Approve"
3. Webhook receives action at `/webhooks/teams`
4. Artifact status updated
5. Confirmation message posted

## Security

### Slack Signature Verification

Webhook handler verifies Slack signatures to prevent replay attacks:

```python
# In src/webhooks.py
def verify_slack_signature(request: Request, body: bytes) -> bool:
    """Verify Slack request signature using signing secret."""
    # Compares HMAC-SHA256 of request body with X-Slack-Signature header
    # Rejects requests older than 5 minutes
```

**Dev Mode**: If `SLACK_SIGNING_SECRET` not set, verification skipped (warning logged).

### Teams Token Authentication

Webhook handler checks bearer token:

```python
def verify_teams_token(request: Request) -> bool:
    """Verify Teams webhook token."""
    # Compares Authorization header with TEAMS_WEBHOOK_TOKEN
```

**Dev Mode**: If `TEAMS_WEBHOOK_TOKEN` not set, verification skipped.

## Production Deployment

### 1. Deploy Webhook Handler

Deploy webhooks server to cloud alongside main app:

**AWS ECS:**

```bash
# Add to task definition
{
  "name": "webhooks",
  "image": "123456789.dkr.ecr.us-east-1.amazonaws.com/djp-workflow:latest",
  "command": ["uvicorn", "src.webhooks:app", "--host", "0.0.0.0", "--port", "8100"],
  "portMappings": [{"containerPort": 8100}],
  "environment": [
    {"name": "SLACK_SIGNING_SECRET", "value": "..."},
    {"name": "TEAMS_WEBHOOK_TOKEN", "value": "..."}
  ]
}
```

**GCP Cloud Run:**

```bash
gcloud run deploy djp-webhooks \
  --image gcr.io/my-project/djp-workflow:latest \
  --command uvicorn \
  --args src.webhooks:app,--host,0.0.0.0,--port,8100 \
  --set-env-vars SLACK_SIGNING_SECRET=...,TEAMS_WEBHOOK_TOKEN=... \
  --allow-unauthenticated
```

### 2. Configure Public URL

Set `WEBHOOK_BASE_URL` to production URL:

```bash
export WEBHOOK_BASE_URL=https://webhooks.djp.example.com
```

Update Slack/Teams app configuration with production webhook URL.

### 3. Enable HTTPS

- Use ALB/Cloud Load Balancer for TLS termination
- Or use Cloud Run's automatic HTTPS

### 4. Set Secrets

Store secrets in secrets manager:

- AWS Secrets Manager
- GCP Secret Manager

Inject at runtime (not in container image).

## Troubleshooting

### Buttons don't appear

- Check `interactive=True` in `post_approval_notification()`
- Verify Slack/Teams webhook URL is correct
- Check webhook posting logs for errors

### Button click does nothing

- Verify webhook server running and accessible
- Check tunnel/proxy forwarding correctly
- Review webhook handler logs for errors
- Verify Slack interactive components URL set

### "Invalid signature" error (Slack)

- Check `SLACK_SIGNING_SECRET` matches app's signing secret
- Ensure request timestamp within 5 minutes
- Verify tunnel doesn't modify request body

### Artifact not found

- Check artifact_id in notification matches actual artifact
- Verify artifact exists in `runs/` directory
- Check file permissions

## Environment Variables Reference

| Variable | Required | Description |
|----------|----------|-------------|
| `WEBHOOK_BASE_URL` | Yes | Base URL for webhook callbacks (e.g., `https://webhooks.example.com`) |
| `SLACK_SIGNING_SECRET` | Recommended | Slack app signing secret for signature verification |
| `SLACK_WEBHOOK_URL` | Yes | Slack incoming webhook URL for posting messages |
| `TEAMS_WEBHOOK_TOKEN` | Recommended | Custom token for Teams webhook authentication |
| `TEAMS_WEBHOOK_URL` | Yes | Teams incoming webhook URL for posting messages |

## Next Steps

- Monitor webhook logs for errors
- Set up alerting for failed approvals
- Add approval metrics dashboard
- Support multi-step approval workflows
- Add approval delegation
