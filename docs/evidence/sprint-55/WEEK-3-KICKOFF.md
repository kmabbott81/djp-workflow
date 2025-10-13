# Sprint 55 Week 3 - Microsoft Large Attachment Upload Sessions

**Date:** 2025-10-12
**Status:** IN PROGRESS
**Branch:** `feat/rollout-infrastructure`
**Goal:** Support attachments >3 MiB via Graph resumable upload (draft → upload → send pattern)

---

## Executive Summary

Week 3 implements Microsoft Graph API **resumable upload sessions** to handle large attachments (>3 MiB), achieving true parity with Gmail's attachment handling capabilities. This work is gated behind feature flags to ensure safe, incremental rollout.

**Key Features:**
- Draft creation → upload session → chunked upload → send pattern
- Resumable uploads with 429/5xx retry logic + `Retry-After` support
- Chunk size validation (320 KiB multiples, default 4 MiB)
- Full telemetry: upload session metrics, byte counters, chunk timing
- Feature-gated: `MS_UPLOAD_SESSIONS_ENABLED` (default `false`)
- Configurable threshold: `MS_UPLOAD_SESSION_THRESHOLD_BYTES` (default 3 MiB)

---

## Implementation Plan

### A. New Module: `src/actions/adapters/microsoft_upload.py`

Core upload session logic with five key functions:

1. **`create_draft(message_json) -> (message_id, internet_message_id?)`**
   - POST `/me/messages` with message JSON (no large attachments)
   - Returns draft message ID for upload session attachment

2. **`create_upload_session(message_id, attachment_meta) -> upload_url`**
   - POST `/me/messages/{id}/attachments/createUploadSession`
   - Returns resumable upload URL for chunked upload

3. **`put_chunks(upload_url, file_bytes, chunk_size=4*1024*1024)`**
   - Chunk size must be multiple of 320 KiB per Graph spec
   - PUT chunks with `Content-Range` headers
   - Retry logic: 429 with `Retry-After`, 5xx with backoff, max 3 retries/chunk
   - Optional `Content-Range` validation and finalization check

4. **`finalize_upload(upload_url) -> attachment_id`**
   - Verify upload completion
   - Return attachment ID from final response

5. **`send_draft(message_id)`**
   - POST `/me/messages/{id}/send`
   - Triggers delivery of draft with uploaded attachments

### B. Adapter Integration: `src/actions/adapters/microsoft.py`

**Logic Flow:**
1. Check if any attachment > `MS_UPLOAD_SESSION_THRESHOLD_BYTES`
2. If large attachment **and** `MS_UPLOAD_SESSIONS_ENABLED != true`:
   - Return structured error: `provider_payload_too_large`
3. If enabled → switch to **draft flow**:
   - Build message JSON without large attachments
   - Create draft via `microsoft_upload.create_draft()`
   - For each large attachment:
     - Create upload session
     - Upload chunks with retry logic
     - Attach to draft
   - Send draft via `microsoft_upload.send_draft()`
4. Preserve existing flow for small attachments (direct `sendMail`)

**Inline Images:** Preserve existing inline image handling (small attachments use direct `sendMail`).

### C. Telemetry: `src/telemetry/prom.py` + Recording Rules

**New Metrics:**
```python
outlook_upload_session_total = Counter(
    'outlook_upload_session_total',
    'Total Microsoft Graph upload sessions',
    ['result']  # started, completed, failed
)

outlook_upload_bytes_total = Counter(
    'outlook_upload_bytes_total',
    'Total bytes uploaded via Microsoft Graph upload sessions',
    ['result']  # completed, failed
)

outlook_upload_chunk_seconds = Histogram(
    'outlook_upload_chunk_seconds',
    'Microsoft Graph upload chunk duration in seconds',
    buckets=[0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0]
)
```

**Recording Rules:** `config/prometheus/prometheus-recording-microsoft.yml`
```yaml
- record: job:outlook_upload_session_success_rate:5m
  expr: |
    rate(outlook_upload_session_total{result="completed"}[5m])
    /
    rate(outlook_upload_session_total[5m])

- record: job:outlook_upload_throughput_mbps:5m
  expr: |
    rate(outlook_upload_bytes_total{result="completed"}[5m]) / 1024 / 1024
```

