# Bootstrap Script Documentation

## Overview

The `bootstrap.py` script provisions the initial administrative user and security infrastructure for a new tenant. It creates:

1. **Admin User** - A user with Admin role in the default team
2. **Default Team** - A team with the admin user as a member
3. **Default Workspace** - A workspace within the team with admin access
4. **Audit Events** - Full audit trail of all bootstrap operations

## Features

- **Idempotent**: Safe to re-run multiple times without creating duplicates
- **Audited**: All operations logged to audit trail for compliance
- **Validated**: Checks configuration before making any changes
- **Flexible**: Supports both environment variables and CLI flags
- **Clear Output**: Detailed status messages for transparency

## Usage

### Basic Usage (CLI Flags)

```bash
python scripts/bootstrap.py --user admin@example.com --tenant acme-corp
```

### Using Environment Variables

```bash
export BOOTSTRAP_ADMIN_USER=admin@example.com
export BOOTSTRAP_TENANT=acme-corp
python scripts/bootstrap.py
```

### Windows (PowerShell)

```powershell
$env:BOOTSTRAP_ADMIN_USER = "admin@example.com"
$env:BOOTSTRAP_TENANT = "acme-corp"
python scripts/bootstrap.py
```

### CLI Flags Override Environment

```bash
export BOOTSTRAP_ADMIN_USER=default@example.com
python scripts/bootstrap.py --user admin@example.com --tenant acme-corp
# Uses admin@example.com (CLI flag wins)
```

## Command-Line Options

| Option | Short | Description |
|--------|-------|-------------|
| `--user USER` | `-u` | Admin user identifier (email or username) |
| `--tenant TENANT` | `-t` | Tenant identifier |
| `--quiet` | `-q` | Suppress status messages (only show errors) |
| `--dry-run` | | Validate configuration without making changes |
| `--help` | `-h` | Show help message |

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `BOOTSTRAP_ADMIN_USER` | Admin user identifier | (none - required) |
| `BOOTSTRAP_TENANT` | Tenant identifier | (none - required) |
| `AUDIT_LOG_DIR` | Directory for audit logs | `audit` |
| `TEAMS_PATH` | Path to teams JSONL file | `logs/teams.jsonl` |
| `WORKSPACES_PATH` | Path to workspaces JSONL file | `logs/workspaces.jsonl` |

## Examples

### First-Time Setup

```bash
# Create initial admin for new tenant
python scripts/bootstrap.py \
  --user admin@acme-corp.com \
  --tenant acme-corp
```

**Output:**
```
[BOOTSTRAP] ============================================================
[BOOTSTRAP] Starting bootstrap process...
[BOOTSTRAP] ============================================================
[BOOTSTRAP] Configuration validated: user=admin@acme-corp.com, tenant=acme-corp
[BOOTSTRAP] Creating admin user 'admin@acme-corp.com' in team 'team-acme-corp-default'...
[BOOTSTRAP] SUCCESS: Admin user created: admin@acme-corp.com
[BOOTSTRAP] Verifying default team 'team-acme-corp-default'...
[BOOTSTRAP] SUCCESS: Default team exists with admin as Admin
[BOOTSTRAP] Creating default workspace 'ws-acme-corp-default'...
[BOOTSTRAP] SUCCESS: Default workspace created: ws-acme-corp-default
[BOOTSTRAP] ============================================================
[BOOTSTRAP] SUCCESS: Bootstrap completed successfully!
[BOOTSTRAP] ============================================================
[BOOTSTRAP] Tenant:      acme-corp
[BOOTSTRAP] Admin User:  admin@acme-corp.com
[BOOTSTRAP] Team:        team-acme-corp-default
[BOOTSTRAP] Workspace:   ws-acme-corp-default
[BOOTSTRAP] Duration:    0.01s
[BOOTSTRAP] ============================================================
```

### Idempotent Re-run

```bash
# Running again with same parameters
python scripts/bootstrap.py \
  --user admin@acme-corp.com \
  --tenant acme-corp
```

**Output:**
```
[BOOTSTRAP] ============================================================
[BOOTSTRAP] Starting bootstrap process...
[BOOTSTRAP] ============================================================
[BOOTSTRAP] Configuration validated: user=admin@acme-corp.com, tenant=acme-corp
[BOOTSTRAP] Creating admin user 'admin@acme-corp.com' in team 'team-acme-corp-default'...
[BOOTSTRAP] User already exists with role: Admin
[BOOTSTRAP] User already has Admin role, skipping creation
[BOOTSTRAP] Verifying default team 'team-acme-corp-default'...
[BOOTSTRAP] SUCCESS: Default team exists with admin as Admin
[BOOTSTRAP] Creating default workspace 'ws-acme-corp-default'...
[BOOTSTRAP] Workspace already exists, admin has role: Admin
[BOOTSTRAP] Admin already has Admin role in workspace, skipping creation
[BOOTSTRAP] ============================================================
[BOOTSTRAP] SUCCESS: Bootstrap completed successfully!
[BOOTSTRAP] ============================================================
[BOOTSTRAP] Tenant:      acme-corp
[BOOTSTRAP] Admin User:  admin@acme-corp.com
[BOOTSTRAP] Team:        team-acme-corp-default
[BOOTSTRAP] Workspace:   ws-acme-corp-default
[BOOTSTRAP] Duration:    0.00s
[BOOTSTRAP] ============================================================
[BOOTSTRAP] Note: All resources already existed (idempotent re-run)
```

