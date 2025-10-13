# Studio Google Connect UX Specification

**Sprint:** 54 (Phase C)
**Date:** October 8, 2025
**Status:** Specification
**Version:** 1.0

---

## Overview

This document specifies the user experience for connecting Google accounts in Relay Studio, including OAuth consent flow, account status display, error states, and disconnect functionality.

---

## User Flows

### Flow 1: Initial Connection (Disconnected → Connected)

**Preconditions:**
- User is logged into Relay Studio
- User has not connected Google account yet
- `PROVIDER_GOOGLE_ENABLED=true` in backend

**Steps:**

1. **User navigates to Settings → Integrations**
   - Sees "Google" card with status: "Not Connected"
   - CTA button: "Connect Google"

2. **User clicks "Connect Google"**
   - Studio calls `/oauth/google/authorize?workspace_id={uuid}`
   - Backend returns `{authorize_url, state, expires_in: 600}`
   - Studio opens `authorize_url` in new window (popup or tab)

3. **User completes OAuth consent in Google popup**
   - Google shows consent screen: "Relay wants to send email on your behalf"
   - User clicks "Allow"
   - Google redirects to `/oauth/google/callback?code=...&state=...&workspace_id=...`

4. **Backend processes callback**
   - Exchanges code for tokens
   - Stores encrypted tokens in database + Redis
   - Redirects to Studio with success: `{studio_url}/integrations?google=connected`

5. **Studio shows success state**
   - Google card status: "Connected"
   - Displays connected email address (e.g., "user@gmail.com")
   - Shows "Disconnect" button
   - Success toast: "Google account connected successfully"

---

### Flow 2: Token Refresh Warning

**Preconditions:**
- User's OAuth token is expiring within 2 minutes
- User is actively using Studio

**Steps:**

1. **Studio polls `/oauth/google/status` every 60 seconds**
   - Backend returns: `{linked: true, expires_in: 90}` (90 seconds until expiry)

2. **Studio shows non-blocking warning banner**
   - Text: "Your Google connection will expire soon. We'll refresh it automatically."
   - Icon: ⏰ (clock)
   - No user action required

3. **Backend auto-refreshes token**
   - Refresh happens automatically during next `/actions/execute` call
   - User sees no interruption

4. **Studio confirms refresh success**
   - Banner updates: "Google connection refreshed" (green checkmark)
   - Auto-dismisses after 3 seconds

---

### Flow 3: Disconnect (Connected → Disconnected)

**Preconditions:**
- User has Google account connected

**Steps:**

1. **User clicks "Disconnect" button**
   - Studio shows confirmation modal:
     - Title: "Disconnect Google?"
     - Body: "You won't be able to send emails via Gmail until you reconnect. Your existing emails will not be affected."
     - Buttons: "Cancel" (secondary), "Disconnect" (danger, red)

2. **User confirms disconnect**
   - Studio calls `/oauth/google/revoke?workspace_id={uuid}`
   - Backend deletes tokens from database + Redis
   - Returns `{success: true}`

3. **Studio shows disconnected state**
   - Google card status: "Not Connected"
   - CTA button: "Connect Google"
   - Success toast: "Google account disconnected"

---

### Flow 4: Send Email with Google (Happy Path)

**Preconditions:**
- User has Google account connected
- User is composing email in Studio

**Steps:**

1. **User composes email**
   - Fills in: To, Subject, Body (plain text or HTML)
   - Optionally attaches files (drag & drop or file picker)

2. **User clicks "Preview"**
   - Studio calls `/actions/preview` with all params
   - Backend validates, builds MIME preview, returns `preview_id`
   - Studio shows preview modal:
     - To, Subject, Body preview
     - Attachment list with file sizes
     - "Send" button

3. **User clicks "Send"**
   - Studio calls `/actions/execute` with `preview_id`
   - Backend retrieves cached attachments, sends via Gmail API
   - Returns `{status: "sent", message_id: "..."}`

4. **Studio shows success state**
   - Success toast: "Email sent successfully"
   - Shows message_id for debugging (if user is admin)
   - Clears compose form

---

## Screen States

### State 1: Disconnected

**Visual:**
```
┌─────────────────────────────────────────┐
│ Google Integration                      │
├─────────────────────────────────────────┤
│ Status: Not Connected                   │
│                                         │
│ Connect your Google account to send    │
│ emails via Gmail.                       │
│                                         │
│ [Connect Google] (button, primary)     │
└─────────────────────────────────────────┘
```

