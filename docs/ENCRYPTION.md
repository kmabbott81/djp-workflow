# Envelope Encryption - Sprint 33B

## Overview

AES-256-GCM envelope encryption for artifacts and logs with local JSONL keyring. Supports key rotation while maintaining access to historical data encrypted with retired keys.

## Architecture

### Envelope Encryption

Each artifact is encrypted with AES-256-GCM using a Data Encryption Key (DEK):

```
Plaintext → AES-256-GCM → Ciphertext + Tag
                ↓
            Envelope = {key_id, nonce, ciphertext, tag}
```

### Keyring Structure

Keys stored in `logs/keyring.jsonl` (append-only):

```jsonl
{"key_id": "key-001", "alg": "AES256-GCM", "created_at": "2025-10-03T...", "status": "active", "key_material_base64": "..."}
{"key_id": "key-001", "alg": "AES256-GCM", "created_at": "2025-10-03T...", "status": "retired", "retired_at": "2025-12-03T..."}
{"key_id": "key-002", "alg": "AES256-GCM", "created_at": "2025-12-03T...", "status": "active", "key_material_base64": "..."}
```

**Last-wins semantics**: Most recent entry for a key_id determines status.

## Configuration

### Environment Variables

```bash
# Enable encryption
ENCRYPTION_ENABLED=true

# Keyring path
KEYRING_PATH=logs/keyring.jsonl

# Active key (managed automatically)
ACTIVE_KEY_ID=auto

# Rotation policy (days)
KEY_ROTATION_DAYS=90
```

## Key Management

### Keyring Operations

```bash
# List all keys (masks key material)
python scripts/keyring.py list

# Show active key
python scripts/keyring.py active

# Rotate key (creates new active, retires old)
python scripts/keyring.py rotate
```

Via compliance CLI:

```bash
python scripts/compliance.py list-keys
python scripts/compliance.py rotate-key
```

### Key Rotation

Rotation creates a new active key and retires the previous one:

1. Current active key → status: retired
2. New key generated with incremented ID
3. New key → status: active

**Historical data remains accessible**: Retired keys can still decrypt old artifacts.

### Rotation Policy

Automatic rotation based on `KEY_ROTATION_DAYS`:

```bash
# Dashboard shows warning when key age exceeds policy
# Manual rotation:
python scripts/compliance.py rotate-key
```

## Encrypted Storage

### File Layout

Each artifact has two files:

```
artifact.md.enc     # Encrypted envelope (JSON)
artifact.md.json    # Metadata sidecar
```

**Sidecar metadata**:
```json
{
  "label": "Confidential",
  "tenant": "acme-corp",
  "key_id": "key-002",
  "created_at": "2025-10-03T12:00:00Z",
  "size": 1024,
  "encrypted": true
}
```

### Write Encrypted

```python
from src.storage.secure_io import write_encrypted

meta = write_encrypted(
    path=Path("artifact.md"),
    data=b"sensitive content",
    label="Confidential",
    tenant="acme-corp"
)
# Creates: artifact.md.enc, artifact.md.json
```

### Read Encrypted

```python
from src.storage.secure_io import read_encrypted

data = read_encrypted(
    path=Path("artifact.md"),
    user_clearance="Confidential"
)
# Returns decrypted plaintext
```

## Backward Compatibility

### Plaintext Fallback

If `ENCRYPTION_ENABLED=false`:
- `write_encrypted()` writes plaintext to `path`
- `read_encrypted()` reads plaintext from `path`
- Sidecar still created with `encrypted: false`

### Migration

Existing plaintext artifacts continue to work:

```python
# Old artifact (plaintext)
artifact.md

# After enabling encryption
artifact.md         # Still readable via plaintext fallback
artifact.md.json    # Sidecar added

# New artifacts
artifact2.md.enc    # Encrypted
artifact2.md.json   # Sidecar with key_id
```

## Tiered Storage Integration

### Preservation Across Tiers

Sidecar metadata preserved during tier promotions:

```
hot/tenant-a/artifact.md.enc
hot/tenant-a/artifact.md.json
  ↓ (promotion)
warm/tenant-a/artifact.md.enc
warm/tenant-a/artifact.md.json
```

Both files must move together to maintain decryption capability.

## Key Recovery

### Lost Keyring

**Prevention**: Back up `logs/keyring.jsonl` regularly

**Recovery**:
1. Restore keyring from backup
2. If no backup: Data loss for encrypted artifacts
3. Plaintext artifacts unaffected

### Corrupted Keyring

**Symptoms**:
- `ValueError: Key not found: key-XXX`
- Decryption failures

**Fix**:
```bash
# Validate keyring format
cat logs/keyring.jsonl | jq .

# Check for malformed lines
grep -v '^{' logs/keyring.jsonl

# Restore from backup
cp backups/keyring.jsonl.bak logs/keyring.jsonl
```

## Re-encryption After Compromise

### Bulk Re-encryption

If a key is compromised:

1. Rotate key immediately
2. Re-encrypt all artifacts with new key
3. Retire compromised key

```bash
# Rotate key
python scripts/compliance.py rotate-key

# Re-encrypt artifacts (future enhancement)
# python scripts/re_encrypt.py --key-id key-XXX --dry-run
```

**Note**: Bulk re-encryption tool not implemented in Sprint 33B (future work).

## Performance Considerations

### Encryption Overhead

- **Write**: ~1-2ms per artifact (small files)
- **Read**: ~1-2ms per artifact
- **Storage**: ~10% overhead (metadata sidecar)

### Key Cache

Active key cached in memory for session:
- First call: Load from JSONL
- Subsequent calls: Use cached key
- Cache invalidated on rotation

### Large Files

For files >100MB, consider chunked encryption (future enhancement).

## Security Guarantees

1. **AES-256-GCM**: Industry-standard authenticated encryption
2. **Unique nonces**: Random 96-bit nonce per encryption
3. **Tamper detection**: GCM tag verifies integrity
4. **Key isolation**: Key material never logged or exported
5. **Audit trail**: All key operations logged to governance events

## Compliance Alignment

- **GDPR**: Encryption at rest, key rotation
- **SOC 2**: Cryptographic controls, key management
- **ISO 27001**: Encryption standards, key lifecycle
- **HIPAA**: Technical safeguards, key management (§164.312)

## Troubleshooting

### Decryption Failed

**Symptom**: `ValueError: Decryption failed`

**Causes**:
1. Corrupted ciphertext
2. Wrong key_id in envelope
3. Tampered data (GCM tag mismatch)

**Check**:
```bash
# Verify key exists
python scripts/keyring.py list | grep key-XXX

# Check sidecar metadata
cat artifact.md.json | jq .key_id

# Verify envelope format
cat artifact.md.enc | jq .
```

### Key Not Found

**Symptom**: `ValueError: Key not found: key-XXX`

**Solutions**:
- Restore keyring from backup
- Check keyring file exists: `ls -l logs/keyring.jsonl`
- Verify key_id in envelope matches keyring

### Rotation Overdue Warning

**Symptom**: Dashboard shows "Key rotation recommended"

**Action**:
```bash
# Check current key age
python scripts/keyring.py active

# Rotate if overdue
python scripts/compliance.py rotate-key
```

## See Also

- [CLASSIFICATION.md](CLASSIFICATION.md) - Data labels and clearances
- [COMPLIANCE.md](COMPLIANCE.md) - Export and deletion
- [SECURITY.md](SECURITY.md) - RBAC roles
- [OPERATIONS.md](OPERATIONS.md) - Key rotation runbook