**Structured Errors:** Increment `structured_error_total{provider="microsoft", code=...}` for:
- `provider_upload_session_create_failed`
- `provider_upload_chunk_failed`
- `provider_upload_finalize_failed`
- `throttled_429` (with `retry_after_seconds` detail)

### D. Error Mapping: `src/actions/adapters/microsoft_errors.py`

**New Error Codes:**
```python
# Upload session specific errors
"provider_upload_session_create_failed": "Failed to create upload session",
"provider_upload_chunk_failed": "Failed to upload chunk",
"provider_upload_finalize_failed": "Failed to finalize upload",
"provider_upload_session_timeout": "Upload session expired",
"provider_upload_session_invalid_chunk_size": "Chunk size not multiple of 320 KiB",
```

**429 Handling:** Map `throttled_429` with `retry_after_seconds` extracted from `Retry-After` header.

### E. Tests

#### Unit Tests: `tests/actions/test_microsoft_upload.py`

**Scenarios:**
1. **Happy path:** 12 MiB file → 3 chunks (4 MiB each) → completed
2. **429 retry:** Mid-stream 429 with `Retry-After: 2` → wait + jitter → resumed
3. **5xx retry:** 503 once → exponential backoff → success on retry
4. **Invalid chunk size:** Non-320 KiB multiple → error surfaced
5. **Content-Range validation:** Wrong range → error detected
6. **Max retries exceeded:** 3 failures → abort with error

**Threshold Logic:**
- Test flag gating: `MS_UPLOAD_SESSIONS_ENABLED=false` → error on large attachment
- Test threshold: 2 MiB file with 3 MiB threshold → direct send (no upload session)

#### Integration Test: `tests/actions/test_microsoft_upload_integration.py`

**Gate:** Only run if `TEST_MICROSOFT_UPLOAD_INTEGRATION=true`

**Scenario:**
1. Create ~6 MiB test file
2. Send via Microsoft adapter with upload session enabled
3. Assert:
   - `outlook_upload_session_total{result="completed"}` incremented
   - `outlook_upload_bytes_total` ~= 6 MiB
   - Message delivered (verify via Graph API read)
   - Attachment accessible in sent message

### F. Documentation

#### `docs/specs/MS-UPLOAD-SESSIONS.md`

**Contents:**
- Flowchart: draft → createUploadSession → PUT chunks → send
- Graph API endpoints used:
  - `POST /me/messages` (create draft)
  - `POST /me/messages/{id}/attachments/createUploadSession`
  - `PUT {uploadUrl}` (chunked upload)
  - `POST /me/messages/{id}/send`
- Chunk size requirements (320 KiB multiples)
- Retry strategy (429 with Retry-After, 5xx with backoff)
- Error handling and edge cases
- Feature flag configuration

#### `docs/evidence/sprint-55/WEEK-3-UPLOAD-SESSIONS-COMPLETE.md`

**Contents:**
- All deliverables (A-F) with code examples
- Unit test results (all scenarios passing)
- Integration test results (gated, screenshot of Prometheus metrics)
- Example upload session flow (request/response logs)
- Grafana dashboard screenshots showing upload metrics
- Edge case handling verification
- Performance benchmarks (throughput, chunk timing)

---

## Success Criteria

- [ ] All unit tests pass (6+ scenarios covered)
- [ ] Gated integration test passes locally
- [ ] Adapter respects `MS_UPLOAD_SESSIONS_ENABLED` flag and threshold
- [ ] Telemetry visible in Prometheus/Grafana
- [ ] Error codes properly mapped and surfaced
- [ ] Documentation complete (spec + evidence)
- [ ] No regression in existing small attachment flow

---

## Timeline

**Week 3 Duration:** 2025-10-12 → 2025-10-18 (7 days)

