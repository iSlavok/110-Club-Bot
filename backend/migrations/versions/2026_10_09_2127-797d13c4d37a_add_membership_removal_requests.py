"""add membership removal requests

Revision ID: 797d13c4d37a
Revises: c13e568dbaa8
Create Date: 2026-10-09 21:27:15.066987
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "797d13c4d37a"
down_revision: str | Sequence[str] | None = "c13e568dbaa8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "membership_removal_requests",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("block_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending",
                "confirmed",
                "rejected",
                "cancelled",
                name="removalrequeststatus",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("alert_message_id", sa.BigInteger(), nullable=True),
        sa.Column("decided_by_tg_id", sa.BigInteger(), nullable=True),
        sa.Column("decided_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["block_id"], ["blocks.id"], name=op.f("fk_membership_removal_requests_block_id_blocks"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_membership_removal_requests")),
    )
    op.create_index(
        op.f("ix_membership_removal_requests_block_id"), "membership_removal_requests", ["block_id"], unique=False
    )
    op.create_table(
        "membership_removal_items",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("request_id", sa.BigInteger(), nullable=False),
        sa.Column("vk_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["request_id"],
            ["membership_removal_requests.id"],
            name=op.f("fk_membership_removal_items_request_id_membership_removal_requests"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_membership_removal_items")),
        sa.UniqueConstraint("request_id", "vk_id", name=op.f("uq_membership_removal_items_request_id_vk_id")),
    )
    op.alter_column("sheet_syncs", "removed", new_column_name="removal_requested")


def downgrade() -> None:
    op.alter_column("sheet_syncs", "removal_requested", new_column_name="removed")
    op.drop_table("membership_removal_items")
    op.drop_index(op.f("ix_membership_removal_requests_block_id"), table_name="membership_removal_requests")
    op.drop_table("membership_removal_requests")
