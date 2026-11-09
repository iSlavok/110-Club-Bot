"""add club chat invites failing

Revision ID: f77442414e7d
Revises: 2533ab5aed3d
Create Date: 2026-11-09 22:46:13.791609
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f77442414e7d"
down_revision: str | Sequence[str] | None = "2533ab5aed3d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clubs", sa.Column("chat_invites_failing", sa.Boolean(), server_default=sa.text("false"), nullable=False)
    )


def downgrade() -> None:
    op.drop_column("clubs", "chat_invites_failing")
