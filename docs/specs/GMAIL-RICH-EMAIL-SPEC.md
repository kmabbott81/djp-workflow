# Gmail Rich Email API Specification

**Sprint:** 54 (Phase C)
**Date:** October 8, 2025
**Status:** Specification
**Version:** 1.0

---

## Overview

This document specifies the API extensions to the `gmail.send` action for HTML email body, regular attachments, and inline images (CID references).

---

## Request Schema

### Extended `gmail.send` Parameters

```json
{
  "action_id": "gmail.send",
  "params": {
    "to": "string (email, required)",
    "subject": "string (required)",
    "text": "string (required, plain text fallback)",
    "html": "string (optional, sanitized HTML body)",
    "cc": ["string (email)"] (optional),
    "bcc": ["string (email)"] (optional),
    "attachments": [
      {
        "filename": "string (required)",
        "content_type": "string (MIME type, required)",
        "data": "string (base64-encoded, required)"
      }
    ] (optional),
    "inline": [
      {
        "cid": "string (Content-ID, required)",
        "filename": "string (required)",
        "content_type": "string (MIME type, required)",
        "data": "string (base64-encoded, required)"
      }
    ] (optional),
    "headers": {
      "Reply-To": "string (email)",
      "X-Priority": "string (1-5)"
    } (optional, future)
  },
  "workspace_id": "uuid (required)",
  "user_email": "string (required)"
}
```

---

## Validation Rules

### Field Constraints

| Field | Type | Max Length | Max Count | Notes |
|-------|------|------------|-----------|-------|
| `to` | email | 254 chars | N/A | RFC 5321 |
| `subject` | string | 998 chars | N/A | RFC 2822 |
| `text` | string | 5 MB | N/A | Plain text fallback |
| `html` | string | 5 MB | N/A | Sanitized HTML |
| `cc` | email[] | 254 chars each | 50 | Per recipient |
| `bcc` | email[] | 254 chars each | 50 | Per recipient |
| `attachments` | array | 25 MB each | 10 | Regular files |
| `attachments[].filename` | string | 255 chars | N/A | No path traversal |
| `attachments[].content_type` | MIME | 100 chars | N/A | Allowlist enforced |
| `attachments[].data` | base64 | 25 MB decoded | N/A | Binary data |
| `inline` | array | 5 MB each | 20 | Inline images only |
| `inline[].cid` | string | 100 chars | N/A | Unique per email |
| `inline[].filename` | string | 255 chars | N/A | No path traversal |
| `inline[].content_type` | MIME | 100 chars | N/A | `image/*` only |
| `inline[].data` | base64 | 5 MB decoded | N/A | Binary data |

### Total Payload Limits

- **Total request size:** 50 MB (Gmail API limit)
- **Total attachments + inline:** 50 MB combined
- **Total recipients (to + cc + bcc):** 100 max

---

## MIME Type Allowlist

### Attachments: Allowed Types

```
application/pdf
application/msword
application/vnd.openxmlformats-officedocument.wordprocessingml.document
application/vnd.ms-excel
application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
application/vnd.ms-powerpoint
application/vnd.openxmlformats-officedocument.presentationml.presentation
image/png
image/jpeg
image/gif
image/webp
text/plain
text/csv
application/json
application/xml
```

### Attachments: Blocked Types

```
application/x-msdownload (.exe)
application/x-sh (.sh)
application/x-bat (.bat)
application/x-powershell (.ps1)
application/zip
application/x-rar-compressed
application/x-7z-compressed
application/java-archive (.jar)
application/x-deb
application/x-rpm
```

### Inline Images: Allowed Types

```
image/png
image/jpeg
image/gif
image/webp
image/svg+xml (future, requires extra sanitization)
```

---

## HTML Sanitization Rules

### Allowed Tags

```html
<p>, <div>, <span>, <a>, <img>, <table>, <thead>, <tbody>, <tr>, <td>, <th>,
<h1>, <h2>, <h3>, <h4>, <h5>, <h6>, <ul>, <ol>, <li>, <strong>, <em>, <b>,
<i>, <u>, <br>, <hr>, <blockquote>, <pre>, <code>
```

### Blocked Tags (Stripped)

```html
<script>, <iframe>, <object>, <embed>, <form>, <input>, <button>, <select>,
<textarea>, <style>, <link>, <meta>, <base>, <applet>
```

