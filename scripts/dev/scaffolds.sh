#!/usr/bin/env bash
# Sprint 54 Phase C: Scaffolds Generator
# Creates placeholder modules and test skeletons (NO LOGIC, NO OVERWRITE)
#
# Usage:
#   bash scripts/dev/scaffolds.sh
#
# Safety:
#   - Will NOT overwrite existing files
#   - Generates TODOs and type stubs only
#   - Idempotent: safe to run multiple times

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

cd "$PROJECT_ROOT"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

log_skip() {
    echo -e "${YELLOW}[SKIP]${NC} $1"
}

# Check if file exists before creating
create_file_if_not_exists() {
    local file_path="$1"
    local content="$2"

    if [ -f "$file_path" ]; then
        log_skip "File already exists: $file_path"
        return 1
    fi

    # Create parent directory if needed
    mkdir -p "$(dirname "$file_path")"

    echo "$content" > "$file_path"
    log_success "Created: $file_path"
    return 0
}

echo "========================================"
echo "Sprint 54 Phase C: Scaffolds Generator"
echo "========================================"
echo ""

# =======================
# 1. MIME Builder Module
# =======================
log_info "Generating MIME builder module..."

MIME_BUILDER_CONTENT='"""Gmail MIME message builder.

Sprint 54 Phase C: Rich email support (HTML, attachments, inline CIDs).

This module provides utilities for constructing RFC 822 MIME messages
compatible with Gmail API'\''s base64url-encoded raw message format.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MimeStructure(str, Enum):
    """MIME multipart structure types."""
    TEXT = "text/plain"
    HTML = "text/html"
    MIXED = "multipart/mixed"  # Text + attachments
    ALTERNATIVE = "multipart/alternative"  # Text + HTML
    RELATED = "multipart/related"  # HTML + inline images


@dataclass
class AttachmentSpec:
    """Specification for an email attachment.

    Attributes:
        content: Raw bytes of the attachment
        filename: Suggested filename (e.g., "report.pdf")
        content_type: MIME type (e.g., "application/pdf")
        disposition: "attachment" or "inline"
        content_id: Optional CID for inline references (e.g., "image1")
    """
    content: bytes
    filename: str
    content_type: str
    disposition: str = "attachment"
    content_id: Optional[str] = None


@dataclass
class MimeMessage:
    """Constructed MIME message ready for Gmail API.

    Attributes:
        raw: Base64url-encoded raw message (no padding)
        size_bytes: Total message size in bytes
        structure: MIME structure type used
    """
    raw: str
    size_bytes: int
    structure: MimeStructure