### Dry Run Mode

```bash
# Validate configuration without making changes
python scripts/bootstrap.py \
  --user admin@acme-corp.com \
  --tenant acme-corp \
  --dry-run
```

**Output:**
```
[BOOTSTRAP] DRY RUN: Validating configuration only...
[BOOTSTRAP] Configuration validated: user=admin@acme-corp.com, tenant=acme-corp
[BOOTSTRAP] SUCCESS: Configuration is valid
```

### Quiet Mode

```bash
# Suppress all output except errors
python scripts/bootstrap.py \
  --user admin@acme-corp.com \
  --tenant acme-corp \
  --quiet
```

**Output:** (none if successful)

### Error Handling

```bash
# Missing required parameters
python scripts/bootstrap.py
```

**Output:**
```
[BOOTSTRAP] FAILED: Admin user is required (set BOOTSTRAP_ADMIN_USER or use --user)
```

## Created Resources

When you run bootstrap for tenant `acme-corp` with user `admin@acme-corp.com`:

### 1. Team
- **ID**: `team-acme-corp-default`
- **Name**: `acme-corp Default Team`
- **Members**: `admin@acme-corp.com` (Admin role)
- **File**: `logs/teams.jsonl`

### 2. Workspace
- **ID**: `ws-acme-corp-default`
- **Name**: `acme-corp Default Workspace`
- **Team**: `team-acme-corp-default`
- **Members**: `admin@acme-corp.com` (Admin role)
- **File**: `logs/workspaces.jsonl`

### 3. Audit Events
- **Location**: `audit/audit-YYYY-MM-DD.jsonl`
- **Events**:
  - Admin user creation/update
  - Workspace creation/update
  - All metadata about the operations

## Audit Trail

The script logs all operations to the audit trail. You can query these events:

```bash
# View today's audit log
cat audit/audit-$(date +%Y-%m-%d).jsonl | grep bootstrap
```

Example audit event:
```json
{
  "timestamp": "2025-10-04T20:04:54.393666",
  "tenant_id": "acme-corp",
  "user_id": "system",
  "action": "login",
  "resource_type": "user",
  "resource_id": "admin@acme-corp.com",
  "result": "success",
  "metadata": {
    "operation": "bootstrap_admin_user",
    "team_id": "team-acme-corp-default",
    "role": "Admin",
    "was_existing": false,
    "upgraded": false
  }
}
```

## Integration with Existing Systems

### Teams Module

The script uses `src/security/teams.py`:
- `upsert_team_member()` - Creates team and adds admin
- `get_team_role()` - Checks existing membership

### Workspaces Module

The script uses `src/security/workspaces.py`:
- `upsert_workspace_member()` - Creates workspace and adds admin
- `get_workspace_role()` - Checks existing membership

### Audit Module

The script uses `src/security/audit.py`:
- `get_audit_logger()` - Gets audit logger instance
- `log_success()` - Logs successful operations
- `log_failure()` - Logs failed operations

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Bootstrap failed (configuration error or execution error) |
| 130 | Interrupted by user (Ctrl+C) |

## Troubleshooting

### Missing Required Parameters

**Error:**
```
[BOOTSTRAP] FAILED: Admin user is required (set BOOTSTRAP_ADMIN_USER or use --user)
```

**Solution:**
```bash
python scripts/bootstrap.py --user admin@example.com --tenant my-tenant
```

### Invalid Tenant ID

**Error:**
```
[BOOTSTRAP] FAILED: Tenant ID cannot contain spaces
```

**Solution:** Use a valid tenant ID without spaces:
```bash
python scripts/bootstrap.py --user admin@example.com --tenant my-tenant
# NOT: --tenant "my tenant"
```

### Permission Errors

**Error:**
```
[BOOTSTRAP] ERROR: Failed to create admin user: [Errno 13] Permission denied: 'logs/teams.jsonl'
```

**Solution:** Ensure the script has write permissions to:
- `logs/` directory
- `audit/` directory

```bash
# Create directories if they don't exist
mkdir -p logs audit
chmod 755 logs audit
```

## Security Considerations

1. **Admin Privileges**: The bootstrap script creates a user with full Admin privileges
2. **Audit Logging**: All operations are logged for compliance and security review
3. **Idempotency**: Safe to re-run, but be aware it will modify existing resources if roles differ
4. **Tenant Isolation**: Resources are scoped to the specified tenant

## Testing

A comprehensive test suite is provided in `scripts/test-bootstrap.ps1`:

```powershell
# Run all tests
cd C:\Users\kylem\openai-agents-workflows-2025.09.28-v1
.\scripts\test-bootstrap.ps1
```

Tests covered:
1. CLI flags usage
2. Environment variables usage
3. CLI flags overriding environment
4. Dry run mode
5. Idempotency
6. Error handling

## Related Documentation

- [Teams Documentation](../src/security/teams.py)
- [Workspaces Documentation](../src/security/workspaces.py)
- [Audit Documentation](../src/security/audit.py)
- [RBAC Documentation](../src/security/authz.py)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review audit logs for detailed error information
3. Verify environment variables and CLI flags
4. Check file permissions for logs and audit directories

---

**Sprint 34A: Collaborative governance bootstrap**