### Allowed Attributes

```
href (on <a>, with protocol whitelist: http, https, mailto)
src (on <img>, with protocol whitelist: http, https, cid)
alt (on <img>)
title (on any tag)
width, height (on <img>, <table>, <td>)
align (on <table>, <td>)
colspan, rowspan (on <td>)
class, id (on any tag, but values sanitized)
style (inline styles, with strict CSS parser)
```

### Blocked Attributes (Removed)

```
onclick, onload, onerror, onmouseover, onfocus, onblur, etc. (all `on*` event handlers)
href with javascript: protocol
src with data: protocol (except for inline images via CID)
```

### CSS Sanitization

- **Allowed properties:** `color`, `background-color`, `font-size`, `font-family`, `text-align`, `padding`, `margin`, `border`, `width`, `height`
- **Blocked properties:** `position`, `z-index`, `display` (if set to `none`), `visibility`, `opacity` (if < 0.1)
- **Blocked values:** `expression(...)`, `url(javascript:...)`, `import`, `@font-face`

---

## Error Taxonomy (Bounded Reasons)

### Validation Errors (400 Bad Request)

| Reason | When It Occurs | HTTP Status |
|--------|----------------|-------------|
| `validation_error_html_too_large` | HTML body > 5MB | 400 |
| `validation_error_attachment_too_large` | Attachment > 25MB | 400 |
| `validation_error_attachment_count_exceeded` | > 10 attachments | 400 |
| `validation_error_inline_too_large` | Inline image > 5MB | 400 |
| `validation_error_inline_count_exceeded` | > 20 inline images | 400 |
| `validation_error_total_size_exceeded` | Total > 50MB | 400 |
| `validation_error_blocked_mime_type` | Attachment has blocked MIME type | 400 |
| `validation_error_invalid_filename` | Filename contains path traversal | 400 |
| `validation_error_invalid_cid` | CID missing or malformed | 400 |
| `validation_error_cid_not_referenced` | Inline image CID not used in HTML | 400 |
| `validation_error_missing_inline_image` | HTML references CID not provided | 400 |

### Feature Flag Errors (501 Not Implemented)

| Reason | When It Occurs | HTTP Status |
|--------|----------------|-------------|
| `feature_disabled_rich_email` | `PROVIDER_GOOGLE_RICH_EMAIL_ENABLED=false` and HTML or attachments provided | 501 |
| `feature_disabled_attachments` | `ATTACHMENTS_ENABLED=false` and attachments provided | 501 |

### Gmail API Errors (Varies)

| Reason | When It Occurs | HTTP Status |
|--------|----------------|-------------|
| `gmail_payload_too_large` | Gmail API rejects > 50MB | 413 |
| `gmail_rate_limited` | Gmail API returns 429 | 429 |
| `gmail_quota_exceeded` | User exceeded daily send quota (500/day free, 2000/day Workspace) | 429 |

---

## Sample Payloads

### 1. Plain Text Email (Baseline)

```json
{
  "action_id": "gmail.send",
  "params": {
    "to": "recipient@example.com",
    "subject": "Hello from Relay",
    "text": "This is a plain text email."
  },
  "workspace_id": "abc-123-def-456",
  "user_email": "sender@example.com"
}
```

**MIME Output:**
```
To: recipient@example.com
Subject: Hello from Relay
MIME-Version: 1.0
Content-Type: text/plain; charset="utf-8"

This is a plain text email.
```

---

### 2. HTML Email with Text Fallback

```json
{
  "action_id": "gmail.send",
  "params": {
    "to": "recipient@example.com",
    "subject": "HTML Email Example",
    "text": "This is the plain text fallback.",
    "html": "<p>This is an <strong>HTML</strong> email with <a href=\"https://example.com\">a link</a>.</p>"
  },
  "workspace_id": "abc-123-def-456",
  "user_email": "sender@example.com"
}
```

**MIME Output:**
```
To: recipient@example.com
Subject: HTML Email Example
MIME-Version: 1.0
Content-Type: multipart/alternative; boundary="boundary123"

--boundary123
Content-Type: text/plain; charset="utf-8"

This is the plain text fallback.

--boundary123
Content-Type: text/html; charset="utf-8"

<p>This is an <strong>HTML</strong> email with <a href="https://example.com">a link</a>.</p>

--boundary123--
```

