"""add vk link data model

Revision ID: d38ecfd6e68f
Revises: 92aa61453499
Create Date: 2026-10-09 01:20:57.338678
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import insert

revision: str = "d38ecfd6e68f"
down_revision: str | Sequence[str] | None = "92aa61453499"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

APP_SETTINGS_ID = 1


def upgrade() -> None:
    app_settings = op.create_table(
        "app_settings",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column(
            "vk_link_mode",
            sa.Enum("link", "oauth", name="vklinkmode", native_enum=False, length=32),
            server_default="oauth",
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.CheckConstraint("id = 1", name=op.f("ck_app_settings_single_row")),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_app_settings")),
    )
    op.execute(insert(app_settings).values(id=APP_SETTINGS_ID).on_conflict_do_nothing(index_elements=["id"]))
    op.create_table(
        "vk_auth_requests",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("state_hash", sa.String(length=64), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("code_verifier", sa.String(length=128), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_vk_auth_requests_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_vk_auth_requests")),
        sa.UniqueConstraint("state_hash", name=op.f("uq_vk_auth_requests_state_hash")),
    )
    op.create_index(op.f("ix_vk_auth_requests_user_id"), "vk_auth_requests", ["user_id"], unique=False)
    op.add_column("users", sa.Column("vk_linked_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "vk_linked_at")
    op.drop_index(op.f("ix_vk_auth_requests_user_id"), table_name="vk_auth_requests")
    op.drop_table("vk_auth_requests")
    op.drop_table("app_settings")
