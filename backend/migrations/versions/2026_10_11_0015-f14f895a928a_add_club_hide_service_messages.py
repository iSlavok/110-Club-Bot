"""add club hide service messages

Revision ID: f14f895a928a
Revises: 3c8cee4d64c8
Create Date: 2026-10-11 00:15:59.832238
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f14f895a928a"
down_revision: str | Sequence[str] | None = "3c8cee4d64c8"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "clubs", sa.Column("hide_service_messages", sa.Boolean(), server_default=sa.text("false"), nullable=False)
    )


def downgrade() -> None:
    op.drop_column("clubs", "hide_service_messages")
