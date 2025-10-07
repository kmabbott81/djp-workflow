"""Add auth tables: api_keys, roles, action_audit

Revision ID: ce6ac882b60d
Revises:
Create Date: 2025-10-06 06:55:00.000000

Sprint 51 Phase 1: Secure Core
- api_keys: API key management with scopes
- roles: User role assignments
- action_audit: Audit log for actions with redaction
"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "ce6ac882b60d"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM types
    op.execute("CREATE TYPE actor_type_enum AS ENUM ('user', 'api_key')")
    op.execute("CREATE TYPE role_enum AS ENUM ('admin', 'developer', 'viewer')")
    op.execute("CREATE TYPE audit_status_enum AS ENUM ('ok', 'error')")
    op.execute(
        "CREATE TYPE error_reason_enum AS ENUM ('timeout', 'provider_unconfigured', 'validation', 'downstream_5xx', 'other', 'none')"
    )

    # Table: api_keys
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("key_hash", sa.Text(), nullable=False),
        sa.Column("scopes", postgresql.JSONB(), nullable=False),
        sa.Column("created_by", sa.Text(), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("revoked_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.UniqueConstraint("workspace_id", "key_hash", name="uq_workspace_key"),
    )
    op.create_index("idx_api_keys_workspace_id", "api_keys", ["workspace_id"])
    op.create_index("idx_api_keys_key_hash", "api_keys", ["key_hash"])

    # Table: roles
    op.create_table(
        "roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.Text(), nullable=False),
        sa.Column("role", sa.Enum("admin", "developer", "viewer", name="role_enum"), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_roles_workspace_user", "roles", ["workspace_id", "user_id"])

    # Table: action_audit
    op.create_table(
        "action_audit",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("run_id", sa.Text(), nullable=True),
        sa.Column("request_id", sa.Text(), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_type", sa.Enum("user", "api_key", name="actor_type_enum"), nullable=False),
        sa.Column("actor_id", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("action_id", sa.Text(), nullable=False),
        sa.Column("preview_id", sa.Text(), nullable=True),
        sa.Column("idempotency_key_hash", sa.Text(), nullable=True),
        sa.Column("signature_present", sa.Boolean(), nullable=False, default=False),
        sa.Column("params_hash", sa.Text(), nullable=False),
        sa.Column("params_prefix64", sa.Text(), nullable=False),
        sa.Column("status", sa.Enum("ok", "error", name="audit_status_enum"), nullable=False),
        sa.Column(
            "error_reason",
            sa.Enum(
                "timeout",
                "provider_unconfigured",
                "validation",
                "downstream_5xx",
                "other",
                "none",
                name="error_reason_enum",
            ),
            nullable=False,
            default="none",
        ),
        sa.Column("http_status", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_action_audit_workspace_created", "action_audit", ["workspace_id", "created_at"])
    op.create_index("idx_action_audit_run_id", "action_audit", ["run_id"])


def downgrade() -> None:
    # Drop tables
    op.drop_index("idx_action_audit_run_id")
    op.drop_index("idx_action_audit_workspace_created")
    op.drop_table("action_audit")

    op.drop_index("idx_roles_workspace_user")
    op.drop_table("roles")

    op.drop_index("idx_api_keys_key_hash")
    op.drop_index("idx_api_keys_workspace_id")
    op.drop_table("api_keys")

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS error_reason_enum")
    op.execute("DROP TYPE IF EXISTS audit_status_enum")
    op.execute("DROP TYPE IF EXISTS role_enum")
    op.execute("DROP TYPE IF EXISTS actor_type_enum")
