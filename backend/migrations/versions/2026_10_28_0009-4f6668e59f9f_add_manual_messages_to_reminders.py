"""add manual messages to reminders

Revision ID: 4f6668e59f9f
Revises: 5a11256a5191
Create Date: 2026-10-28 00:09:09.018914
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "4f6668e59f9f"
down_revision: str | Sequence[str] | None = "5a11256a5191"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("reminders", sa.Column("text", sa.Text(), nullable=True))
    op.alter_column("reminders", "lesson_id", existing_type=sa.BIGINT(), nullable=True)
    op.create_check_constraint(
        op.f("ck_reminders_message_has_no_lesson"),
        "reminders",
        "(kind = 'message') = (lesson_id IS NULL)",
    )
    op.create_check_constraint(
        op.f("ck_reminders_only_message_has_text"),
        "reminders",
        "(kind = 'message') = (text IS NOT NULL)",
    )


# Messages written by admins have no lesson to keep them by: they are dropped.
def downgrade() -> None:
    op.drop_constraint(op.f("ck_reminders_only_message_has_text"), "reminders", type_="check")
    op.drop_constraint(op.f("ck_reminders_message_has_no_lesson"), "reminders", type_="check")
    op.execute(sa.text("DELETE FROM reminders WHERE kind = 'message'"))
    op.alter_column("reminders", "lesson_id", existing_type=sa.BIGINT(), nullable=False)
    op.drop_column("reminders", "text")
