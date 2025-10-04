"""
Envelope encryption using AES-256-GCM.

Sprint 33B: Encrypt/decrypt with keyring support.
"""

import base64
from typing import Any

from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from .keyring import get_key


def encrypt(plaintext: bytes, keyring_key: dict) -> dict:
    """
    Encrypt data using envelope encryption with AES-256-GCM.

    Args:
        plaintext: Raw bytes to encrypt
        keyring_key: Key record from keyring (must have key_material_base64)

    Returns:
        Envelope blob with key_id, nonce, ciphertext, tag

    Example:
        >>> from src.crypto.keyring import active_key
        >>> key = active_key()
        >>> envelope = encrypt(b"secret data", key)
        >>> envelope['key_id']
        'key-001'
        >>> 'ciphertext' in envelope
        True
    """
    key_id = keyring_key["key_id"]
    key_material_b64 = keyring_key["key_material_base64"]
    key_material = base64.b64decode(key_material_b64)

    # Generate random nonce (96 bits recommended for GCM)
    import os

    nonce = os.urandom(12)

    # Encrypt with AESGCM
    aesgcm = AESGCM(key_material)
    ciphertext = aesgcm.encrypt(nonce, plaintext, None)

    # AESGCM returns ciphertext + tag concatenated
    # Tag is last 16 bytes
    tag = ciphertext[-16:]
    ciphertext_only = ciphertext[:-16]

    return {
        "key_id": key_id,
        "nonce": base64.b64encode(nonce).decode("utf-8"),
        "ciphertext": base64.b64encode(ciphertext_only).decode("utf-8"),
        "tag": base64.b64encode(tag).decode("utf-8"),
    }


def decrypt(envelope: dict, keyring_get_fn: Any = None) -> bytes:
    """
    Decrypt envelope-encrypted data.

    Args:
        envelope: Envelope blob with key_id, nonce, ciphertext, tag
        keyring_get_fn: Function to retrieve key by key_id (defaults to get_key)

    Returns:
        Decrypted plaintext bytes

    Raises:
        ValueError: If key not found or decryption fails

    Example:
        >>> envelope = {"key_id": "key-001", "nonce": "...", "ciphertext": "...", "tag": "..."}
        >>> plaintext = decrypt(envelope)
        >>> plaintext
        b'secret data'
    """
    if keyring_get_fn is None:
        keyring_get_fn = get_key

    key_id = envelope["key_id"]
    key_record = keyring_get_fn(key_id)

    if not key_record:
        raise ValueError(f"Key not found: {key_id}")

    key_material_b64 = key_record["key_material_base64"]
    key_material = base64.b64decode(key_material_b64)

    nonce = base64.b64decode(envelope["nonce"])
    ciphertext_only = base64.b64decode(envelope["ciphertext"])
    tag = base64.b64decode(envelope["tag"])

    # Reconstruct full ciphertext (ciphertext + tag)
    ciphertext = ciphertext_only + tag

    # Decrypt with AESGCM
    aesgcm = AESGCM(key_material)
    try:
        plaintext = aesgcm.decrypt(nonce, ciphertext, None)
        return plaintext
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}") from e
