"""sync reminder buttons with the lesson

Revision ID: 9ca7f30ae2ce
Revises: 595331f8182e
Create Date: 2026-11-16 21:38:57.489752
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "9ca7f30ae2ce"
down_revision: str | Sequence[str] | None = "595331f8182e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("reminders", sa.Column("buttons", postgresql.JSONB(astext_type=sa.Text()), nullable=True))
    op.add_column("reminders", sa.Column("buttons_checked_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("reminders", sa.Column("buttons_lesson_version", sa.DateTime(timezone=True), nullable=True))
    op.drop_column("reminders", "call_button_removed_at")
    op.drop_column("reminders", "buttons_removed_at")


def downgrade() -> None:
    op.add_column("reminders", sa.Column("buttons_removed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("reminders", sa.Column("call_button_removed_at", sa.DateTime(timezone=True), nullable=True))
    op.drop_column("reminders", "buttons_lesson_version")
    op.drop_column("reminders", "buttons_checked_at")
    op.drop_column("reminders", "buttons")
