# Bootstrap Script Quick Start

## TL;DR

```bash
# Create initial admin for your tenant
python scripts/bootstrap.py --user admin@example.com --tenant my-tenant
```

That's it! The script creates:
- Admin user with full privileges
- Default team with admin as member
- Default workspace for the team
- Audit trail of all operations

## Common Commands

### First-Time Setup
```bash
python scripts/bootstrap.py --user admin@acme.com --tenant acme
```

### Check Configuration (No Changes)
```bash
python scripts/bootstrap.py --user admin@acme.com --tenant acme --dry-run
```

### Re-run Safely (Idempotent)
```bash
# Safe to run multiple times - won't create duplicates
python scripts/bootstrap.py --user admin@acme.com --tenant acme
```

### Using Environment Variables
```bash
# Unix/Linux/macOS
export BOOTSTRAP_ADMIN_USER=admin@acme.com
export BOOTSTRAP_TENANT=acme
python scripts/bootstrap.py

# Windows PowerShell
$env:BOOTSTRAP_ADMIN_USER = "admin@acme.com"
$env:BOOTSTRAP_TENANT = "acme"
python scripts/bootstrap.py
```

### Quiet Mode (No Output)
```bash
python scripts/bootstrap.py --user admin@acme.com --tenant acme --quiet
```

## What Gets Created

For tenant `acme` with user `admin@acme.com`:

| Resource | ID | Location |
|----------|----|---------|
| Team | `team-acme-default` | `logs/teams.jsonl` |
| Workspace | `ws-acme-default` | `logs/workspaces.jsonl` |
| Audit Events | varies | `audit/audit-YYYY-MM-DD.jsonl` |

## Testing

```bash
# PowerShell (Windows)
.\scripts\test-bootstrap.ps1

# Bash (Unix/Linux/macOS)
./scripts/test-bootstrap.sh
```

## Need Help?

```bash
python scripts/bootstrap.py --help
```

See [BOOTSTRAP_README.md](BOOTSTRAP_README.md) for full documentation.

---

**Sprint 34A: Collaborative governance**
