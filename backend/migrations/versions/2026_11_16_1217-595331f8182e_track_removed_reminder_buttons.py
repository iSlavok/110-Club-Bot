"""track removed reminder buttons

Revision ID: 595331f8182e
Revises: cb03c1a20cd7
Create Date: 2026-11-16 12:17:41.162223
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "595331f8182e"
down_revision: str | Sequence[str] | None = "cb03c1a20cd7"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("reminders", sa.Column("call_button_removed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("reminders", sa.Column("buttons_removed_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("reminders", "buttons_removed_at")
    op.drop_column("reminders", "call_button_removed_at")
