# Cloud Folder Connectors

Connect and sync files from multiple cloud storage providers for ingestion and indexing.

## Supported Providers

| Provider | Auth Type | Delta Sync | Rate Limits |
|----------|-----------|------------|-------------|
| **Google Drive** | Service Account / OAuth | ✅ Changes API | 1000 req/100s/user |
| **OneDrive** | OAuth (Graph API) | ✅ Delta API | 1200 req/5min/app |
| **SharePoint** | OAuth (Graph API) | ✅ Delta API | 1200 req/5min/app |
| **Dropbox** | OAuth | ✅ Cursor-based | 300 req/min |
| **Box** | OAuth | ✅ Event Stream | 10 req/sec |
| **AWS S3** | IAM / Access Keys | ⚠️ Timestamp-based | No limit (costs apply) |
| **Google Cloud Storage** | Service Account | ⚠️ Timestamp-based | No limit (costs apply) |

## Setup

### Google Drive

**Required Scopes:**
- `https://www.googleapis.com/auth/drive.readonly`

**Environment Variables:**
```bash
GDRIVE_SERVICE_ACCOUNT_JSON=/path/to/service-account.json
# OR
GDRIVE_CREDENTIALS_JSON=/path/to/oauth-credentials.json
```

**Service Account Setup:**
1. Create project in Google Cloud Console
2. Enable Drive API
3. Create service account with Drive API access
4. Share target folders with service account email

**OAuth Setup:**
1. Create OAuth 2.0 Client ID (Desktop app)
2. Download credentials JSON
3. Run OAuth flow to get refresh token

### OneDrive

**Required Scopes:**
- `Files.Read` or `Files.Read.All`

**Environment Variables:**
```bash
ONEDRIVE_CLIENT_ID=your-client-id
ONEDRIVE_CLIENT_SECRET=your-client-secret
ONEDRIVE_TENANT_ID=your-tenant-id
ONEDRIVE_ACCESS_TOKEN=your-access-token
```

**Setup:**
1. Register app in Azure AD
2. Add delegated permissions: Files.Read.All
3. Generate access token via OAuth flow
4. Implement token refresh (recommended: use MSAL library)

### SharePoint

**Required Scopes:**
- `Sites.Read.All`
- `Files.Read.All`

**Environment Variables:**
```bash
SHAREPOINT_CLIENT_ID=your-client-id
SHAREPOINT_CLIENT_SECRET=your-client-secret
SHAREPOINT_TENANT_ID=your-tenant-id
SHAREPOINT_SITE_ID=your-site-id
SHAREPOINT_ACCESS_TOKEN=your-access-token
```

**Setup:**
1. Same as OneDrive (use Azure AD)
2. Get site ID:
   ```bash
   GET https://graph.microsoft.com/v1.0/sites/{hostname}:/sites/{site-name}
   ```
3. Store site ID in `SHAREPOINT_SITE_ID`

### Dropbox

**Required Scopes:**
- `files.metadata.read`
- `files.content.read`

**Environment Variables:**
```bash
DROPBOX_ACCESS_TOKEN=your-access-token
# OR
DROPBOX_APP_KEY=your-app-key
DROPBOX_APP_SECRET=your-app-secret
```

**Setup:**
1. Create app at https://www.dropbox.com/developers/apps
2. Set permissions: files.metadata.read, files.content.read
3. Generate access token (Settings → OAuth 2 → Generate)

**Webhook Setup (optional):**
- Configure webhook URL in app settings
- Use `/files/list_folder/longpoll` for real-time notifications

### Box

**Required Scopes:**
- `root_readwrite` or `read_all_files_and_folders`

**Environment Variables:**
```bash
BOX_ACCESS_TOKEN=your-access-token
# OR
BOX_CLIENT_ID=your-client-id
BOX_CLIENT_SECRET=your-client-secret
```

**Setup:**
1. Create app at https://app.box.com/developers/console
2. Configure OAuth 2.0 with appropriate scopes
3. Generate access token or implement OAuth flow

### AWS S3

**Environment Variables:**
```bash
AWS_ACCESS_KEY_ID=your-access-key
AWS_SECRET_ACCESS_KEY=your-secret-key
AWS_REGION=us-east-1
S3_BUCKET_NAME=your-bucket-name
```

**Setup:**
1. Create IAM user with S3 read permissions
2. Attach policy: `AmazonS3ReadOnlyAccess`
3. Generate access keys

**Delta Sync:**
- S3 doesn't have native delta sync
- Uses timestamp-based filtering (pseudo-delta)
- For production: use S3 Event Notifications → SQS/SNS