class MimeBuilder:
    """Builds RFC 822 MIME messages for Gmail API.

    TODO (Sprint 54):
    - [ ] Implement build_simple_text()
    - [ ] Implement build_html_alternative()
    - [ ] Implement build_with_attachments()
    - [ ] Implement build_with_inline_images()
    - [ ] Add support for CC/BCC headers
    - [ ] Handle Unicode characters in headers (RFC 2047)
    - [ ] Validate Content-ID uniqueness
    - [ ] Add telemetry (gmail_mime_build_seconds)
    """

    def build_simple_text(
        self,
        to: str,
        subject: str,
        body: str,
        from_email: Optional[str] = None,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
    ) -> MimeMessage:
        """Build a simple text/plain message.

        Args:
            to: Recipient email address
            subject: Email subject line
            body: Plain text body
            from_email: Sender email (optional, Gmail API may set automatically)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)

        Returns:
            MimeMessage with base64url-encoded raw field

        Raises:
            ValueError: If to/subject/body are empty
        """
        raise NotImplementedError("TODO: Sprint 54 Phase C")

    def build_html_alternative(
        self,
        to: str,
        subject: str,
        text_body: str,
        html_body: str,
        from_email: Optional[str] = None,
        cc: Optional[list[str]] = None,
        bcc: Optional[list[str]] = None,
    ) -> MimeMessage:
        """Build a multipart/alternative message (text + HTML).

        Args:
            to: Recipient email address
            subject: Email subject line
            text_body: Plain text fallback body
            html_body: HTML body (should be pre-sanitized)
            from_email: Sender email (optional)
            cc: CC recipients (optional)
            bcc: BCC recipients (optional)

        Returns:
            MimeMessage with multipart/alternative structure

        Raises:
            ValueError: If html_body is empty

        Note:
            - HTML body MUST be sanitized before calling this method
            - Text body is used as fallback for clients that don'\''t support HTML
        """
        raise NotImplementedError("TODO: Sprint 54 Phase C")

    def build_with_attachments(
        self,
        to: str,
        subject: str,
        body: str,
        attachments: list[AttachmentSpec],
        html_body: Optional[str] = None,
        from_email: Optional[str] = None,
    ) -> MimeMessage:
        """Build a multipart/mixed message with attachments.

        Args:
            to: Recipient email address
            subject: Email subject line
            body: Plain text body
            attachments: List of attachment specifications
            html_body: Optional HTML body (creates multipart/alternative)
            from_email: Sender email (optional)

        Returns:
            MimeMessage with multipart/mixed structure

        Raises:
            ValueError: If attachments list is empty
            ValueError: If total payload size exceeds Gmail limit (35MB)

        Note:
            - Attachments are base64-encoded in the MIME message
            - Content-Disposition header set to "attachment" for each file
        """
        raise NotImplementedError("TODO: Sprint 54 Phase C")

    def build_with_inline_images(
        self,
        to: str,
        subject: str,
        html_body: str,
        inline_attachments: list[AttachmentSpec],
        text_body: Optional[str] = None,
        from_email: Optional[str] = None,
    ) -> MimeMessage:
        """Build a multipart/related message with inline images.

        Args:
            to: Recipient email address
            subject: Email subject line
            html_body: HTML body with cid: references (pre-sanitized)
            inline_attachments: List of inline attachment specs with content_id
            text_body: Optional plain text fallback
            from_email: Sender email (optional)

        Returns:
            MimeMessage with multipart/related structure

        Raises:
            ValueError: If html_body has no cid: references
            ValueError: If inline_attachments missing content_id field
            ValueError: If orphan CIDs detected (HTML refs without attachment)

        Note:
            - content_id in AttachmentSpec must match cid: refs in HTML
            - Example: AttachmentSpec(content_id="logo") matches <img src="cid:logo">
            - Content-Disposition header set to "inline" for each image
        """
        raise NotImplementedError("TODO: Sprint 54 Phase C")


def encode_base64url(data: bytes) -> str:
    """Encode bytes to base64url format (RFC 4648 Section 5).

    Gmail API requires base64url encoding WITHOUT padding (no trailing =).

    Args:
        data: Raw bytes to encode

    Returns:
        Base64url-encoded string with no padding

    Example:
        >>> encode_base64url(b"hello")
        "aGVsbG8"
    """
    raise NotImplementedError("TODO: Sprint 54 Phase C")


def validate_content_ids(html_body: str, attachments: list[AttachmentSpec]) -> list[str]:
    """Validate inline Content-ID references match attachments.

    Args:
        html_body: HTML content with cid: references
        attachments: List of inline attachments with content_id set

    Returns:
        List of orphan CIDs (HTML references without matching attachment)

    Example:
        >>> html = '\''<img src="cid:logo"> <img src="cid:photo">'\''
        >>> attachments = [AttachmentSpec(content_id="logo", ...)]
        >>> validate_content_ids(html, attachments)
        ['\''photo'\'']  # Orphan: referenced in HTML but no attachment
    """
    raise NotImplementedError("TODO: Sprint 54 Phase C")
'

create_file_if_not_exists "src/actions/adapters/google_mime.py" "$MIME_BUILDER_CONTENT"

# ==========================
# 2. Attachment Validation
# ==========================
log_info "Generating attachment validation module..."

ATTACHMENT_VALIDATION_CONTENT='"""Attachment validation for Gmail rich email.

