"""initial schema

Revision ID: 03e97a1dbdb9
Revises:
Create Date: 2026-10-07 16:10:22.220026
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "03e97a1dbdb9"
down_revision: str | Sequence[str] | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "admin_users",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("tg_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("role", sa.Enum("admin", "curator", name="adminrole", native_enum=False, length=32), nullable=False),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_admin_users")),
        sa.UniqueConstraint("tg_id", name=op.f("uq_admin_users_tg_id")),
    )
    op.create_table(
        "clubs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=True),
        sa.Column("reminders_topic_id", sa.Integer(), nullable=True),
        sa.Column("spreadsheet_id", sa.String(length=100), nullable=True),
        sa.Column("sheet_name", sa.String(length=100), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_clubs")),
        sa.UniqueConstraint("title", name=op.f("uq_clubs_title")),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("tg_id", sa.BigInteger(), nullable=False),
        sa.Column("tg_username", sa.String(length=32), nullable=True),
        sa.Column("full_name", sa.String(length=129), nullable=False),
        sa.Column("vk_id", sa.BigInteger(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_users")),
        sa.UniqueConstraint("tg_id", name=op.f("uq_users_tg_id")),
        sa.UniqueConstraint("vk_id", name=op.f("uq_users_vk_id")),
    )
    op.create_table(
        "blocks",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("club_id", sa.BigInteger(), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("sheet_column_title", sa.String(length=100), nullable=False),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("ends_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("ends_at > starts_at", name=op.f("ck_blocks_ends_after_start")),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], name=op.f("fk_blocks_club_id_clubs"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_blocks")),
        sa.UniqueConstraint("club_id", "sheet_column_title", name=op.f("uq_blocks_club_id_sheet_column_title")),
    )
    op.create_index(op.f("ix_blocks_club_id"), "blocks", ["club_id"], unique=False)
    op.create_table(
        "memberships",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("block_id", sa.BigInteger(), nullable=False),
        sa.Column("vk_id", sa.BigInteger(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["block_id"], ["blocks.id"], name=op.f("fk_memberships_block_id_blocks"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_memberships")),
        sa.UniqueConstraint("block_id", "vk_id", name=op.f("uq_memberships_block_id_vk_id")),
    )
    op.create_index(op.f("ix_memberships_vk_id"), "memberships", ["vk_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_memberships_vk_id"), table_name="memberships")
    op.drop_table("memberships")
    op.drop_index(op.f("ix_blocks_club_id"), table_name="blocks")
    op.drop_table("blocks")
    op.drop_table("users")
    op.drop_table("clubs")
    op.drop_table("admin_users")