### Google Cloud Storage

**Environment Variables:**
```bash
GCS_SERVICE_ACCOUNT_JSON=/path/to/service-account.json
GCS_BUCKET_NAME=your-bucket-name
```

**Setup:**
1. Create service account in GCP Console
2. Grant `Storage Object Viewer` role
3. Download service account JSON key

**Delta Sync:**
- GCS doesn't have native delta sync
- Uses timestamp-based filtering (pseudo-delta)
- For production: use GCS Pub/Sub notifications

## Usage

### Basic Usage

```python
from src.connectors.cloud import GDriveConnector, ConnectorConfig
from src.metadata import insert_staged_item, StagedItemRecord

# Configure connector
config = ConnectorConfig(
    tenant_id="tenant-123",
    connector_name="gdrive",
    include_patterns=["*.pdf", "*.docx"],
    exclude_patterns=["*/Archive/*"],
    mime_types=["application/pdf"],
    max_size_bytes=50_000_000,  # 50 MB
)

# Create connector
connector = GDriveConnector(config)

# Authenticate
if not connector.authenticate():
    print("Authentication failed")
    exit(1)

# List items
items, next_page_token = connector.list_items()

# Filter and stage
filtered = connector.filter_items(items)

for item in filtered:
    record = StagedItemRecord(
        tenant_id=config.tenant_id,
        connector=config.connector_name,
        external_id=item.external_id,
        path=item.path,
        name=item.name,
        mime_type=item.mime_type,
        size_bytes=item.size_bytes,
        last_modified=item.last_modified.isoformat(),
        status="staged",
    )
    insert_staged_item(record)
```

### Incremental Sync (Delta)

```python
from src.metadata import get_delta_token, save_delta_token

# Get last delta token
delta_token = get_delta_token(tenant_id="tenant-123", connector="gdrive")

# Fetch changes
changes, new_delta_token = connector.get_delta_changes(delta_token)

# Process changes
for item in connector.filter_items(changes):
    # Insert/update staged item
    record = StagedItemRecord(...)
    insert_staged_item(record)

# Save new delta token
save_delta_token(tenant_id="tenant-123", connector="gdrive", delta_token=new_delta_token)
```

### Include/Exclude Patterns

```python
config = ConnectorConfig(
    tenant_id="tenant-123",
    connector_name="gdrive",
    include_patterns=[
        "*.pdf",        # All PDFs
        "*.docx",       # All Word docs
        "/Reports/*",   # Everything in Reports folder
    ],
    exclude_patterns=[
        "*/Archive/*",  # Exclude Archive folders
        "*_draft*",     # Exclude drafts
        "*.tmp",        # Exclude temp files
    ],
)
```

## Error Handling

All connectors handle common errors gracefully:

```python
items, next_token = connector.list_items()

if not items and not next_token:
    # Authentication failed or API error
    print("Sync failed - check logs")
```

**Common Issues:**

| Error | Cause | Solution |
|-------|-------|----------|
| Authentication failed | Invalid/expired token | Refresh token or re-authenticate |
| Rate limit exceeded | Too many requests | Implement exponential backoff |
| Permission denied | Insufficient scopes | Update app permissions |
| Quota exceeded | Daily API quota hit | Wait or request increase |

## Rate Limits & Quotas

### Best Practices

1. **Batch Operations**: Use pagination with reasonable page sizes (100-500 items)
2. **Exponential Backoff**: Retry with increasing delays on 429 errors
3. **Delta Sync**: Always use delta endpoints instead of full re-sync
4. **Caching**: Store delta tokens to avoid redundant API calls

### Provider-Specific Notes

**Google Drive:**
- Per-user quota: 1000 requests per 100 seconds
- Batch operations count as single request
- Changes API is more efficient than full listing

**Microsoft Graph (OneDrive/SharePoint):**
- Per-app quota: 1200 requests per 5 minutes
- Delta queries don't count toward quota as heavily
- Use `$select` to reduce response size

**Dropbox:**
- 300 requests per minute per app
- Cursor-based pagination is efficient
- Longpoll endpoint for real-time updates

**Box:**
- 10 requests per second per user
- Event stream is most efficient for delta sync
- Consider using Box Skills for automation

**S3/GCS:**
- No hard rate limits, but costs per API call
- Use CloudFront/CDN for frequent access
- Prefer event notifications over polling

## Budget Considerations

### Connector Costs

