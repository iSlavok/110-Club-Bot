"""link lessons to the platform

Revision ID: cb03c1a20cd7
Revises: 182e27292724
Create Date: 2026-11-15 14:35:32.049001
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "cb03c1a20cd7"
down_revision: str | Sequence[str] | None = "182e27292724"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("clubs", sa.Column("platform_course_id", sa.Integer(), nullable=True))
    op.add_column("lessons", sa.Column("platform_lesson_id", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("lessons", "platform_lesson_id")
    op.drop_column("clubs", "platform_course_id")