---

### 3. HTML Email with Inline Image (CID)

```json
{
  "action_id": "gmail.send",
  "params": {
    "to": "recipient@example.com",
    "subject": "Email with Inline Image",
    "text": "This email contains an inline image.",
    "html": "<p>Here is an inline image:</p><img src=\"cid:image1\" alt=\"Logo\">",
    "inline": [
      {
        "cid": "image1",
        "filename": "logo.png",
        "content_type": "image/png",
        "data": "iVBORw0KGgoAAAANSUhEUgAAAAUA... (base64 data)"
      }
    ]
  },
  "workspace_id": "abc-123-def-456",
  "user_email": "sender@example.com"
}
```

**MIME Output:**
```
To: recipient@example.com
Subject: Email with Inline Image
MIME-Version: 1.0
Content-Type: multipart/related; boundary="boundary456"

--boundary456
Content-Type: multipart/alternative; boundary="boundary789"

--boundary789
Content-Type: text/plain; charset="utf-8"

This email contains an inline image.

--boundary789
Content-Type: text/html; charset="utf-8"

<p>Here is an inline image:</p><img src="cid:image1" alt="Logo">

--boundary789--

--boundary456
Content-Type: image/png
Content-Transfer-Encoding: base64
Content-ID: <image1>
Content-Disposition: inline; filename="logo.png"

iVBORw0KGgoAAAANSUhEUgAAAAUA...
(base64 data)

--boundary456--
```

---

### 4. Email with Regular Attachment

```json
{
  "action_id": "gmail.send",
  "params": {
    "to": "recipient@example.com",
    "subject": "Invoice Attached",
    "text": "Please find the invoice attached.",
    "attachments": [
      {
        "filename": "invoice-2025-10.pdf",
        "content_type": "application/pdf",
        "data": "JVBERi0xLjQKJeLjz9MKNSAwIG9iago8... (base64 data)"
      }
    ]
  },
  "workspace_id": "abc-123-def-456",
  "user_email": "sender@example.com"
}
```

**MIME Output:**
```
To: recipient@example.com
Subject: Invoice Attached
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="boundary123"

--boundary123
Content-Type: text/plain; charset="utf-8"

Please find the invoice attached.

--boundary123
Content-Type: application/pdf
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename="invoice-2025-10.pdf"

JVBERi0xLjQKJeLjz9MKNSAwIG9iago8...
(base64 data)

--boundary123--
```

---

### 5. Full Example: HTML + Inline Image + Attachment

```json
{
  "action_id": "gmail.send",
  "params": {
    "to": "recipient@example.com",
    "subject": "Newsletter - October 2025",
    "text": "Plain text fallback: Check out our newsletter.",
    "html": "<h1>Newsletter</h1><p>Welcome to October!</p><img src=\"cid:header\" alt=\"Header\"><p>See attachment for details.</p>",
    "inline": [
      {
        "cid": "header",
        "filename": "header.jpg",
        "content_type": "image/jpeg",
        "data": "/9j/4AAQSkZJRgABAQEAYABgAAD... (base64 data)"
      }
    ],
    "attachments": [
      {
        "filename": "newsletter-october-2025.pdf",
        "content_type": "application/pdf",
        "data": "JVBERi0xLjQKJeLjz9MKNSAwIG9iago8... (base64 data)"
      }
    ]
  },
  "workspace_id": "abc-123-def-456",
  "user_email": "sender@example.com"
}
```

**MIME Output:**
```
To: recipient@example.com
Subject: Newsletter - October 2025
MIME-Version: 1.0
Content-Type: multipart/mixed; boundary="outer"

--outer
Content-Type: multipart/related; boundary="related"

--related
Content-Type: multipart/alternative; boundary="alternative"

--alternative
Content-Type: text/plain; charset="utf-8"

Plain text fallback: Check out our newsletter.

--alternative
Content-Type: text/html; charset="utf-8"

<h1>Newsletter</h1><p>Welcome to October!</p><img src="cid:header" alt="Header"><p>See attachment for details.</p>

--alternative--

--related
Content-Type: image/jpeg
Content-Transfer-Encoding: base64
Content-ID: <header>
Content-Disposition: inline; filename="header.jpg"

/9j/4AAQSkZJRgABAQEAYABgAAD...
(base64 data)

--related--

--outer
Content-Type: application/pdf
Content-Transfer-Encoding: base64
Content-Disposition: attachment; filename="newsletter-october-2025.pdf"

JVBERi0xLjQKJeLjz9MKNSAwIG9iago8...
(base64 data)

--outer--
```