**Day 1-2 (Sat-Sun):** Core implementation
- `microsoft_upload.py` module
- Adapter integration
- Basic unit tests

**Day 3-4 (Mon-Tue):** Telemetry + error handling
- Prometheus metrics
- Recording rules
- Error mapping
- Retry logic refinement

**Day 5-6 (Wed-Thu):** Testing + docs
- Full unit test suite
- Gated integration test
- Spec document
- Evidence document

**Day 7 (Fri):** Verification + PR
- End-to-end verification
- Grafana screenshots
- PR creation
- Sprint tracking update

---

## Graph API Endpoints Reference

### 1. Create Draft Message
```http
POST https://graph.microsoft.com/v1.0/me/messages
Content-Type: application/json

{
  "subject": "Test with large attachment",
  "body": { "contentType": "HTML", "content": "<p>Hello</p>" },
  "toRecipients": [{ "emailAddress": { "address": "user@example.com" }}]
}
```

**Response:**
```json
{
  "id": "AAMkAGI...",
  "internetMessageId": "<abc123@example.com>"
}
```

### 2. Create Upload Session
```http
POST https://graph.microsoft.com/v1.0/me/messages/{id}/attachments/createUploadSession
Content-Type: application/json

{
  "AttachmentItem": {
    "attachmentType": "file",
    "name": "large-file.pdf",
    "size": 6291456
  }
}
```

**Response:**
```json
{
  "uploadUrl": "https://outlook.office.com/...",
  "expirationDateTime": "2025-10-13T12:00:00Z"
}
```

### 3. Upload Chunk
```http
PUT {uploadUrl}
Content-Length: 4194304
Content-Range: bytes 0-4194303/6291456

<binary data>
```

**Response (intermediate):**
```json
{
  "expirationDateTime": "2025-10-13T12:00:00Z",
  "nextExpectedRanges": ["4194304-"]
}
```

**Response (final):**
```json
{
  "id": "attachment-id-abc123",
  "name": "large-file.pdf",
  "size": 6291456
}
```

### 4. Send Draft
```http
POST https://graph.microsoft.com/v1.0/me/messages/{id}/send
```

**Response:** `202 Accepted` (no body)

---

## Feature Flags

### Environment Variables

```bash
# Enable upload sessions (default: false)
MS_UPLOAD_SESSIONS_ENABLED=true

# Threshold for upload session (default: 3 MiB = 3145728 bytes)
MS_UPLOAD_SESSION_THRESHOLD_BYTES=3145728

# Chunk size for uploads (default: 4 MiB, must be 320 KiB multiple)
MS_UPLOAD_CHUNK_SIZE_BYTES=4194304

# Integration test gate (default: false)
TEST_MICROSOFT_UPLOAD_INTEGRATION=false
```

### Runtime Configuration (src/config/prefs.py)

```python
MS_UPLOAD_SESSIONS_ENABLED = os.getenv("MS_UPLOAD_SESSIONS_ENABLED", "false").lower() == "true"
MS_UPLOAD_SESSION_THRESHOLD_BYTES = int(os.getenv("MS_UPLOAD_SESSION_THRESHOLD_BYTES", "3145728"))
MS_UPLOAD_CHUNK_SIZE_BYTES = int(os.getenv("MS_UPLOAD_CHUNK_SIZE_BYTES", "4194304"))

# Validate chunk size is 320 KiB multiple
if MS_UPLOAD_CHUNK_SIZE_BYTES % (320 * 1024) != 0:
    raise ValueError(f"MS_UPLOAD_CHUNK_SIZE_BYTES must be multiple of 320 KiB, got {MS_UPLOAD_CHUNK_SIZE_BYTES}")
```

---

## Next Steps

1. Create `microsoft_upload.py` module with stub functions
2. Add feature flags to `src/config/prefs.py`
3. Integrate upload session logic into `microsoft.py`
4. Add telemetry metrics and recording rules
5. Write comprehensive unit tests
6. Create gated integration test
7. Document spec and evidence

---

**Created:** 2025-10-12
**Owner:** Platform Engineering
**Status:** Ready to implement