Sprint 54 Phase C: Validates attachment size, count, MIME types, and content.
"""

from enum import Enum


class AttachmentValidationError(str, Enum):
    """Bounded error reasons for attachment validation failures."""
    ATTACHMENT_TOO_LARGE = "attachment_too_large"
    ATTACHMENT_COUNT_EXCEEDED = "attachment_count_exceeded"
    ATTACHMENT_TYPE_BLOCKED = "attachment_type_blocked"
    INLINE_TOO_LARGE = "inline_too_large"
    INLINE_COUNT_EXCEEDED = "inline_count_exceeded"
    TOTAL_PAYLOAD_TOO_LARGE = "total_payload_too_large"
    FILENAME_INVALID = "filename_invalid"


# Attachment size limits (Gmail API constraints)
MAX_ATTACHMENT_SIZE_BYTES = 25 * 1024 * 1024  # 25 MB per attachment
MAX_INLINE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB per inline image
MAX_TOTAL_PAYLOAD_BYTES = 35 * 1024 * 1024  # 35 MB total message size

# Attachment count limits
MAX_ATTACHMENT_COUNT = 10  # Regular attachments
MAX_INLINE_COUNT = 20  # Inline images (higher limit for rich HTML)

# MIME type allowlist (common safe types)
ALLOWED_MIME_TYPES = {
    # Documents
    "application/pdf",
    "application/msword",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/vnd.ms-excel",
    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "application/vnd.ms-powerpoint",
    "application/vnd.openxmlformats-officedocument.presentationml.presentation",

    # Images
    "image/png",
    "image/jpeg",
    "image/gif",
    "image/webp",
    "image/svg+xml",

    # Text
    "text/plain",
    "text/csv",
    "text/html",

    # Archives (use with caution)
    "application/zip",
    "application/x-tar",
    "application/gzip",
}

# MIME type blocklist (executable/dangerous types)
BLOCKED_MIME_TYPES = {
    "application/x-executable",
    "application/x-msdownload",
    "application/x-sh",
    "application/x-bat",
    "application/x-dosexec",
    "application/vnd.microsoft.portable-executable",
}

# Filename extension blocklist
BLOCKED_EXTENSIONS = {
    ".exe", ".dll", ".bat", ".cmd", ".sh", ".bash",
    ".ps1", ".vbs", ".js", ".jar", ".app", ".deb", ".rpm",
}


def validate_attachment_size(size_bytes: int, is_inline: bool = False) -> None:
    """Validate attachment size against limits.

    Args:
        size_bytes: Size of the attachment in bytes
        is_inline: True if this is an inline image, False for regular attachment

    Raises:
        ValueError: If size exceeds limit (includes AttachmentValidationError reason)

    TODO (Sprint 54):
    - [ ] Implement size validation
    - [ ] Add telemetry counter (gmail_validation_errors_total)
    """
    raise NotImplementedError("TODO: Sprint 54 Phase C")


def validate_attachment_count(count: int, is_inline: bool = False) -> None:
    """Validate attachment count against limits.

    Args:
        count: Number of attachments
        is_inline: True for inline images, False for regular attachments

    Raises:
        ValueError: If count exceeds limit (includes AttachmentValidationError reason)

    TODO (Sprint 54):
    - [ ] Implement count validation
    - [ ] Add telemetry counter
    """
    raise NotImplementedError("TODO: Sprint 54 Phase C")


def validate_mime_type(mime_type: str) -> None:
    """Validate MIME type against allowlist and blocklist.

    Args:
        mime_type: MIME type string (e.g., "application/pdf")

    Raises:
        ValueError: If MIME type is blocked or not in allowlist

    TODO (Sprint 54):
    - [ ] Implement allowlist/blocklist check
    - [ ] Add telemetry counter
    - [ ] Log blocked MIME types (never log actual content)
    """
    raise NotImplementedError("TODO: Sprint 54 Phase C")


def validate_filename(filename: str) -> None:
    """Validate filename for dangerous extensions.

    Args:
        filename: Attachment filename (e.g., "report.pdf")

    Raises:
        ValueError: If filename has blocked extension (includes error reason)

    TODO (Sprint 54):
    - [ ] Implement extension blocklist check
    - [ ] Add telemetry counter
    - [ ] Log SHA256(filename) only, never actual filename
    """
    raise NotImplementedError("TODO: Sprint 54 Phase C")


def validate_total_payload_size(attachments: list, inline: list, html_body: str = "") -> None:
    """Validate total payload size (attachments + inline + HTML).

    Args:
        attachments: List of attachment specs with size_bytes field
        inline: List of inline attachment specs with size_bytes field
        html_body: HTML body content (if present)

    Raises:
        ValueError: If total payload exceeds Gmail limit (35 MB)

    TODO (Sprint 54):
    - [ ] Sum up all sizes (attachments + inline + HTML + headers overhead)
    - [ ] Add 10% buffer for MIME encoding overhead
    - [ ] Add telemetry counter
    """
    raise NotImplementedError("TODO: Sprint 54 Phase C")
'

create_file_if_not_exists "src/actions/validation/attachments.py" "$ATTACHMENT_VALIDATION_CONTENT"

# =======================
# 3. HTML Sanitization
# =======================
log_info "Generating HTML sanitization module..."

HTML_SANITIZATION_CONTENT='"""HTML sanitization for Gmail rich email.