---

## Privacy & Redaction Policy

### What Gets Logged

- **SHA256 digest** of HTML body (first 64 bytes before hashing)
- **SHA256 digest** of each attachment (first 64 bytes before hashing)
- **Filenames** (sanitized, no full paths)
- **MIME types**
- **File sizes** (bytes)
- **CID references** (but not image data)

### What Does NOT Get Logged

- **Raw HTML body** (security & privacy concern)
- **Raw attachment data** (privacy & storage concern)
- **Inline image data** (privacy concern)
- **Email addresses** (PII) in non-production logs

### Audit Log Format

```json
{
  "action": "gmail.send",
  "workspace_id": "abc-123-def-456",
  "user_email": "sender@example.com",
  "timestamp": "2025-10-08T14:32:15Z",
  "status": "success",
  "message_id": "18f7a1b2c3d4e5f6",
  "params_digest": "e3b0c44298fc1c14...",
  "html_sha256": "5d41402abc4b2a76..." (if HTML provided),
  "attachments": [
    {
      "filename": "invoice-2025-10.pdf",
      "content_type": "application/pdf",
      "size_bytes": 245680,
      "sha256": "a1b2c3d4e5f6g7h8..."
    }
  ],
  "inline": [
    {
      "cid": "header",
      "filename": "header.jpg",
      "content_type": "image/jpeg",
      "size_bytes": 15680,
      "sha256": "9h8g7f6e5d4c3b2a..."
    }
  ],
  "metrics": {
    "mime_build_ms": 45,
    "gmail_api_latency_ms": 320
  }
}
```

---

## HTTP Response Examples

### Success Response

**Status:** 200 OK

```json
{
  "status": "sent",
  "message_id": "18f7a1b2c3d4e5f6",
  "thread_id": "18f7a1b2c3d4e5f6",
  "to": "recipient@example.com",
  "subject": "Newsletter - October 2025",
  "attachments_count": 1,
  "inline_count": 1
}
```

### Validation Error Response

**Status:** 400 Bad Request

```json
{
  "error": "Validation error: Attachment too large",
  "reason": "validation_error_attachment_too_large",
  "details": {
    "filename": "large-video.mp4",
    "size_bytes": 30000000,
    "max_bytes": 25000000
  }
}
```

### Feature Disabled Response

**Status:** 501 Not Implemented

```json
{
  "error": "Rich email features are disabled (PROVIDER_GOOGLE_RICH_EMAIL_ENABLED=false)",
  "reason": "feature_disabled_rich_email",
  "details": {
    "html_provided": true,
    "attachments_provided": true
  }
}
```

### Gmail API Error Response

**Status:** 429 Too Many Requests

```json
{
  "error": "Gmail API rate limit exceeded",
  "reason": "gmail_rate_limited",
  "retry_after": 60,
  "details": {
    "quota_type": "per_user_rate_limit",
    "limit": "500/day"
  }
}
```

---

## Implementation Notes

### Base64URL Encoding

- **Standard Base64:** Uses `+` and `/`, with `=` padding
- **Base64URL:** Uses `-` and `_`, NO padding
- **Gmail API Requirement:** Base64URL without padding
- **Implementation:** `base64.urlsafe_b64encode().rstrip(b'=')`

### CID Reference Format

- **CID in HTML:** `<img src="cid:image1">`
- **CID in MIME:** `Content-ID: <image1>`
- **Note:** CID in MIME header is wrapped in `<>`, but NOT in HTML `src`

### MIME Boundary Generation

- Use secure random string (16 bytes hex)
- Prefix with `===` to avoid collision with content
- Example: `boundary="===abc123def456==="`

### Character Encoding

- **Email headers:** UTF-8 with RFC 2047 encoding (e.g., `=?utf-8?b?...?=`)
- **Email body:** UTF-8 with `Content-Type: text/html; charset="utf-8"`
- **Filenames:** UTF-8, sanitize to ASCII-safe subset

---

**Gmail Rich Email API Specification v1.0 Complete**
