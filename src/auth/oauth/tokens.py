"""OAuth 2.0 token storage with database persistence and Redis caching.

Implements write-through cache pattern:
- Write: Save to database (encrypted), then cache in Redis
- Read: Check Redis first, fall back to database if not cached
- Refresh: Update both database and cache

Sprint 53: Google OAuth token management for Actions API.
"""

import json
import os
from datetime import datetime, timedelta
from typing import Optional

from cryptography.fernet import Fernet


class OAuthTokenCache:
    """Manage OAuth tokens with encrypted database storage and Redis cache.

    Tokens are stored encrypted in the database (source of truth) and cached
    in Redis for fast access. Uses write-through cache pattern.

    Redis key format: oauth:token:{provider}:{workspace_id}:{actor_id}
    TTL: Match token expiry (or 1 hour default)

    Database table: oauth_tokens
    - Encrypted: access_token, refresh_token
    - Plaintext: provider, workspace_id, actor_id, expires_at, scope

    Example:
        cache = OAuthTokenCache()

        # Store tokens after OAuth callback
        cache.store_tokens(
            provider="google",
            workspace_id="ws_123",
            actor_id="user_456",
            access_token="ya29.a0...",
            refresh_token="1//0g...",
            expires_in=3600,
            scope="https://www.googleapis.com/auth/gmail.send"
        )

        # Retrieve tokens (from cache or DB)
        tokens = cache.get_tokens("google", "ws_123", "user_456")
        if tokens:
            gmail_client = build('gmail', 'v1', credentials=tokens["access_token"])
    """

    def __init__(self, redis_url: Optional[str] = None, encryption_key: Optional[str] = None):
        """Initialize OAuth token cache.

        Args:
            redis_url: Redis connection URL (default from REDIS_URL env var)
            encryption_key: Fernet encryption key (default from OAUTH_ENCRYPTION_KEY env var)
        """
        self.redis_url = redis_url or os.getenv("REDIS_URL")
        self.redis_client = None
        self.backend = "db-only"  # or "db+cache"

        # Initialize Redis cache (optional)
        if self.redis_url:
            try:
                import redis

                self.redis_client = redis.from_url(self.redis_url, decode_responses=True, socket_connect_timeout=2)
                self.redis_client.ping()
                self.backend = "db+cache"
                print("[INFO] OAuth token cache: Using database + Redis cache")
            except Exception as e:
                print(f"[WARN] OAuth token cache: Redis unavailable: {e}. Using database only.")
                self.backend = "db-only"
        else:
            print("[INFO] OAuth token cache: Using database only (no Redis)")

        # Initialize encryption
        encryption_key_str = encryption_key or os.getenv("OAUTH_ENCRYPTION_KEY")
        if not encryption_key_str:
            # Generate a key for development (INSECURE - use env var in production)
            print("[WARN] OAUTH_ENCRYPTION_KEY not set. Generating ephemeral key (dev only).")
            self.cipher = Fernet(Fernet.generate_key())
        else:
            self.cipher = Fernet(encryption_key_str.encode("utf-8"))

    def store_tokens(
        self,
        provider: str,
        workspace_id: str,
        actor_id: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        expires_in: Optional[int] = None,
        scope: Optional[str] = None,
    ) -> None:
        """Store OAuth tokens with encryption and caching.

        Args:
            provider: OAuth provider ("google", "microsoft", etc.)
            workspace_id: Workspace identifier
            actor_id: User/actor identifier
            access_token: Access token to encrypt and store
            refresh_token: Refresh token to encrypt and store (optional)
            expires_in: Token lifetime in seconds (default 3600)
            scope: OAuth scopes granted (space-separated)
        """
        # Encrypt tokens
        access_token_encrypted = self.cipher.encrypt(access_token.encode("utf-8")).decode("utf-8")
        refresh_token_encrypted = None
        if refresh_token:
            refresh_token_encrypted = self.cipher.encrypt(refresh_token.encode("utf-8")).decode("utf-8")

        # Calculate expiry
        expires_in = expires_in or 3600  # Default 1 hour
        expires_at = datetime.now() + timedelta(seconds=expires_in)

        # Store in database (source of truth)
        self._store_in_db(
            provider=provider,
            workspace_id=workspace_id,
            actor_id=actor_id,
            access_token_encrypted=access_token_encrypted,
            refresh_token_encrypted=refresh_token_encrypted,
            expires_at=expires_at,
            scope=scope,
        )

        # Cache in Redis (if available)
        if self.backend == "db+cache":
            self._cache_in_redis(
                provider=provider,
                workspace_id=workspace_id,
                actor_id=actor_id,
                access_token=access_token,  # Cache decrypted for fast access
                refresh_token=refresh_token,
                expires_at=expires_at,
                scope=scope,
                ttl_seconds=expires_in,
            )

    def get_tokens(self, provider: str, workspace_id: str, actor_id: str) -> Optional[dict[str, any]]:
        """Retrieve OAuth tokens (from cache or database).

        Args:
            provider: OAuth provider ("google", "microsoft", etc.)
            workspace_id: Workspace identifier
            actor_id: User/actor identifier

        Returns:
            Dictionary with access_token, refresh_token, expires_at, scope
            or None if tokens not found or expired
        """
        # Try cache first (if available)
        if self.backend == "db+cache":
            cached = self._get_from_redis(provider, workspace_id, actor_id)
            if cached:
                return cached

        # Fall back to database
        tokens = self._get_from_db(provider, workspace_id, actor_id)

        # Warm cache if found in DB
        if tokens and self.backend == "db+cache":
            ttl_seconds = int((tokens["expires_at"] - datetime.now()).total_seconds())
            if ttl_seconds > 0:
                self._cache_in_redis(
                    provider=provider,
                    workspace_id=workspace_id,
                    actor_id=actor_id,
                    access_token=tokens["access_token"],
                    refresh_token=tokens["refresh_token"],
                    expires_at=tokens["expires_at"],
                    scope=tokens.get("scope"),
                    ttl_seconds=ttl_seconds,
                )

        return tokens

    def delete_tokens(self, provider: str, workspace_id: str, actor_id: str) -> None:
        """Delete OAuth tokens from both cache and database.

        Args:
            provider: OAuth provider
            workspace_id: Workspace identifier
            actor_id: User/actor identifier
        """
        # Delete from cache
        if self.backend == "db+cache":
            key = f"oauth:token:{provider}:{workspace_id}:{actor_id}"
            self.redis_client.delete(key)

        # Delete from database
        self._delete_from_db(provider, workspace_id, actor_id)

    def _store_in_db(
        self,
        provider: str,
        workspace_id: str,
        actor_id: str,
        access_token_encrypted: str,
        refresh_token_encrypted: Optional[str],
        expires_at: datetime,
        scope: Optional[str],
    ) -> None:
        """Store encrypted tokens in database (placeholder - implement with DB connection)."""
        # TODO: Implement database storage in Sprint 53 Phase B
        # For now, log that we would store in DB
        print(
            f"[TODO] Store in DB: provider={provider}, workspace={workspace_id}, "
            f"actor={actor_id}, expires={expires_at.isoformat()}"
        )

    def _get_from_db(self, provider: str, workspace_id: str, actor_id: str) -> Optional[dict[str, any]]:
        """Retrieve and decrypt tokens from database (placeholder)."""
        # TODO: Implement database retrieval in Sprint 53 Phase B
        print(f"[TODO] Get from DB: provider={provider}, workspace={workspace_id}, actor={actor_id}")
        return None

    def _delete_from_db(self, provider: str, workspace_id: str, actor_id: str) -> None:
        """Delete tokens from database (placeholder)."""
        # TODO: Implement database deletion in Sprint 53 Phase B
        print(f"[TODO] Delete from DB: provider={provider}, workspace={workspace_id}, actor={actor_id}")

    def _cache_in_redis(
        self,
        provider: str,
        workspace_id: str,
        actor_id: str,
        access_token: str,
        refresh_token: Optional[str],
        expires_at: datetime,
        scope: Optional[str],
        ttl_seconds: int,
    ) -> None:
        """Cache tokens in Redis with TTL."""
        key = f"oauth:token:{provider}:{workspace_id}:{actor_id}"
        value = json.dumps(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "expires_at": expires_at.isoformat(),
                "scope": scope,
            }
        )

        # Set with TTL matching token expiry
        self.redis_client.setex(key, ttl_seconds, value)

    def _get_from_redis(self, provider: str, workspace_id: str, actor_id: str) -> Optional[dict[str, any]]:
        """Retrieve tokens from Redis cache."""
        key = f"oauth:token:{provider}:{workspace_id}:{actor_id}"
        value = self.redis_client.get(key)

        if not value:
            return None

        try:
            data = json.loads(value)
            # Parse expires_at back to datetime
            data["expires_at"] = datetime.fromisoformat(data["expires_at"])
            return data
        except (json.JSONDecodeError, KeyError, ValueError):
            return None