**Copy:**
- **Title:** "Google Integration"
- **Status:** "Not Connected" (gray badge)
- **Description:** "Connect your Google account to send emails via Gmail."
- **Button:** "Connect Google" (primary, blue)

---

### State 2: Connecting (OAuth in Progress)

**Visual:**
```
┌─────────────────────────────────────────┐
│ Google Integration                      │
├─────────────────────────────────────────┤
│ Status: Connecting...                   │
│                                         │
│ [Spinner] Please complete authorization│
│ in the popup window.                    │
│                                         │
│ [Cancel] (button, secondary)           │
└─────────────────────────────────────────┘
```

**Copy:**
- **Title:** "Google Integration"
- **Status:** "Connecting..." (yellow badge, spinner)
- **Description:** "Please complete authorization in the popup window."
- **Button:** "Cancel" (secondary, closes popup)

---

### State 3: Connected

**Visual:**
```
┌─────────────────────────────────────────┐
│ Google Integration                      │
├─────────────────────────────────────────┤
│ Status: Connected ✓                     │
│                                         │
│ Connected as: user@gmail.com            │
│ Scopes: Send emails                     │
│ Last refreshed: 2 minutes ago           │
│                                         │
│ [Disconnect] (button, danger)          │
│ [View Details] (link, muted)           │
└─────────────────────────────────────────┘
```

**Copy:**
- **Title:** "Google Integration"
- **Status:** "Connected" (green badge, checkmark)
- **Connected as:** "user@gmail.com" (from OAuth tokens)
- **Scopes:** "Send emails" (simplified, maps to `gmail.send`)
- **Last refreshed:** "2 minutes ago" (relative time)
- **Button:** "Disconnect" (danger, red)
- **Link:** "View Details" (opens modal with full OAuth status)

---

### State 4: Token Expiring Soon

**Visual:**
```
┌─────────────────────────────────────────┐
│ Google Integration                      │
├─────────────────────────────────────────┤
│ Status: Connected ✓                     │
│                                         │
│ ⚠️ Token expiring in 90 seconds.       │
│    Refreshing automatically...          │
│                                         │
│ Connected as: user@gmail.com            │
│                                         │
│ [Disconnect] (button, danger)          │
└─────────────────────────────────────────┘
```

**Copy:**
- **Warning:** "⚠️ Token expiring in 90 seconds. Refreshing automatically..."
- **Status:** Still shows "Connected"
- **No user action required**

---

### State 5: Error - Missing OAuth Credentials

**Visual:**
```
┌─────────────────────────────────────────┐
│ Google Integration                      │
├─────────────────────────────────────────┤
│ Status: Configuration Error             │
│                                         │
│ ❌ Google integration is not configured │
│    on this server. Contact your admin. │
│                                         │
│ [Contact Support] (button, secondary)  │
└─────────────────────────────────────────┘
```

**Copy:**
- **Title:** "Google Integration"
- **Status:** "Configuration Error" (red badge)
- **Error:** "❌ Google integration is not configured on this server. Contact your admin."
- **Button:** "Contact Support" (opens support email or chat)

---

### State 6: Error - Token Expired

**Visual:**
```
┌─────────────────────────────────────────┐
│ Google Integration                      │
├─────────────────────────────────────────┤
│ Status: Connection Expired              │
│                                         │
│ ⚠️ Your Google connection has expired.  │
│    Please reconnect to continue sending │
│    emails.                              │
│                                         │
│ [Reconnect Google] (button, primary)   │
└─────────────────────────────────────────┘
```

**Copy:**
- **Title:** "Google Integration"
- **Status:** "Connection Expired" (orange badge)
- **Error:** "⚠️ Your Google connection has expired. Please reconnect to continue sending emails."
- **Button:** "Reconnect Google" (primary, restarts OAuth flow)

---

### State 7: Error - Rate Limited

**Visual:**
```
┌─────────────────────────────────────────┐
│ Google Integration                      │
├─────────────────────────────────────────┤
│ Status: Rate Limited                    │
│                                         │
│ ⚠️ Gmail send quota exceeded.           │
│    You've sent 500 emails today.        │
│    Quota resets in 6 hours.             │
│                                         │
│ [View Quota] (link, muted)             │
└─────────────────────────────────────────┘
```