Sprint 54 Phase C: Allowlist-based HTML sanitization to prevent XSS.
Uses bleach library with strict tag/attribute policies.
"""

from typing import Optional


# Allowed HTML tags (safe subset)
ALLOWED_TAGS = {
    # Text formatting
    "p", "br", "span", "div", "strong", "em", "b", "i", "u", "s", "strike",
    "h1", "h2", "h3", "h4", "h5", "h6",

    # Lists
    "ul", "ol", "li",

    # Links & images
    "a", "img",

    # Tables
    "table", "thead", "tbody", "tr", "th", "td",

    # Quotes & code
    "blockquote", "pre", "code",
}

# Blocked HTML tags (XSS vectors)
BLOCKED_TAGS = {
    "script", "iframe", "object", "embed", "applet",
    "form", "input", "button", "textarea", "select",
    "meta", "link", "style", "base",
}

# Allowed attributes per tag
ALLOWED_ATTRIBUTES = {
    "*": ["class", "id"],  # Global attributes
    "a": ["href", "title", "target"],
    "img": ["src", "alt", "title", "width", "height"],
    "table": ["border", "cellpadding", "cellspacing"],
    "td": ["colspan", "rowspan", "align", "valign"],
    "th": ["colspan", "rowspan", "align", "valign"],
}

# Allowed URL schemes (for href/src attributes)
ALLOWED_PROTOCOLS = {"http", "https", "mailto", "cid"}

# Allowed CSS properties (for style attribute, if enabled)
ALLOWED_CSS_PROPERTIES = {
    "color", "background-color", "font-size", "font-family",
    "text-align", "padding", "margin", "border",
}


def sanitize_html(html_body: str, strip_comments: bool = True) -> tuple[str, dict]:
    """Sanitize HTML using allowlist-based approach.

    Args:
        html_body: Raw HTML content from user
        strip_comments: If True, remove HTML comments

    Returns:
        Tuple of (sanitized_html, stats) where stats contains:
        - tags_removed: Count of blocked tags removed
        - attributes_removed: Count of disallowed attributes removed
        - css_blocked: Count of CSS properties blocked

    Raises:
        ValueError: If html_body is empty or invalid encoding

    TODO (Sprint 54):
    - [ ] Implement bleach.clean() with ALLOWED_TAGS/ALLOWED_ATTRIBUTES
    - [ ] Track removals for telemetry (gmail_html_sanitization_changes_total)
    - [ ] Log SHA256(html_body) ONLY, never raw HTML (privacy policy)
    - [ ] Add duration metric (gmail_html_sanitization_seconds)

    Example:
        >>> html = '\''<p>Hello</p><script>alert("XSS")</script>'\''
        >>> clean, stats = sanitize_html(html)
        >>> clean
        '\''<p>Hello</p>'\''
        >>> stats
        {'\''tags_removed'\'': 1, '\''attributes_removed'\'': 0, '\''css_blocked'\'': 0}
    """
    raise NotImplementedError("TODO: Sprint 54 Phase C")


def validate_html_size(html_body: str, max_size_bytes: int = 5 * 1024 * 1024) -> None:
    """Validate HTML body size.

    Args:
        html_body: HTML content
        max_size_bytes: Maximum allowed size (default 5 MB)

    Raises:
        ValueError: If HTML exceeds max_size_bytes

    TODO (Sprint 54):
    - [ ] Check len(html_body.encode("utf-8"))
    - [ ] Add telemetry counter (gmail_validation_errors_total{reason="html_too_large"})
    """
    raise NotImplementedError("TODO: Sprint 54 Phase C")


def validate_html_encoding(html_body: str) -> None:
    """Validate HTML is valid UTF-8.

    Args:
        html_body: HTML content

    Raises:
        ValueError: If HTML is not valid UTF-8 (includes error reason)

    TODO (Sprint 54):
    - [ ] Try encoding to UTF-8 and catch UnicodeEncodeError
    - [ ] Add telemetry counter
    """
    raise NotImplementedError("TODO: Sprint 54 Phase C")
'

create_file_if_not_exists "src/actions/validation/html_sanitization.py" "$HTML_SANITIZATION_CONTENT"

# ========================
# 4. Gmail Adapter Extension
# ========================
log_info "Checking existing Gmail adapter..."

if [ -f "src/actions/adapters/google.py" ]; then
    log_skip "Gmail adapter exists: src/actions/adapters/google.py (will extend in Sprint 54)"
    echo "       TODO: Add html, attachments[], inline[] parameters to preview/execute"
else
    log_info "Gmail adapter not found (expected for new projects)"
fi

# ====================
# 5. Test Skeletons
# ====================
log_info "Generating test skeleton files..."

# MIME Builder Tests
MIME_TEST_CONTENT='"""Unit tests for Gmail MIME builder.

