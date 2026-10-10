"""add chat accesses

Revision ID: 3c8cee4d64c8
Revises: b0f0d4175064
Create Date: 2026-10-10 21:31:47.855092
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "3c8cee4d64c8"
down_revision: str | Sequence[str] | None = "b0f0d4175064"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "chat_accesses",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("club_id", sa.BigInteger(), nullable=False),
        sa.Column("user_id", sa.BigInteger(), nullable=False),
        sa.Column("chat_id", sa.BigInteger(), nullable=False),
        sa.Column("invite_link", sa.String(length=255), nullable=False),
        sa.Column(
            "status",
            sa.Enum("invited", "joined", "left", "kicked", name="chataccessstatus", native_enum=False, length=32),
            nullable=False,
        ),
        sa.Column("invited_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("joined_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("kicked_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["club_id"], ["clubs.id"], name=op.f("fk_chat_accesses_club_id_clubs"), ondelete="CASCADE"
        ),
        sa.ForeignKeyConstraint(
            ["user_id"], ["users.id"], name=op.f("fk_chat_accesses_user_id_users"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_chat_accesses")),
        sa.UniqueConstraint("club_id", "user_id", name=op.f("uq_chat_accesses_club_id_user_id")),
        sa.UniqueConstraint("invite_link", name=op.f("uq_chat_accesses_invite_link")),
    )
    op.create_index("ix_chat_accesses_club_id_status", "chat_accesses", ["club_id", "status"], unique=False)
    op.add_column(
        "clubs", sa.Column("chat_kicks_on_hold", sa.Boolean(), server_default=sa.text("false"), nullable=False)
    )
    op.add_column("clubs", sa.Column("chat_error", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("clubs", "chat_error")
    op.drop_column("clubs", "chat_kicks_on_hold")
    op.drop_index("ix_chat_accesses_club_id_status", table_name="chat_accesses")
    op.drop_table("chat_accesses")
