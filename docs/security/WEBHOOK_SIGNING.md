# Webhook Signature Verification

**Purpose:** Verify webhook requests from Relay actions API using HMAC-SHA256 signatures.

## Overview

When `ACTIONS_SIGNING_SECRET` is configured, Relay signs all webhook requests with an HMAC-SHA256 signature in the `X-Signature` header. Recipients should verify this signature to ensure requests originated from Relay and haven't been tampered with.

## Signature Format

```
X-Signature: sha256=<hex_digest>
```

**Example:**
```
X-Signature: sha256=a591a6d40bf420404a011733cfb7b190d62c65bf0bcda32b57b277d9ad9f146e
```

## Verification Steps

1. **Extract signature** from `X-Signature` header
2. **Compute HMAC** using your shared secret and the raw request body
3. **Compare** computed signature with received signature (constant-time comparison)
4. **Reject** request if signatures don't match

---

## Implementation Examples

### Node.js (Express)

```javascript
const crypto = require('crypto');
const express = require('express');

const app = express();
const SIGNING_SECRET = process.env.RELAY_SIGNING_SECRET;

// Middleware to verify webhook signatures
function verifyWebhookSignature(req, res, next) {
  if (!SIGNING_SECRET) {
    return res.status(500).json({ error: 'Signing secret not configured' });
  }

  const signature = req.headers['x-signature'];
  if (!signature || !signature.startsWith('sha256=')) {
    return res.status(401).json({ error: 'Missing or invalid signature' });
  }

  const receivedSig = signature.replace('sha256=', '');

  // Compute expected signature
  const hmac = crypto.createHmac('sha256', SIGNING_SECRET);
  hmac.update(req.rawBody);  // Requires raw body (see below)
  const expectedSig = hmac.digest('hex');

  // Constant-time comparison
  if (!crypto.timingSafeEqual(Buffer.from(receivedSig), Buffer.from(expectedSig))) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  next();
}

// Middleware to capture raw body (required for signature verification)
app.use(express.json({
  verify: (req, res, buf) => {
    req.rawBody = buf.toString('utf8');
  }
}));

// Apply signature verification to webhook endpoints
app.post('/webhooks/relay', verifyWebhookSignature, (req, res) => {
  console.log('Verified webhook from Relay:', req.body);
  res.json({ success: true });
});

app.listen(3000, () => console.log('Webhook receiver listening on port 3000'));
```

---

### Python (Flask)

```python
import hmac
import hashlib
from flask import Flask, request, jsonify
import os

app = Flask(__name__)
SIGNING_SECRET = os.getenv('RELAY_SIGNING_SECRET')

def verify_webhook_signature(raw_body: bytes, signature_header: str) -> bool:
    """Verify HMAC-SHA256 signature for webhook request."""
    if not SIGNING_SECRET:
        raise ValueError('Signing secret not configured')

    if not signature_header or not signature_header.startswith('sha256='):
        return False

    received_sig = signature_header.replace('sha256=', '')

    # Compute expected signature
    expected_sig = hmac.new(
        SIGNING_SECRET.encode('utf-8'),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison
    return hmac.compare_digest(received_sig, expected_sig)

@app.route('/webhooks/relay', methods=['POST'])
def handle_relay_webhook():
    signature = request.headers.get('X-Signature', '')
    raw_body = request.get_data()

    if not verify_webhook_signature(raw_body, signature):
        return jsonify({'error': 'Invalid signature'}), 401

    payload = request.json
    print(f'Verified webhook from Relay: {payload}')

    return jsonify({'success': True}), 200

if __name__ == '__main__':
    app.run(port=3000)
```

---

### Python (FastAPI)

```python
import hmac
import hashlib
from fastapi import FastAPI, Request, HTTPException, Header
from typing import Optional
import os

app = FastAPI()
SIGNING_SECRET = os.getenv('RELAY_SIGNING_SECRET')

async def verify_webhook_signature(request: Request, x_signature: Optional[str] = Header(None)):
    """FastAPI dependency to verify webhook signatures."""
    if not SIGNING_SECRET:
        raise HTTPException(status_code=500, detail='Signing secret not configured')

    if not x_signature or not x_signature.startswith('sha256='):
        raise HTTPException(status_code=401, detail='Missing or invalid signature')

    received_sig = x_signature.replace('sha256=', '')

    # Read raw body
    raw_body = await request.body()

    # Compute expected signature
    expected_sig = hmac.new(
        SIGNING_SECRET.encode('utf-8'),
        raw_body,
        hashlib.sha256
    ).hexdigest()

    # Constant-time comparison
    if not hmac.compare_digest(received_sig, expected_sig):
        raise HTTPException(status_code=401, detail='Invalid signature')

@app.post('/webhooks/relay', dependencies=[Depends(verify_webhook_signature)])
async def handle_relay_webhook(payload: dict):
    print(f'Verified webhook from Relay: {payload}')
    return {'success': True}
```

---

## Security Best Practices