| Provider | API Costs | Storage Costs | Notes |
|----------|-----------|---------------|-------|
| **GDrive** | Free (quota limits) | Storage billed separately | Quota: 1 billion requests/day |
| **OneDrive** | Free (quota limits) | Included with M365 | Graph API throttling applies |
| **SharePoint** | Free (quota limits) | Included with M365 | Same as OneDrive |
| **Dropbox** | Free (quota limits) | Storage billed | Rate limits enforced |
| **Box** | Free (quota limits) | Storage billed | Enterprise tier recommended |
| **S3** | $0.0004/1000 LIST | $0.023/GB/month | Use S3 Intelligent-Tiering |
| **GCS** | $0.05/10,000 ops | $0.020/GB/month | Use lifecycle policies |

### Cost Optimization

1. **Full Sync vs Delta:**
   - Full sync: 10,000 files = 100+ API calls
   - Delta sync: Only changed files (~10-100 calls)
   - **Recommendation**: Always use delta after initial sync

2. **Filtering:**
   - Apply include/exclude patterns to reduce staged items
   - Skip large binary files (videos, ISOs) unless needed
   - Set `max_size_bytes` to avoid ingesting huge files

3. **Scheduling:**
   - Run delta sync on schedule (hourly, daily)
   - Use webhooks for real-time updates (Dropbox, Box)
   - Batch operations during off-peak hours

4. **Storage:**
   - S3/GCS: Use lifecycle policies to archive old files
   - Enable compression for text-heavy corpora
   - Clean up staged items after successful ingestion

## Security

### Credential Storage

**Never commit credentials to git.** Use:
- Environment variables (`.env` file, not committed)
- AWS Secrets Manager / GCP Secret Manager
- Azure Key Vault

### Least Privilege

Grant minimal permissions:
- **Read-only** scopes where possible
- **Folder-level** access instead of root
- **Service accounts** for automation (no user impersonation)

### Audit Logging

All connector operations are logged to audit trail:

```python
from src.security.audit import get_audit_logger, AuditAction

logger = get_audit_logger()
logger.log_success(
    tenant_id="tenant-123",
    user_id="system",
    action=AuditAction.INGEST_CORPUS,
    resource_type="connector",
    resource_id="gdrive",
    metadata={"files_staged": 1234, "connector": "gdrive"},
)
```

## Migrations

### Adding Connectors to Existing Tenants

1. **Stage existing files:**
   ```python
   # Run initial full sync
   items, token = connector.list_items()
   # Save all items with status='staged'
   ```

2. **Save delta token:**
   ```python
   save_delta_token(tenant_id, connector_name, token)
   ```

3. **Schedule delta sync:**
   ```python
   # Cron job or worker to run hourly
   delta_token = get_delta_token(tenant_id, connector_name)
   changes, new_token = connector.get_delta_changes(delta_token)
   save_delta_token(tenant_id, connector_name, new_token)
   ```

### Rollback Plan

If connector causes issues:

1. **Disable connector:**
   ```python
   # Mark all staged items as 'skipped'
   update_staged_item_status(item_id, status="skipped")
   ```

2. **Clear staged items:**
   ```sql
   DELETE FROM staged_items WHERE tenant_id = ? AND connector = ?
   ```

3. **Revoke credentials:**
   - Remove environment variables
   - Revoke OAuth tokens in provider console

## Troubleshooting

### Authentication Issues

```bash
# Test authentication
python -c "from src.connectors.cloud import GDriveConnector, ConnectorConfig; \
           connector = GDriveConnector(ConnectorConfig(tenant_id='test', connector_name='gdrive')); \
           print('Auth OK' if connector.authenticate() else 'Auth FAIL')"
```

### Delta Sync Not Working

1. Check delta token exists:
   ```python
   token = get_delta_token("tenant-123", "gdrive")
   print(f"Token: {token}")
   ```

2. Verify changes detected:
   ```python
   changes, new_token = connector.get_delta_changes(token)
   print(f"Found {len(changes)} changes")
   ```

3. Force full re-sync:
   ```python
   # Pass delta_token=None to get fresh state
   changes, new_token = connector.get_delta_changes(delta_token=None)
   ```

### Performance Issues

1. **Reduce page size:** Lower `MaxKeys` / `pageSize` if hitting timeouts
2. **Parallel workers:** Run multiple workers for different folders
3. **Filter early:** Apply include/exclude patterns before staging
4. **Monitor quotas:** Check provider console for quota usage

## Next Steps

1. Set up connectors for your providers
2. Run initial full sync to stage files
3. Schedule delta sync jobs (see `Sprint 11` for distributed workers)
4. Monitor staged items in observability dashboard
5. Configure ingestion pipeline (see `Sprint 10`)
