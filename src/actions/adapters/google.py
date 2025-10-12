"""Google action adapter (Gmail Send).

Sprint 53 Phase B: Gmail send action with OAuth token refresh.
"""

import base64
import hashlib
import os
import re
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import Any, Optional

import httpx
from pydantic import BaseModel, Field, ValidationError, field_validator

from ..contracts import ActionDefinition, Provider

# Simple email regex (RFC 5322 simplified)
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


class GmailSendParams(BaseModel):
    """Parameters for gmail.send action."""

    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    text: str = Field(..., description="Email body (plain text)")
    cc: Optional[list[str]] = Field(None, description="CC recipients")
    bcc: Optional[list[str]] = Field(None, description="BCC recipients")

    @field_validator("to")
    @classmethod
    def validate_to_email(cls, v: str) -> str:
        if not EMAIL_REGEX.match(v):
            raise ValueError(f"Invalid email address: {v}")
        return v

    @field_validator("cc", "bcc")
    @classmethod
    def validate_email_list(cls, v: Optional[list[str]]) -> Optional[list[str]]:
        if v is not None:
            for email in v:
                if not EMAIL_REGEX.match(email):
                    raise ValueError(f"Invalid email address in list: {email}")
        return v


class GoogleAdapter:
    """Adapter for Google actions (Gmail)."""

    def __init__(self, rollout_gate=None):
        """Initialize Google adapter.

        Args:
            rollout_gate: Optional RolloutGate for gradual feature rollout
        """
        self.enabled = os.getenv("PROVIDER_GOOGLE_ENABLED", "false").lower() == "true"
        self.client_id = os.getenv("GOOGLE_CLIENT_ID")
        self.client_secret = os.getenv("GOOGLE_CLIENT_SECRET")
        self.rollout_gate = rollout_gate

    def list_actions(self) -> list[ActionDefinition]:
        """List available Google actions."""
        actions = [
            ActionDefinition(
                id="gmail.send",
                name="Send Gmail",
                description="Send an email via Gmail API",
                provider=Provider.GOOGLE,
                schema={
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "format": "email",
                            "description": "Recipient email address",
                        },
                        "subject": {
                            "type": "string",
                            "description": "Email subject",
                        },
                        "text": {
                            "type": "string",
                            "description": "Email body (plain text)",
                        },
                        "cc": {
                            "type": "array",
                            "items": {"type": "string", "format": "email"},
                            "description": "CC recipients",
                        },
                        "bcc": {
                            "type": "array",
                            "items": {"type": "string", "format": "email"},
                            "description": "BCC recipients",
                        },
                    },
                    "required": ["to", "subject", "text"],
                },
                enabled=self.enabled,
            )
        ]

        return actions

    def preview(self, action: str, params: dict[str, Any]) -> dict[str, Any]:
        """Preview a Google action.

        Validates parameters, builds MIME message, and returns digest.
        No network side effects.
        """
        if action == "gmail.send":
            return self._preview_gmail_send(params)

        raise ValueError(f"Unknown action: {action}")

    def _preview_gmail_send(self, params: dict[str, Any]) -> dict[str, Any]:
        """Preview gmail.send action."""
        # Validate with Pydantic
        try:
            validated = GmailSendParams(**params)
        except ValidationError as e:
            raise ValueError(f"Validation error: {e}") from e

        # Build MIME message
        mime_message = self._build_mime_message(
            to=validated.to,
            subject=validated.subject,
            text=validated.text,
            cc=validated.cc,
            bcc=validated.bcc,
        )

        # Base64URL encode (no padding)
        raw_message = base64.urlsafe_b64encode(mime_message.encode("utf-8"))
        raw_message = raw_message.rstrip(b"=")  # Remove padding

        # Compute digest (SHA256 of headers + subject + first 64 chars of body)
        digest_input = f"{validated.to}|{validated.subject}|{validated.text[:64]}"
        digest = hashlib.sha256(digest_input.encode("utf-8")).hexdigest()[:16]

        # Build summary
        summary = f"Send email to {validated.to}\nSubject: {validated.subject}\nBody: {validated.text[:100]}..."
        if validated.cc:
            summary += f"\nCC: {', '.join(validated.cc)}"
        if validated.bcc:
            summary += f"\nBCC: {', '.join(validated.bcc)}"

        warnings = []
        if not self.enabled:
            warnings.append("PROVIDER_GOOGLE_ENABLED is false - execution will fail")
        if not self.client_id or not self.client_secret:
            warnings.append("Google OAuth credentials not configured")

        return {
            "summary": summary,
            "params": params,
            "warnings": warnings,
            "digest": digest,
            "raw_message_length": len(raw_message),
        }

    def _build_mime_message(
        self,
        to: str,
        subject: str,
        text: str,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
    ) -> str:
        """Build RFC822 MIME message."""
        message = MIMEMultipart()
        message["To"] = to
        message["Subject"] = subject

        if cc:
            message["Cc"] = ", ".join(cc)
        if bcc:
            message["Bcc"] = ", ".join(bcc)

        # Attach plain text body
        message.attach(MIMEText(text, "plain"))

        # Return as string
        return message.as_string()

    async def execute(self, action: str, params: dict[str, Any], workspace_id: str, actor_id: str) -> dict[str, Any]:
        """Execute a Google action.

        Args:
            action: Action ID (e.g., 'gmail.send')
            params: Validated parameters from preview
            workspace_id: Workspace UUID
            actor_id: Actor ID (user email or API key ID)

        Returns:
            Execution result with status and response data

        Raises:
            ValueError: If action is unknown or validation fails
            httpx.HTTPStatusError: If Gmail API returns error
        """
        if action == "gmail.send":
            return await self._execute_gmail_send(params, workspace_id, actor_id)

        raise ValueError(f"Unknown action: {action}")

    async def _execute_gmail_send(self, params: dict[str, Any], workspace_id: str, actor_id: str) -> dict[str, Any]:
        """Execute gmail.send action.

        Bounded error reasons:
        - provider_disabled: PROVIDER_GOOGLE_ENABLED=false
        - rollout_gated: Feature not rolled out to this user
        - oauth_token_missing: No tokens found for workspace
        - oauth_token_expired: Token refresh failed
        - gmail_4xx: Client error (400-499)
        - gmail_5xx: Server error (500-599)
        - validation_error: Invalid parameters
        """
        from src.telemetry.prom import record_action_error, record_action_execution

        start_time = time.perf_counter()

        # Guard: Check feature flag
        if not self.enabled:
            record_action_error(provider="google", action="gmail.send", reason="provider_disabled")
            raise ValueError("Google provider is disabled (PROVIDER_GOOGLE_ENABLED=false)")

        # Guard: Check rollout gate
        if self.rollout_gate is not None:
            context = {"actor_id": actor_id, "workspace_id": workspace_id}
            if not self.rollout_gate.allow("google", context):
                record_action_error(provider="google", action="gmail.send", reason="rollout_gated")
                raise ValueError("Gmail send not rolled out to this user (rollout gate)")

        # Validate parameters
        try:
            validated = GmailSendParams(**params)
        except ValidationError as e:
            record_action_error(provider="google", action="gmail.send", reason="validation_error")
            raise ValueError(f"Validation error: {e}") from e

        # Fetch OAuth tokens (with auto-refresh)
        from src.auth.oauth.tokens import OAuthTokenCache

        token_cache = OAuthTokenCache()
        try:
            tokens = await token_cache.get_tokens_with_auto_refresh(
                provider="google", workspace_id=workspace_id, actor_id=actor_id
            )
        except Exception as e:
            record_action_error(provider="google", action="gmail.send", reason="oauth_token_missing")
            raise ValueError(f"OAuth token error: {e}") from e

        if not tokens:
            record_action_error(provider="google", action="gmail.send", reason="oauth_token_missing")
            raise ValueError("No OAuth tokens found for workspace")

        access_token = tokens.get("access_token")
        if not access_token:
            record_action_error(provider="google", action="gmail.send", reason="oauth_token_missing")
            raise ValueError("Access token missing from token cache")

        # Build MIME message
        mime_message = self._build_mime_message(
            to=validated.to,
            subject=validated.subject,
            text=validated.text,
            cc=validated.cc,
            bcc=validated.bcc,
        )

        # Base64URL encode (no padding)
        raw_message = base64.urlsafe_b64encode(mime_message.encode("utf-8"))
        raw_message = raw_message.rstrip(b"=")  # Remove padding

        # Call Gmail API
        gmail_url = "https://gmail.googleapis.com/gmail/v1/users/me/messages/send"
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        payload = {"raw": raw_message.decode("utf-8")}

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(gmail_url, json=payload, headers=headers)

                # Handle errors
                if 400 <= response.status_code < 500:
                    error_detail = response.text[:200]
                    record_action_error(provider="google", action="gmail.send", reason="gmail_4xx")

                    # Record execution (failed)
                    duration = time.perf_counter() - start_time
                    record_action_execution(
                        provider="google", action="gmail.send", status="error", duration_seconds=duration
                    )

                    raise httpx.HTTPStatusError(
                        f"Gmail API client error {response.status_code}: {error_detail}",
                        request=response.request,
                        response=response,
                    )

                if 500 <= response.status_code < 600:
                    error_detail = response.text[:200]
                    record_action_error(provider="google", action="gmail.send", reason="gmail_5xx")

                    # Record execution (failed)
                    duration = time.perf_counter() - start_time
                    record_action_execution(
                        provider="google", action="gmail.send", status="error", duration_seconds=duration
                    )

                    raise httpx.HTTPStatusError(
                        f"Gmail API server error {response.status_code}: {error_detail}",
                        request=response.request,
                        response=response,
                    )

                # Success
                response_data = response.json()

                # Record metrics
                duration = time.perf_counter() - start_time
                record_action_execution(provider="google", action="gmail.send", status="ok", duration_seconds=duration)

                return {
                    "status": "sent",
                    "message_id": response_data.get("id"),
                    "thread_id": response_data.get("threadId"),
                    "to": validated.to,
                    "subject": validated.subject,
                }

        except httpx.TimeoutException as e:
            record_action_error(provider="google", action="gmail.send", reason="gmail_timeout")

            # Record execution (failed)
            duration = time.perf_counter() - start_time
            record_action_execution(provider="google", action="gmail.send", status="error", duration_seconds=duration)

            raise TimeoutError("Gmail API request timed out after 30s") from e

        except httpx.NetworkError as e:
            record_action_error(provider="google", action="gmail.send", reason="gmail_network_error")

            # Record execution (failed)
            duration = time.perf_counter() - start_time
            record_action_execution(provider="google", action="gmail.send", status="error", duration_seconds=duration)

            raise ConnectionError("Network error connecting to Gmail API") from e
