"""Unit tests for OAuth token refresh with Redis lock.

Sprint 53 Phase B: Test concurrent refresh, lock acquisition, metrics emission.
"""

import asyncio
import os
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.auth.oauth.tokens import OAuthTokenCache


class TestOAuthRefreshLock:
    """Test suite for OAuth token refresh with Redis lock (stampede prevention)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.original_client_id = os.environ.get("GOOGLE_CLIENT_ID")
        self.original_client_secret = os.environ.get("GOOGLE_CLIENT_SECRET")

        # Set required env vars for testing
        os.environ["GOOGLE_CLIENT_ID"] = "test-client-id"
        os.environ["GOOGLE_CLIENT_SECRET"] = "test-secret"

    def teardown_method(self):
        """Restore original environment."""
        if self.original_client_id is not None:
            os.environ["GOOGLE_CLIENT_ID"] = self.original_client_id
        elif "GOOGLE_CLIENT_ID" in os.environ:
            del os.environ["GOOGLE_CLIENT_ID"]

        if self.original_client_secret is not None:
            os.environ["GOOGLE_CLIENT_SECRET"] = self.original_client_secret
        elif "GOOGLE_CLIENT_SECRET" in os.environ:
            del os.environ["GOOGLE_CLIENT_SECRET"]

    @pytest.mark.anyio
    async def test_concurrent_refresh_only_one_performs_refresh(self):
        """Test that when multiple callers hit expired token, only one performs refresh."""
        # Create two token cache instances (simulating two concurrent requests)
        cache1 = OAuthTokenCache()
        cache2 = OAuthTokenCache()

        # Mock Redis client
        mock_redis = MagicMock()
        cache1.redis_client = mock_redis
        cache2.redis_client = mock_redis

        # Track which caller acquires lock
        lock_acquired_by = []

        def mock_set(key, value, nx=True, ex=10):
            """Mock Redis SET with NX (only set if not exists)."""
            if nx and len(lock_acquired_by) == 0:
                # First caller acquires lock
                lock_acquired_by.append("caller1")
                return True
            else:
                # Second caller fails to acquire lock
                return False

        mock_redis.set = mock_set
        mock_redis.delete = MagicMock()

        # Mock expiring token (within 120 seconds)
        expiring_tokens = {
            "access_token": "old-token",
            "refresh_token": "refresh-token",
            "expires_at": datetime.utcnow() + timedelta(seconds=60),  # Expires in 60s
            "scope": "gmail.send",
        }

        # Mock refreshed tokens
        refreshed_tokens = {
            "access_token": "new-token",
            "refresh_token": "refresh-token",
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "scope": "gmail.send",
        }

        # Mock _perform_refresh to return new tokens
        refresh_call_count = [0]

        async def mock_perform_refresh(*args):
            refresh_call_count[0] += 1
            await asyncio.sleep(0.1)  # Simulate network delay
            return refreshed_tokens

        # Mock get_tokens to return expiring tokens
        with patch.object(cache1, "get_tokens", AsyncMock(return_value=expiring_tokens)), patch.object(
            cache2, "get_tokens", AsyncMock(return_value=expiring_tokens)
        ), patch.object(cache1, "_perform_refresh", mock_perform_refresh), patch.object(
            cache2, "_perform_refresh", mock_perform_refresh
        ):
            # Execute both callers concurrently
            task1 = cache1.get_tokens_with_auto_refresh("google", "workspace-123", "user@example.com")
            task2 = cache2.get_tokens_with_auto_refresh("google", "workspace-123", "user@example.com")

            _results = await asyncio.gather(task1, task2)

            # Assert only one refresh was performed
            assert refresh_call_count[0] == 1, f"Expected 1 refresh call, got {refresh_call_count[0]}"

            # Assert lock was acquired by only one caller
            assert len(lock_acquired_by) == 1

            # Both callers should eventually get tokens (one from refresh, one from retry/cache)
            # Note: The second caller may return old tokens or raise error depending on retry logic
            # For this test, we just verify only one refresh happened

    @pytest.mark.anyio
    async def test_refresh_lock_acquisition_and_release(self):
        """Test that refresh lock is acquired and released correctly."""
        cache = OAuthTokenCache()

        mock_redis = MagicMock()
        cache.redis_client = mock_redis

        # Mock successful lock acquisition
        mock_redis.set = MagicMock(return_value=True)
        mock_redis.delete = MagicMock()

        expiring_tokens = {
            "access_token": "old-token",
            "refresh_token": "refresh-token",
            "expires_at": datetime.utcnow() + timedelta(seconds=60),
            "scope": "gmail.send",
        }

        refreshed_tokens = {
            "access_token": "new-token",
            "refresh_token": "refresh-token",
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "scope": "gmail.send",
        }

        with patch.object(cache, "get_tokens", AsyncMock(return_value=expiring_tokens)), patch.object(
            cache, "_perform_refresh", AsyncMock(return_value=refreshed_tokens)
        ):
            result = await cache.get_tokens_with_auto_refresh("google", "workspace-123", "user@example.com")

            # Assert lock was acquired with correct key and TTL
            mock_redis.set.assert_called_once()
            call_args = mock_redis.set.call_args
            assert call_args[0][0] == "oauth:refresh:workspace-123:user:google"
            assert call_args[1]["nx"] is True  # NX flag set
            assert call_args[1]["ex"] == 10  # 10 second TTL

            # Assert lock was released after refresh
            mock_redis.delete.assert_called_once_with("oauth:refresh:workspace-123:user:google")

            # Assert refreshed tokens were returned
            assert result["access_token"] == "new-token"

    @pytest.mark.anyio
    async def test_refresh_lock_contention_retry_logic(self):
        """Test that when lock is held, caller waits and retries."""
        cache = OAuthTokenCache()

        mock_redis = MagicMock()
        cache.redis_client = mock_redis

        # Simulate lock already held (set returns False)
        mock_redis.set = MagicMock(return_value=False)

        expiring_tokens = {
            "access_token": "old-token",
            "refresh_token": "refresh-token",
            "expires_at": datetime.utcnow() + timedelta(seconds=60),
            "scope": "gmail.send",
        }

        # After retries, mock get_tokens to return updated tokens (as if another process refreshed)
        refreshed_tokens = {
            "access_token": "new-token",
            "refresh_token": "refresh-token",
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "scope": "gmail.send",
        }

        call_count = [0]

        async def mock_get_tokens(*args):
            call_count[0] += 1
            if call_count[0] == 1:
                # First call returns expiring tokens
                return expiring_tokens
            else:
                # Subsequent calls return refreshed tokens (as if another process refreshed)
                return refreshed_tokens

        with patch.object(cache, "get_tokens", mock_get_tokens):
            result = await cache.get_tokens_with_auto_refresh("google", "workspace-123", "user@example.com")

            # Assert retry logic was executed (get_tokens called multiple times)
            assert call_count[0] > 1, "Expected multiple get_tokens calls during retry"

            # Assert eventually got refreshed tokens
            assert result["access_token"] == "new-token"

    @pytest.mark.anyio
    async def test_refresh_token_not_expiring_no_refresh(self):
        """Test that tokens not expiring within 120s don't trigger refresh."""
        cache = OAuthTokenCache()

        mock_redis = MagicMock()
        cache.redis_client = mock_redis

        # Token expires in 3 hours (not soon)
        valid_tokens = {
            "access_token": "current-token",
            "refresh_token": "refresh-token",
            "expires_at": datetime.utcnow() + timedelta(hours=3),
            "scope": "gmail.send",
        }

        with patch.object(cache, "get_tokens", AsyncMock(return_value=valid_tokens)):
            result = await cache.get_tokens_with_auto_refresh("google", "workspace-123", "user@example.com")

            # Assert no lock acquisition attempted
            mock_redis.set.assert_not_called()

            # Assert original tokens returned (no refresh)
            assert result["access_token"] == "current-token"

    @pytest.mark.anyio
    async def test_refresh_without_redis_still_works(self):
        """Test that refresh works even without Redis (degraded mode)."""
        cache = OAuthTokenCache()
        cache.redis_client = None  # No Redis available

        expiring_tokens = {
            "access_token": "old-token",
            "refresh_token": "refresh-token",
            "expires_at": datetime.utcnow() + timedelta(seconds=60),
            "scope": "gmail.send",
        }

        refreshed_tokens = {
            "access_token": "new-token",
            "refresh_token": "refresh-token",
            "expires_at": datetime.utcnow() + timedelta(hours=1),
            "scope": "gmail.send",
        }

        with patch.object(cache, "get_tokens", AsyncMock(return_value=expiring_tokens)), patch.object(
            cache, "_perform_refresh", AsyncMock(return_value=refreshed_tokens)
        ):
            result = await cache.get_tokens_with_auto_refresh("google", "workspace-123", "user@example.com")

            # Assert refresh still happened (without lock protection)
            assert result["access_token"] == "new-token"

    @pytest.mark.anyio
    async def test_refresh_with_no_refresh_token_returns_current_if_valid(self):
        """Test that if no refresh_token but token still valid, returns current token."""
        cache = OAuthTokenCache()

        mock_redis = MagicMock()
        cache.redis_client = mock_redis

        # Token expiring soon but no refresh_token
        tokens_no_refresh = {
            "access_token": "current-token",
            "refresh_token": None,  # No refresh token
            "expires_at": datetime.utcnow() + timedelta(seconds=60),
            "scope": "gmail.send",
        }

        with patch.object(cache, "get_tokens", AsyncMock(return_value=tokens_no_refresh)):
            result = await cache.get_tokens_with_auto_refresh("google", "workspace-123", "user@example.com")

            # Should return current token (still valid for 60s)
            assert result["access_token"] == "current-token"

            # Should not attempt to acquire lock (no refresh possible)
            mock_redis.set.assert_not_called()

    @pytest.mark.anyio
    async def test_refresh_with_expired_token_and_no_refresh_token_raises_error(self):
        """Test that if token already expired and no refresh_token, raises 401."""
        cache = OAuthTokenCache()

        # Token already expired
        expired_tokens = {
            "access_token": "expired-token",
            "refresh_token": None,
            "expires_at": datetime.utcnow() - timedelta(seconds=10),  # Expired 10s ago
            "scope": "gmail.send",
        }

        with patch.object(cache, "get_tokens", AsyncMock(return_value=expired_tokens)):
            with pytest.raises(ValueError) as exc_info:  # Should raise ValueError
                await cache.get_tokens_with_auto_refresh("google", "workspace-123", "user@example.com")

            error_msg = str(exc_info.value).lower()
            assert "token expired" in error_msg or "no refresh token" in error_msg

    @pytest.mark.anyio
    async def test_perform_refresh_calls_google_endpoint(self):
        """Test that _perform_refresh calls Google's token endpoint correctly."""
        cache = OAuthTokenCache()

        # Mock successful Google token refresh response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new-access-token",
            "expires_in": 3600,
            "scope": "https://www.googleapis.com/auth/gmail.send"
            # Note: refresh_token may not be returned (Google reuses existing)
        }

        with patch("httpx.AsyncClient") as MockAsyncClient, patch.object(cache, "store_tokens", AsyncMock()):
            mock_client_instance = MockAsyncClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            result = await cache._perform_refresh("google", "workspace-123", "user@example.com", "old-refresh-token")

            # Assert Google token endpoint was called
            mock_client_instance.post.assert_called_once()
            call_args = mock_client_instance.post.call_args
            assert "https://oauth2.googleapis.com/token" in call_args[0][0]

            # Assert refresh_token was included in request
            token_data = call_args[1]["data"]
            assert token_data["grant_type"] == "refresh_token"
            assert token_data["refresh_token"] == "old-refresh-token"
            assert token_data["client_id"] == "test-client-id"
            assert token_data["client_secret"] == "test-secret"

            # Assert new tokens were returned
            assert result["access_token"] == "new-access-token"

    @pytest.mark.anyio
    async def test_perform_refresh_handles_google_error(self):
        """Test that _perform_refresh handles Google API errors correctly."""
        cache = OAuthTokenCache()

        # Mock failed Google response (e.g., invalid refresh token)
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.text = "invalid_grant: Token has been expired or revoked"

        with patch("httpx.AsyncClient") as MockAsyncClient:
            mock_client_instance = MockAsyncClient.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(return_value=mock_response)

            with pytest.raises(ValueError):  # Should raise ValueError
                await cache._perform_refresh("google", "workspace-123", "user@example.com", "invalid-token")

    @pytest.mark.anyio
    async def test_refresh_lock_key_format(self):
        """Test that Redis lock key follows correct format."""
        cache = OAuthTokenCache()

        mock_redis = MagicMock()
        cache.redis_client = mock_redis
        mock_redis.set = MagicMock(return_value=True)
        mock_redis.delete = MagicMock()

        expiring_tokens = {
            "access_token": "old-token",
            "refresh_token": "refresh-token",
            "expires_at": datetime.utcnow() + timedelta(seconds=60),
            "scope": "gmail.send",
        }

        refreshed_tokens = {"access_token": "new-token", "expires_at": datetime.utcnow() + timedelta(hours=1)}

        with patch.object(cache, "get_tokens", AsyncMock(return_value=expiring_tokens)), patch.object(
            cache, "_perform_refresh", AsyncMock(return_value=refreshed_tokens)
        ):
            await cache.get_tokens_with_auto_refresh("google", "workspace-abc-123", "user@example.com")

            # Verify lock key format: oauth:refresh:{workspace_id}:user:{provider}
            lock_key = mock_redis.set.call_args[0][0]
            assert lock_key == "oauth:refresh:workspace-abc-123:user:google"