### ✅ DO

- **Use constant-time comparison** (`crypto.timingSafeEqual` in Node, `hmac.compare_digest` in Python) to prevent timing attacks
- **Verify before processing** - reject invalid signatures immediately
- **Use raw request body** - compute HMAC over the exact bytes received, not the parsed JSON
- **Store secret securely** - use environment variables or secret managers (never hardcode)
- **Log verification failures** - monitor for potential attacks
- **Rotate secrets periodically** - update `ACTIONS_SIGNING_SECRET` quarterly

### ❌ DON'T

- **Don't use string equality** (`==`) for signature comparison (vulnerable to timing attacks)
- **Don't compute HMAC over parsed JSON** - use raw body bytes
- **Don't expose signature in error messages** - return generic 401 errors
- **Don't skip verification** in production, even temporarily
- **Don't reuse secrets** across environments (dev/staging/prod should have unique secrets)

---

## Testing Your Implementation

### Test 1: Valid Signature (200 OK)

```bash
# Generate test signature
SECRET="your-shared-secret"
BODY='{"test":"data"}'
SIGNATURE=$(echo -n "$BODY" | openssl dgst -sha256 -hmac "$SECRET" -hex | awk '{print $2}')

# Send request
curl -X POST https://your-webhook-receiver.com/webhooks/relay \
  -H "Content-Type: application/json" \
  -H "X-Signature: sha256=$SIGNATURE" \
  -d "$BODY"

# Expected: HTTP 200 OK
```

### Test 2: Invalid Signature (401 Unauthorized)

```bash
curl -X POST https://your-webhook-receiver.com/webhooks/relay \
  -H "Content-Type: application/json" \
  -H "X-Signature: sha256=invalid" \
  -d '{"test":"data"}'

# Expected: HTTP 401 Unauthorized
```

### Test 3: Missing Signature (401 Unauthorized)

```bash
curl -X POST https://your-webhook-receiver.com/webhooks/relay \
  -H "Content-Type: application/json" \
  -d '{"test":"data"}'

# Expected: HTTP 401 Unauthorized
```

---

## Troubleshooting

### Signature Mismatch

**Symptom:** Signatures don't match even though secret is correct

**Common causes:**
1. **Body transformation** - middleware modified request body before verification (e.g., JSON parsing)
2. **Character encoding** - body bytes don't match (use UTF-8)
3. **Whitespace differences** - extra newlines or spaces added/removed
4. **Wrong secret** - dev secret used in production, or vice versa

**Fix:** Verify you're computing HMAC over the exact raw bytes received, before any parsing or transformation.

### Missing X-Signature Header

**Symptom:** `X-Signature` header not present in requests

**Cause:** `ACTIONS_SIGNING_SECRET` not configured on Relay server

**Fix:** Set `ACTIONS_SIGNING_SECRET` environment variable on Railway and redeploy.

### Timing Attack Concerns

**Symptom:** Security audit flags string comparison

**Fix:** Use constant-time comparison functions:
- Node.js: `crypto.timingSafeEqual()`
- Python: `hmac.compare_digest()`
- Go: `subtle.ConstantTimeCompare()`

---

## Relay Configuration

**On Relay Server (Railway):**

```bash
# Set signing secret (generate with: openssl rand -hex 32)
railway variables --set ACTIONS_SIGNING_SECRET=<64-char-hex-string>

# Verify it's set
railway variables | grep ACTIONS_SIGNING_SECRET
```

**On Webhook Receiver:**

```bash
# Use the same secret
export RELAY_SIGNING_SECRET=<64-char-hex-string>
```

⚠️ **Security:** Never commit secrets to git. Use environment variables or secret managers.

---

## Monitoring & Alerts

### Recommended Metrics

- `webhook_signature_failures_total` - Count of failed verifications
- `webhook_signature_missing_total` - Count of requests without signature
- `webhook_signature_success_total` - Count of successful verifications

### Alert Rules

```yaml
- alert: WebhookSignatureFailures
  expr: rate(webhook_signature_failures_total[5m]) > 0.1
  for: 10m
  annotations:
    summary: "High rate of webhook signature failures"
    description: "More than 10% of webhook requests have invalid signatures. Possible attack or misconfiguration."

- alert: WebhookSignatureMissing
  expr: rate(webhook_signature_missing_total[5m]) > 0
  for: 5m
  annotations:
    summary: "Webhook requests missing signatures"
    description: "Relay may be misconfigured (ACTIONS_SIGNING_SECRET not set)."
```

---

## References

- [RFC 2104: HMAC: Keyed-Hashing for Message Authentication](https://tools.ietf.org/html/rfc2104)
- [OWASP: HMAC Best Practices](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [GitHub Webhook Security](https://docs.github.com/en/developers/webhooks-and-events/webhooks/securing-your-webhooks)

---

🤖 Generated with [Claude Code](https://claude.com/claude-code)

*Document version: Sprint 51 Phase 2 (2025-10-07)*
