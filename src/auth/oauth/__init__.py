"""OAuth 2.0 authentication and authorization for Actions API.

Sprint 53: Provider vertical slice (Google OAuth flow).
"""

from .state import OAuthStateManager

__all__ = ["OAuthStateManager"]