**Copy:**
- **Title:** "Google Integration"
- **Status:** "Rate Limited" (orange badge)
- **Error:** "⚠️ Gmail send quota exceeded. You've sent 500 emails today. Quota resets in 6 hours."
- **Link:** "View Quota" (opens Gmail quota help doc)

---

## Modal: OAuth Details

**Triggered by:** "View Details" link in Connected state

**Visual:**
```
┌───────────────────────────────────────────────┐
│ Google OAuth Status                           │
├───────────────────────────────────────────────┤
│                                               │
│ Account: user@gmail.com                       │
│ Provider: Google                              │
│ Workspace ID: abc-123-def-456                 │
│                                               │
│ Scopes Granted:                               │
│   • https://www.googleapis.com/auth/gmail.send│
│                                               │
│ Token Status:                                 │
│   • Access Token: Valid (expires in 45 min)   │
│   • Refresh Token: Available                  │
│                                               │
│ Last Activity:                                │
│   • Last email sent: 2 minutes ago            │
│   • Last token refresh: 15 minutes ago        │
│                                               │
│ [Close] (button, secondary)                   │
└───────────────────────────────────────────────┘
```

**Data Source:**
- Calls `/oauth/google/status?workspace_id={uuid}`
- Backend returns:
  ```json
  {
    "linked": true,
    "email": "user@gmail.com",
    "scopes": "https://www.googleapis.com/auth/gmail.send",
    "expires_in": 2700,
    "last_used": "2025-10-08T14:30:00Z",
    "last_refreshed": "2025-10-08T14:15:00Z"
  }
  ```

---

## Modal: Disconnect Confirmation

**Triggered by:** "Disconnect" button in Connected state

**Visual:**
```
┌───────────────────────────────────────────────┐
│ Disconnect Google?                            │
├───────────────────────────────────────────────┤
│                                               │
│ You won't be able to send emails via Gmail   │
│ until you reconnect. Your existing emails     │
│ will not be affected.                         │
│                                               │
│ Connected as: user@gmail.com                  │
│                                               │
│ [Cancel] (button, secondary)                  │
│ [Disconnect] (button, danger, red)           │
└───────────────────────────────────────────────┘
```

**Copy:**
- **Title:** "Disconnect Google?"
- **Body:** "You won't be able to send emails via Gmail until you reconnect. Your existing emails will not be affected."
- **Account:** "Connected as: user@gmail.com"
- **Buttons:** "Cancel" (secondary), "Disconnect" (danger, red)

---

## Toast Messages

### Success Toasts

| Trigger | Message | Duration | Icon |
|---------|---------|----------|------|
| OAuth connection successful | "Google account connected successfully" | 3s | ✅ |
| OAuth disconnection successful | "Google account disconnected" | 3s | ✅ |
| Email sent successfully | "Email sent successfully" | 3s | ✅ |
| Token refreshed | "Google connection refreshed" | 3s | ✅ |

### Error Toasts

| Trigger | Message | Duration | Icon |
|---------|---------|----------|------|
| OAuth connection failed | "Failed to connect Google account. Please try again." | 5s | ❌ |
| Email send failed (OAuth) | "Email failed to send: Google account not connected." | 5s | ❌ |
| Email send failed (rate limit) | "Gmail rate limit exceeded. Try again in 60 seconds." | 10s | ⚠️ |
| File too large | "File too large (max 25MB). Please compress or split." | 5s | ⚠️ |
| Too many attachments | "Too many attachments (max 10). Please remove some." | 5s | ⚠️ |

---

## Accessibility Requirements

### WCAG 2.1 AA Compliance

**Keyboard Navigation:**
- All buttons and links must be keyboard-accessible (Tab, Enter, Space)
- Modal dialogs trap focus (Esc to close)
- Toast messages announced by screen readers (aria-live="polite")

**Screen Reader Support:**
- Status badges have aria-label (e.g., `aria-label="Connected to Google"`)
- Spinner has aria-label="Connecting to Google, please wait"
- Error messages have role="alert"

**Color Contrast:**
- All text meets 4.5:1 contrast ratio
- Status badges use color + icon (not color alone)

**Focus Indicators:**
- All interactive elements have visible focus indicator (2px blue outline)

---

## CORS & Headers

### CORS Configuration

