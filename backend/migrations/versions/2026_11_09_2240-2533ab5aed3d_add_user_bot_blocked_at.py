"""add user bot blocked at

Revision ID: 2533ab5aed3d
Revises: c4e88cbf5828
Create Date: 2026-11-09 22:40:56.331337
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "2533ab5aed3d"
down_revision: str | Sequence[str] | None = "c4e88cbf5828"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("bot_blocked_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "bot_blocked_at")
