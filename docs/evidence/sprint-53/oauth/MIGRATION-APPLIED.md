# OAuth Tokens Database Migration - Sprint 53 Phase B

**Date:** October 8, 2025
**Migration:** `bb51836389e7_add_oauth_tokens_table.py`
**Status:** ✅ Applied Successfully

---

## Migration Details

**Revision ID:** `bb51836389e7`
**Previous Revision:** `ce6ac882b60d` (Sprint 51 auth tables)
**Description:** Add oauth_tokens table for encrypted OAuth token storage

---

## Table Structure

### oauth_tokens

| Column | Type | Nullable | Default | Description |
|--------|------|----------|---------|-------------|
| id | UUID | NO | gen_random_uuid() | Primary key |
| workspace_id | UUID | NO | - | Multi-tenant isolation |
| actor_type | actor_type_enum | NO | - | 'user' or 'api_key' |
| actor_id | TEXT | NO | - | User ID or API key ID |
| provider | TEXT | NO | - | OAuth provider (google, microsoft) |
| scopes | TEXT | YES | - | Space-separated OAuth scopes |
| encrypted_access_token | TEXT | NO | - | Fernet-encrypted access token |
| encrypted_refresh_token | TEXT | YES | - | Fernet-encrypted refresh token |
| access_token_expires_at | TIMESTAMP | YES | - | Token expiry (UTC) |
| created_at | TIMESTAMP | NO | now() | Record creation timestamp |
| updated_at | TIMESTAMP | NO | now() | Record update timestamp |

---

## Constraints

### Primary Key
- `oauth_tokens_pkey` on `id`

### Unique Constraint
- `uq_oauth_tokens_identity` on `(workspace_id, provider, actor_type, actor_id)`
  - Ensures one OAuth connection per user/provider/workspace combination
  - Allows multiple providers per user
  - Allows multiple workspaces per user

### NOT NULL Constraints
- All identity columns (workspace_id, actor_type, actor_id, provider)
- Encrypted access token required
- Timestamps required

---

## Indexes

1. **idx_oauth_tokens_workspace_id**
   - Columns: `workspace_id`
   - Purpose: Fast filtering by workspace

2. **idx_oauth_tokens_workspace_provider**
   - Columns: `workspace_id, provider`
   - Purpose: Fast lookup for specific provider connections

---

## ENUM Type Reuse

**Challenge:** The `actor_type_enum` was created in Sprint 51 migration (ce6ac882b60d).

**Solution:** Use `postgresql.ENUM` with `create_type=False` to reference existing type:

```python
actor_type_enum = postgresql.ENUM("user", "api_key", name="actor_type_enum", create_type=False)
```

**Why this matters:**
- Avoids "type already exists" error
- Maintains type consistency across tables
- Follows PostgreSQL best practices

---

## Migration Execution

### Local Development

```bash
# Load .env file (DATABASE_URL)
python -m alembic upgrade head
```

**Output:**
```
INFO  [alembic.runtime.migration] Context impl PostgresqlImpl.
INFO  [alembic.runtime.migration] Will assume transactional DDL.
INFO  [alembic.runtime.migration] Running upgrade ce6ac882b60d -> bb51836389e7, add oauth_tokens table
```

**Verification:**
```bash
python -m alembic current
# Output: bb51836389e7 (head)
```

### Production (Railway)

**Not yet deployed.** Migration exists only in feature branch `sprint/53-provider-vertical-slice`.

**Deployment plan:**
1. Merge feature branch to main
2. Railway will auto-detect migration
3. Apply with: `railway run alembic upgrade head`
4. Verify with: `railway run alembic current`

---

## Database Verification

**Query:**
```sql
SELECT column_name, data_type, is_nullable, column_default
FROM information_schema.columns
WHERE table_name = 'oauth_tokens'
ORDER BY ordinal_position;
```

**Result:** ✅ All 11 columns present with correct types

**Constraints Query:**
```sql
SELECT constraint_name, constraint_type
FROM information_schema.table_constraints
WHERE table_name = 'oauth_tokens';
```

**Result:** ✅ Primary key + unique constraint present

---

## Integration with OAuthTokenCache

The `src/auth/oauth/tokens.py` module (created in Phase A) is ready to use this table:

```python
class OAuthTokenCache:
    async def _db_store(self, ...):
        # INSERT INTO oauth_tokens (...) VALUES (...)
        # ON CONFLICT (workspace_id, provider, actor_type, actor_id)
        # DO UPDATE SET ...

    async def _db_get(self, ...):
        # SELECT * FROM oauth_tokens
        # WHERE workspace_id = %s
        #   AND provider = %s
        #   AND actor_type = %s
        #   AND actor_id = %s
```

**Database methods are currently stubs** - will be implemented in this phase.

---

## Security Notes

1. **Encryption at Rest:**
   - Access and refresh tokens encrypted with Fernet (AES-128)
   - Requires `OAUTH_ENCRYPTION_KEY` environment variable
   - Key generated in Phase A: `Mvwr_5P4VoevQaR7WcNUom56zII1QuECnErU0PfBSSE=`
   - Key set in Railway: ✅ Complete

2. **Redis Caching:**
   - Decrypted tokens cached in Redis for fast access
   - Redis on private Railway network (redis.railway.internal)
   - TTL matches token expiry

3. **Multi-Tenant Isolation:**
   - workspace_id required for all operations
   - Unique constraint prevents cross-workspace token leakage

---

## Rollback Plan

If issues arise, rollback with:

```bash
python -m alembic downgrade ce6ac882b60d
```

**Effects:**
- Drops oauth_tokens table
- Drops indexes
- Does NOT drop actor_type_enum (shared with other tables)

---

## Alembic Environment Fixes

### Issue 1: .env Loading

**Problem:** Alembic didn't load DATABASE_URL from .env file.

**Fix:** Added to `migrations/env.py`:
```python
from dotenv import load_dotenv
load_dotenv()
```

### Issue 2: URL-Encoded Characters

**Problem:** DATABASE_URL contains `%` characters (URL-encoded password), causing ConfigParser interpolation error.

**Fix:** Escape % characters in `migrations/env.py`:
```python
database_url_escaped = database_url.replace("%", "%%")
config.set_main_option("sqlalchemy.url", database_url_escaped)
```

---

## Files Modified

```
migrations/
├── env.py (modified: dotenv loading, % escaping)
└── versions/
    └── bb51836389e7_add_oauth_tokens_table.py (created)
```

**Lines Added:** ~60 lines (migration) + 4 lines (env.py)

---

## Next Steps

1. ✅ **Migration Applied**
2. ⏳ **Implement OAuth endpoints** - /oauth/google/authorize, /oauth/google/callback
3. ⏳ **Implement OAuthTokenCache DB methods** - _db_store(), _db_get()
4. ⏳ **Test end-to-end OAuth flow** - Store/retrieve tokens

---

## Success Criteria

- [x] Migration file created
- [x] Migration applied to development database
- [x] Table structure verified (11 columns)
- [x] Unique constraint present
- [x] Indexes created (2 indexes)
- [x] ENUM type reused (no duplication error)
- [x] Documentation complete

**Status:** ✅ **COMPLETE** - Ready for OAuth endpoint implementation

---

**Evidence:** This document serves as proof that the oauth_tokens table is ready for Phase B OAuth flow implementation.
