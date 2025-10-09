"""add oauth_tokens table

Revision ID: bb51836389e7
Revises: ce6ac882b60d
Create Date: 2025-10-08 14:59:28.023176

Sprint 53 Phase B: OAuth Integration
- oauth_tokens: Store encrypted OAuth access/refresh tokens with metadata
- Supports multi-provider (google, microsoft, etc.)
- Multi-tenant: workspace + actor isolation
"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "bb51836389e7"
down_revision: Union[str, None] = "ce6ac882b60d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Table: oauth_tokens
    # Note: actor_type_enum already exists from Sprint 51 migration (ce6ac882b60d)
    # Use postgresql.ENUM with create_type=False to reference existing type
    actor_type_enum = postgresql.ENUM("user", "api_key", name="actor_type_enum", create_type=False)

    op.create_table(
        "oauth_tokens",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("actor_type", actor_type_enum, nullable=False),
        sa.Column("actor_id", sa.Text(), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("scopes", sa.Text(), nullable=True),
        sa.Column("encrypted_access_token", sa.Text(), nullable=False),
        sa.Column("encrypted_refresh_token", sa.Text(), nullable=True),
        sa.Column("access_token_expires_at", sa.TIMESTAMP(timezone=True), nullable=True),
        sa.Column("created_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.TIMESTAMP(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.UniqueConstraint("workspace_id", "provider", "actor_type", "actor_id", name="uq_oauth_tokens_identity"),
    )
    op.create_index("idx_oauth_tokens_workspace_id", "oauth_tokens", ["workspace_id"])
    op.create_index("idx_oauth_tokens_workspace_provider", "oauth_tokens", ["workspace_id", "provider"])


def downgrade() -> None:
    # Drop indexes and table
    op.drop_index("idx_oauth_tokens_workspace_provider")
    op.drop_index("idx_oauth_tokens_workspace_id")
    op.drop_table("oauth_tokens")