**Backend must allow:**
```
Access-Control-Allow-Origin: https://relay-studio.vercel.app
Access-Control-Allow-Methods: GET, POST, OPTIONS
Access-Control-Allow-Headers: Content-Type, Authorization, Idempotency-Key, X-Request-ID
Access-Control-Allow-Credentials: true
```

### Required Request Headers

| Header | Purpose | Example |
|--------|---------|---------|
| `Authorization` | Bearer token (Studio auth) | `Bearer eyJhbGciOi...` |
| `X-Request-ID` | Tracing/debugging | `req-abc-123-def-456` |
| `Idempotency-Key` | Prevent duplicate sends | `uuid-v4` |

### Response Headers to Check

| Header | Purpose | Example |
|--------|---------|---------|
| `X-Request-ID` | Correlate with backend logs | `req-abc-123-def-456` |
| `Retry-After` | Rate limit retry hint | `60` (seconds) |
| `X-RateLimit-Limit` | Rate limit ceiling | `100` |
| `X-RateLimit-Remaining` | Remaining quota | `45` |

---

## Deep Links for Support

### Link 1: OAuth Status API

**URL:** `{backend_url}/oauth/google/status?workspace_id={uuid}`

**Purpose:** Debug OAuth connection issues

**Show in UI:** "View Details" link in Connected state

### Link 2: Audit Logs

**URL:** `{backend_url}/audit/actions?workspace_id={uuid}&action=gmail.send`

**Purpose:** View email send history

**Show in UI:** Future feature (not in Sprint 54)

### Link 3: Help Docs

**URL:** `https://docs.relay.com/integrations/google`

**Purpose:** User-facing help docs for Google integration

**Show in UI:** "Learn More" link in Disconnected state

---

## Error Message Copy Deck

### Client-Side Errors (Studio)

| Error Code | User-Facing Message |
|------------|---------------------|
| `file_too_large` | "File too large (max 25MB). Please compress or split the file." |
| `too_many_attachments` | "Too many attachments (max 10). Please remove some files." |
| `invalid_email` | "Invalid email address. Please check and try again." |
| `oauth_popup_blocked` | "Popup blocked. Please allow popups and try again." |
| `oauth_timeout` | "OAuth connection timed out. Please try again." |

### Server-Side Errors (Backend)

| Error Reason | User-Facing Message |
|--------------|---------------------|
| `provider_disabled` | "Google integration is disabled. Contact your admin." |
| `oauth_token_missing` | "Google account not connected. Please connect your account." |
| `oauth_token_expired` | "Google connection expired. Please reconnect." |
| `gmail_4xx` | "Gmail rejected the email. Please check recipient address." |
| `gmail_5xx` | "Gmail is temporarily unavailable. Please try again later." |
| `gmail_rate_limited` | "Gmail rate limit exceeded. Try again in 60 seconds." |
| `validation_error_html_too_large` | "Email body too large (max 5MB). Please shorten the content." |
| `validation_error_attachment_too_large` | "Attachment '{filename}' too large (max 25MB)." |

---

## Implementation Notes

### OAuth Popup Handling

**Recommended Approach: Popup Window**
```javascript
const popup = window.open(authorizeUrl, 'oauth', 'width=600,height=700');

// Poll for popup close
const pollTimer = setInterval(() => {
  if (popup.closed) {
    clearInterval(pollTimer);
    // Check if OAuth succeeded (poll /oauth/google/status)
  }
}, 500);
```

**Alternative: Redirect Flow**
- Save current state to localStorage
- Redirect to `authorizeUrl`
- Backend redirects back to Studio with `?google=connected`
- Studio restores state from localStorage

**Recommendation:** Use popup for better UX (user doesn't lose context)

### Token Refresh Polling

**Recommended Polling Interval:** 60 seconds

```javascript
setInterval(async () => {
  const status = await fetch(`/oauth/google/status?workspace_id=${workspaceId}`);
  const data = await status.json();

  if (data.expires_in < 120) {
    showWarning("Token expiring soon...");
  }
}, 60000);
```

**Note:** Backend auto-refreshes tokens during `/actions/execute`, so polling is just for UI awareness.

---

## Figma Design Links

**(To be added by design team)**

- **Disconnected State:** [Figma link placeholder]
- **Connected State:** [Figma link placeholder]
- **OAuth Flow:** [Figma link placeholder]
- **Error States:** [Figma link placeholder]

---

**Studio Google Connect UX Specification v1.0 Complete**
