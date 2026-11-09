"""add block kick approval

Revision ID: 182e27292724
Revises: f77442414e7d
Create Date: 2026-11-09 23:40:52.459576
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "182e27292724"
down_revision: str | Sequence[str] | None = "f77442414e7d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("blocks", sa.Column("kicks_approved_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("blocks", sa.Column("kick_approval_message_id", sa.Integer(), nullable=True))
    op.add_column("blocks", sa.Column("kick_approval_waiting", sa.Integer(), nullable=True))
    # Blocks that already started had their kicks running without approval: they keep running.
    blocks = sa.table(
        "blocks",
        sa.column("starts_at", sa.DateTime(timezone=True)),
        sa.column("kicks_approved_at", sa.DateTime(timezone=True)),
    )
    op.execute(
        sa.update(blocks)
        .where(blocks.c.starts_at <= sa.func.now(), blocks.c.kicks_approved_at.is_(None))
        .values(kicks_approved_at=blocks.c.starts_at)
    )


def downgrade() -> None:
    op.drop_column("blocks", "kick_approval_waiting")
    op.drop_column("blocks", "kick_approval_message_id")
    op.drop_column("blocks", "kicks_approved_at")
