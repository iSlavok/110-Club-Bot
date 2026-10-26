"""add default lesson and deadline times

Revision ID: 5a11256a5191
Revises: 41c38fbe5402
Create Date: 2026-10-26 22:25:28.476069
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "5a11256a5191"
down_revision: str | Sequence[str] | None = "41c38fbe5402"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("app_settings", sa.Column("default_lesson_time", sa.Time(), server_default="16:00", nullable=False))
    op.add_column("app_settings", sa.Column("default_homework_time", sa.Time(), server_default="23:59", nullable=False))


def downgrade() -> None:
    op.drop_column("app_settings", "default_homework_time")
    op.drop_column("app_settings", "default_lesson_time")
