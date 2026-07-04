"""initial schema: users, chat_sessions, memory_summaries, transactions

Revision ID: 0001
Revises:
Create Date: 2026-07-04
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("tg_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "status",
            sa.Enum("ONBOARDING", "ACTIVE", "BLOCKED", name="userstatus"),
            nullable=False,
        ),
        sa.Column("encrypted_birth_data", sa.Text(), nullable=False, server_default=""),
        sa.Column("memory_summary", sa.Text(), nullable=True),
        sa.Column("memory_summary_version", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("talk_seconds", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("daily_messages", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("weekly_messages", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("last_daily_reset", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_weekly_reset", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "tariff",
            sa.Enum("FREE", "PREMIUM_MONTHLY", "PREMIUM_YEARLY", name="tariff"),
            nullable=False,
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            onupdate=sa.func.now(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tg_id"),
    )
    op.create_index("ix_users_tg_id", "users", ["tg_id"])

    op.create_table(
        "chat_sessions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "ACTIVE",
                "ENDED_EXPLICIT",
                "ENDED_SEMANTIC",
                "ENDED_TIMEOUT",
                name="sessionstatus",
            ),
            nullable=False,
        ),
        sa.Column(
            "messages_since_last_semantic_check",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_chat_sessions_user_id", "chat_sessions", ["user_id"])

    op.create_table(
        "memory_summaries",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("version", sa.Integer(), nullable=False, server_default="1"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            onupdate=sa.func.now(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id"),
    )
    op.create_index("ix_memory_summaries_user_id", "memory_summaries", ["user_id"])

    op.create_table(
        "transactions",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.String(30), nullable=False),
        sa.Column("provider_transaction_id", sa.String(255), nullable=False),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("currency", sa.String(10), nullable=False, server_default="USD"),
        sa.Column(
            "status",
            sa.Enum("PENDING", "COMPLETED", "FAILED", name="transactionstatus"),
            nullable=False,
        ),
        sa.Column("plan", sa.String(30), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            onupdate=sa.func.now(),
            nullable=True,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_transaction_id"),
    )
    op.create_index("ix_transactions_user_id", "transactions", ["user_id"])
    op.create_index(
        "ix_transactions_provider_transaction_id",
        "transactions",
        ["provider_transaction_id"],
    )


def downgrade() -> None:
    op.drop_table("transactions")
    op.drop_table("memory_summaries")
    op.drop_table("chat_sessions")
    op.drop_table("users")

    op.execute("DROP TYPE IF EXISTS transactionstatus")
    op.execute("DROP TYPE IF EXISTS sessionstatus")
    op.execute("DROP TYPE IF EXISTS tariff")
    op.execute("DROP TYPE IF EXISTS userstatus")
