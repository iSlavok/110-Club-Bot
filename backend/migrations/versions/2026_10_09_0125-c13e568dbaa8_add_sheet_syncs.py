"""add sheet syncs

Revision ID: c13e568dbaa8
Revises: d38ecfd6e68f
Create Date: 2026-10-09 01:25:43.722930
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "c13e568dbaa8"
down_revision: str | Sequence[str] | None = "d38ecfd6e68f"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sheet_syncs",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("club_id", sa.BigInteger(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status", sa.Enum("ok", "failed", name="sheetsyncstatus", native_enum=False, length=32), nullable=False
        ),
        sa.Column("added", sa.Integer(), nullable=False),
        sa.Column("removed", sa.Integer(), nullable=False),
        sa.Column(
            "issues", postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False
        ),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["club_id"], ["clubs.id"], name=op.f("fk_sheet_syncs_club_id_clubs"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_sheet_syncs")),
    )
    op.create_index(
        "ix_sheet_syncs_club_id_started_at",
        "sheet_syncs",
        ["club_id", sa.literal_column("started_at DESC")],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_sheet_syncs_club_id_started_at", table_name="sheet_syncs")
    op.drop_table("sheet_syncs")
