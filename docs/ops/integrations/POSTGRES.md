# Postgres Integration

## What this integrates

PostgreSQL database for persistent storage of OAuth tokens, API keys, audit logs, and user roles. Deployed as a Railway service with automatic backups via GitHub Actions.

## Where it's configured

- Railway Dashboard → PostgreSQL service (auto-provisioned)
- `src/db/connection.py` - asyncpg connection pool
- `migrations/` - Alembic database migrations (if present)
- `scripts/db_backup.py` - Automated backup script
- `src/auth/tokens.py`, `src/db/audit.py` - Token and audit storage

## Env vars / secrets

| Name | Scope | Where set | Notes |
|------|-------|-----------|-------|
| `DATABASE_URL` | Runtime | Railway Variables (auto) | Format: `postgresql://user:pass@host:port/db` |
| `DATABASE_PUBLIC_URL` | GitHub Actions | Repository Secrets | For pg_dump from Actions (public accessible endpoint) |

## How to verify (60 seconds)

```bash
# 1. Test connection
psql "$DATABASE_URL" -c "SELECT 1"
# Returns: 1 (1 row)

# 2. Check database size
psql "$DATABASE_URL" -c "SELECT pg_size_pretty(pg_database_size(current_database()))"
# Returns: e.g., "145 MB"

# 3. List tables
psql "$DATABASE_URL" -c "\dt"
# Shows: api_keys, roles, oauth_tokens, audit_log, etc.

# 4. Check recent audit entries
psql "$DATABASE_URL" -c "SELECT COUNT(*) FROM audit_log WHERE created_at > NOW() - INTERVAL '24 hours'"
# Returns count of recent audit entries

# 5. Verify migrations applied (if using Alembic)
psql "$DATABASE_URL" -c "SELECT version_num FROM alembic_version"
# Shows current migration version
```

## Common failure → quick fix

### Connection refused or authentication failed
**Cause:** DATABASE_URL incorrect or database service down
**Fix:**
1. Check Railway → PostgreSQL service status (should be green)
2. Get fresh DATABASE_URL from Railway → PostgreSQL → Connect tab
3. Update Railway → Relay service → Variables → DATABASE_URL

### "Relation does not exist" error
**Cause:** Table missing (migration not run)
**Fix:**
```bash
# Run migrations
alembic upgrade head
# Or manually create tables from schema
psql "$DATABASE_URL" -f schema.sql
```

### Database backup failing in GitHub Actions
**Cause:** DATABASE_PUBLIC_URL not set or network blocked
**Fix:**
1. Verify Railway PostgreSQL has public networking enabled
2. Get public connection string from Railway
3. Update GitHub Secrets → DATABASE_PUBLIC_URL
4. Format: `postgresql://user:pass@public-host:port/db`

### Slow queries
**Cause:** Missing indexes or large table scans
**Fix:**
```bash
# Check slow queries
psql "$DATABASE_URL" -c "SELECT query, mean_exec_time FROM pg_stat_statements ORDER BY mean_exec_time DESC LIMIT 10"
# Add indexes as needed
psql "$DATABASE_URL" -c "CREATE INDEX idx_audit_created ON audit_log(created_at)"
```

## References

- src/db/connection.py - Connection pool using asyncpg
- scripts/db_backup.py - pg_dump wrapper with compression and retention
- .github/workflows/backup.yml:36-40 - Daily backup job (09:00 UTC)
- Railway PostgreSQL Service - Managed PostgreSQL with daily snapshots
- migrations/ - Alembic migration scripts (if present)