Sprint 54 Phase C: Test multipart MIME message construction.
"""

import pytest
from src.actions.adapters.google_mime import (
    MimeBuilder, AttachmentSpec, MimeStructure,
    encode_base64url, validate_content_ids
)


class TestMimeBuilderSimpleText:
    """Test simple text/plain message construction."""

    @pytest.mark.anyio
    async def test_build_simple_text_minimal(self):
        """TODO: Test minimal text message (to, subject, body only)."""
        pytest.skip("Sprint 54 Phase C implementation")

    @pytest.mark.anyio
    async def test_build_simple_text_with_cc_bcc(self):
        """TODO: Test text message with CC/BCC headers."""
        pytest.skip("Sprint 54 Phase C implementation")


class TestMimeBuilderHTMLAlternative:
    """Test multipart/alternative (text + HTML) messages."""

    @pytest.mark.anyio
    async def test_build_html_alternative_basic(self):
        """TODO: Test HTML message with text fallback."""
        pytest.skip("Sprint 54 Phase C implementation")


class TestMimeBuilderAttachments:
    """Test multipart/mixed with attachments."""

    @pytest.mark.anyio
    async def test_build_with_single_attachment(self):
        """TODO: Test message with 1 PDF attachment."""
        pytest.skip("Sprint 54 Phase C implementation")


class TestMimeBuilderInlineImages:
    """Test multipart/related with inline CIDs."""

    @pytest.mark.anyio
    async def test_build_with_inline_image(self):
        """TODO: Test HTML with inline image (cid: reference)."""
        pytest.skip("Sprint 54 Phase C implementation")


class TestBase64URLEncoding:
    """Test base64url encoding (no padding)."""

    def test_encode_base64url_no_padding(self):
        """TODO: Verify no trailing = padding."""
        pytest.skip("Sprint 54 Phase C implementation")


class TestContentIDValidation:
    """Test inline CID orphan detection."""

    def test_validate_content_ids_no_orphans(self):
        """TODO: Verify all cid: refs match attachments."""
        pytest.skip("Sprint 54 Phase C implementation")

    def test_validate_content_ids_orphan_detected(self):
        """TODO: Detect orphan CID (HTML ref without attachment)."""
        pytest.skip("Sprint 54 Phase C implementation")
'

create_file_if_not_exists "tests/actions/test_google_mime_unit.py" "$MIME_TEST_CONTENT"

# HTML Sanitization Tests
HTML_TEST_CONTENT='"""Unit tests for HTML sanitization.

