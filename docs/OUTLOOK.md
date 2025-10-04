# Outlook Add-in Integration

Minimal viable Outlook taskpane for composing emails from templates and triaging content via DJP.

## Overview

The DJP Outlook add-in provides two key features:

1. **Compose from Template** - Select a template, fill inputs, render, and insert into email body
2. **Send to DJP Triage** - Send email content to DJP workflow for analysis

## Prerequisites

- Outlook Desktop (Windows/Mac) or Outlook Web
- DJP web API running on `http://localhost:8000`
- Node.js (for serving taskpane files)

## Local Development Setup

### 1. Start Web API

```bash
# Terminal 1: Start web API
cd C:\Users\kylem\openai-agents-workflows-2025.09.28-v1
uvicorn src.webapi:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Serve Taskpane Files

The taskpane HTML/JS must be served via HTTPS for Outlook to load them.

**Option A: Using Python HTTP Server with SSL**

```bash
# Generate self-signed certificate (one-time)
openssl req -x509 -newkey rsa:2048 -keyout key.pem -out cert.pem -days 365 -nodes

# Serve taskpane
cd integrations/outlook/src
python -m http.server 8443 --bind 0.0.0.0
```

**Option B: Using http-server (Node.js)**

```bash
npm install -g http-server
cd integrations/outlook/src
http-server -p 8443 --ssl --cert cert.pem --key key.pem
```

Update `manifest.xml` to use `https://localhost:8443/taskpane.html` instead of port 8000.

### 3. Sideload Manifest

**Outlook Desktop (Windows):**

1. File → Info → Manage Add-ins → My Add-ins
2. Click "+ Add a custom add-in" → "Add from file..."
3. Browse to `integrations/outlook/manifest.xml`
4. Click "Install"

**Outlook Web:**

1. Settings (gear icon) → View all Outlook settings
2. Mail → Customize actions → Get Add-ins
3. My add-ins → Add a custom add-in → Add from file
4. Upload `manifest.xml`

### 4. Test Add-in

1. Compose new email
2. Click "DJP Assistant" button in ribbon
3. Taskpane opens on right side
4. Test "Compose from Template" and "Send to DJP Triage"

## Features

### Compose from Template

1. Click "Compose from Template"
2. Select template from dropdown
3. Form appears with template inputs
4. Fill required fields
5. Click "Render & Insert"
6. Rendered HTML inserted into email body

### Send to DJP Triage

1. Open or compose email
2. Click "Send to DJP Triage"
3. Email content sent to `/api/triage` endpoint
4. Artifact ID displayed in status message
5. View full artifact in `runs/api/triage/`

## API Endpoints Used

- `GET /api/templates` - List available templates
- `POST /api/render` - Render template with inputs
- `POST /api/triage` - Triage email content via DJP

## Security Considerations

### Development Mode

- **HTTPS required**: Outlook requires HTTPS for add-ins (use self-signed cert for dev)
- **CORS enabled**: Web API has CORS middleware for `*` origin (restrict in production)
- **No authentication**: Local development mode has no auth (add in production)

### Production Deployment

**1. Host Web API in Cloud**

Deploy to AWS App Runner / GCP Cloud Run (see `docs/DEPLOYMENT.md`):

```bash
# Example: Cloud Run
gcloud run deploy djp-webapi \
  --image gcr.io/my-project/djp-workflow:latest \
  --platform managed \
  --allow-unauthenticated
```

**2. Host Taskpane Files**

Serve `taskpane.html` and `taskpane.js` from cloud:

- AWS S3 + CloudFront
- GCP Cloud Storage + Cloud CDN
- Azure Blob Storage + CDN

Update `manifest.xml` with production URLs:

```xml
<SourceLocation DefaultValue="https://djp.example.com/static/taskpane.html"/>
```

**3. Add Authentication**

**Option A: API Key**

```javascript
// In taskpane.js
const API_KEY = 'your-api-key-here';
const response = await fetch(`${API_BASE}/api/templates`, {
    headers: { 'Authorization': `Bearer ${API_KEY}` }
});
```

**Option B: OAuth (Microsoft Graph)**

Use Office.js auth API to get user token:

```javascript
Office.auth.getAccessToken().then(token => {
    fetch(API_BASE, { headers: { 'Authorization': `Bearer ${token}` } });
});
```

Configure Azure AD app registration and add to `manifest.xml`.

**4. Restrict CORS**

Update `src/webapi.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://djp.example.com", "https://outlook.office365.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)
```

## Troubleshooting

### Add-in doesn't load

- Check taskpane files served via HTTPS
- Verify manifest.xml URLs are correct
- Check browser console in taskpane (F12)
- Trust self-signed certificate (visit https://localhost:8443 in browser first)

### "Failed to load templates"

- Ensure web API running on correct port
- Check CORS headers in API response
- Verify network connectivity (firewall/proxy)

### Render fails

- Check all required inputs filled
- Verify template exists in `/api/templates` response
- Check API logs for validation errors

### Triage fails

- Verify email has content (not empty)
- Check API logs for DJP workflow errors
- Ensure OPENAI_API_KEY set (or mock mode enabled)

## Production Checklist

- [ ] Deploy web API to cloud (AWS/GCP)
- [ ] Host taskpane files on CDN
- [ ] Update manifest.xml with production URLs
- [ ] Add authentication (API key or OAuth)
- [ ] Restrict CORS to known origins
- [ ] Enable HTTPS only (no HTTP)
- [ ] Test with real Outlook accounts
- [ ] Submit to AppSource (optional) or distribute internally

## Next Steps

- Add OAuth authentication
- Support email attachments
- Add template favorites
- Rich text preview
- Send rendered emails directly
- Schedule template runs
