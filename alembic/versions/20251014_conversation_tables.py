"""Add conversation and messages tables for chat UI

Revision ID: 20251014_conversations
Revises: previous_revision
Create Date: 2025-10-14

Sprint 56 Week 1: Database schema for chat conversation persistence.
"""
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

# revision identifiers
revision = "20251014_conversations"
down_revision = None  # Update this to the latest revision ID
branch_labels = None
depends_on = None


def upgrade():
    # Create conversations table
    op.create_table(
        "conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("workspace_id", UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", sa.String(255), nullable=False),
        sa.Column("title", sa.String(500), nullable=True),  # Auto-generated from first message
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.TIMESTAMP, server_default=sa.text("NOW()"), nullable=False),
        sa.Index("idx_conversations_workspace_user", "workspace_id", "user_id"),
        sa.Index("idx_conversations_created_at", "created_at"),
    )

    # Create messages table
    op.create_table(
        "messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column(
            "conversation_id", UUID(as_uuid=True), sa.ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False
        ),
        sa.Column("role", sa.String(50), nullable=False),  # 'user' or 'assistant'
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("model", sa.String(100), nullable=True),  # 'gpt-4', 'claude-sonnet-4', etc.
        sa.Column("metadata", JSONB, nullable=True),  # tokens, latency, error info, etc.
        sa.Column("created_at", sa.TIMESTAMP, server_default=sa.text("NOW()"), nullable=False),
        sa.Index("idx_messages_conversation_id", "conversation_id"),
        sa.Index("idx_messages_created_at", "created_at"),
    )


def downgrade():
    op.drop_table("messages")
    op.drop_table("conversations")