Sprint 54 Phase C: Test allowlist-based HTML cleaning.
"""

import pytest
from src.actions.validation.html_sanitization import (
    sanitize_html, validate_html_size, validate_html_encoding,
    ALLOWED_TAGS, BLOCKED_TAGS
)


class TestHTMLSanitization:
    """Test HTML sanitization with bleach."""

    def test_sanitize_removes_script_tags(self):
        """TODO: Verify <script> tags are removed."""
        pytest.skip("Sprint 54 Phase C implementation")

    def test_sanitize_removes_dangerous_attributes(self):
        """TODO: Verify onclick/onerror attributes removed."""
        pytest.skip("Sprint 54 Phase C implementation")

    def test_sanitize_allows_safe_tags(self):
        """TODO: Verify <p>, <strong>, <a> tags preserved."""
        pytest.skip("Sprint 54 Phase C implementation")


class TestHTMLValidation:
    """Test HTML size and encoding validation."""

    def test_validate_html_size_within_limit(self):
        """TODO: Accept HTML under 5 MB."""
        pytest.skip("Sprint 54 Phase C implementation")

    def test_validate_html_size_exceeds_limit(self):
        """TODO: Reject HTML over 5 MB."""
        pytest.skip("Sprint 54 Phase C implementation")
'

create_file_if_not_exists "tests/actions/test_html_sanitization_unit.py" "$HTML_TEST_CONTENT"

# Attachment Validation Tests
ATTACHMENT_TEST_CONTENT='"""Unit tests for attachment validation.

Sprint 54 Phase C: Test attachment size, count, MIME type checks.
"""

import pytest
from src.actions.validation.attachments import (
    validate_attachment_size, validate_attachment_count,
    validate_mime_type, validate_filename,
    MAX_ATTACHMENT_SIZE_BYTES, BLOCKED_EXTENSIONS
)


class TestAttachmentSizeValidation:
    """Test attachment size limits."""

    def test_validate_size_within_limit(self):
        """TODO: Accept attachment under 25 MB."""
        pytest.skip("Sprint 54 Phase C implementation")

    def test_validate_size_exceeds_limit(self):
        """TODO: Reject attachment over 25 MB."""
        pytest.skip("Sprint 54 Phase C implementation")


class TestMIMETypeValidation:
    """Test MIME type allowlist/blocklist."""

    def test_validate_mime_type_pdf_allowed(self):
        """TODO: Accept application/pdf."""
        pytest.skip("Sprint 54 Phase C implementation")

    def test_validate_mime_type_executable_blocked(self):
        """TODO: Reject application/x-executable."""
        pytest.skip("Sprint 54 Phase C implementation")


class TestFilenameValidation:
    """Test filename extension blocklist."""

    def test_validate_filename_exe_blocked(self):
        """TODO: Reject .exe extension."""
        pytest.skip("Sprint 54 Phase C implementation")
'

create_file_if_not_exists "tests/actions/test_attachment_validation_unit.py" "$ATTACHMENT_TEST_CONTENT"

echo ""
echo "========================================"
echo "Scaffolds Generation Complete"
echo "========================================"
echo ""
echo "✓ Created 3 new modules with type stubs and TODOs:"
echo "  - src/actions/adapters/google_mime.py"
echo "  - src/actions/validation/attachments.py"
echo "  - src/actions/validation/html_sanitization.py"
echo ""
echo "✓ Created 3 test skeleton files:"
echo "  - tests/actions/test_google_mime_unit.py"
echo "  - tests/actions/test_html_sanitization_unit.py"
echo "  - tests/actions/test_attachment_validation_unit.py"
echo ""
echo "Next Steps:"
echo "==========="
echo "1. Review Sprint 54 plan: docs/planning/SPRINT-54-PLAN.md"
echo "2. Review API spec: docs/specs/GMAIL-RICH-EMAIL-SPEC.md"
echo "3. Review test matrix: tests/plans/SPRINT-54-TEST-MATRIX.md"
echo "4. Install bleach library: pip install bleach"
echo "5. Implement MimeBuilder.build_simple_text() first (simplest case)"
echo "6. Write passing unit tests for each method before moving on"
echo "7. Implement HTML sanitization with ALLOWED_TAGS/BLOCKED_TAGS"
echo "8. Add telemetry metrics (gmail_mime_build_seconds, etc.)"
echo "9. Extend src/actions/adapters/google.py with html/attachments params"
echo "10. Create integration test (quarantined by default)"
echo ""
echo "Feature Flags (keep OFF until Phase C complete):"
echo "  PROVIDER_GOOGLE_RICH_EMAIL_ENABLED=false"
echo "  ATTACHMENTS_ENABLED=false"
echo ""
echo "Questions? See: docs/planning/SPRINT-54-PLAN.md (Section 11: Open Questions)"
