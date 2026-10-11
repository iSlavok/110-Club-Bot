"""add lessons and reminders

Revision ID: b0f0d4175064
Revises: 797d13c4d37a
Create Date: 2026-10-10 01:02:37.351076
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "b0f0d4175064"
down_revision: str | Sequence[str] | None = "797d13c4d37a"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "lessons",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("club_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "kind", sa.Enum("lesson", "curator_call", name="lessonkind", native_enum=False, length=32), nullable=False
        ),
        sa.Column("title", sa.String(length=200), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("starts_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("call_url", sa.String(length=1000), nullable=True),
        sa.Column("is_cancelled", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("reminder_offsets", postgresql.ARRAY(sa.Integer()), server_default="{}", nullable=False),
        sa.Column("homework_deadline_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("homework_reminder_offsets", postgresql.ARRAY(sa.Integer()), server_default="{}", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["club_id"], ["clubs.id"], name=op.f("fk_lessons_club_id_clubs"), ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_lessons")),
    )
    op.create_index("ix_lessons_club_id_starts_at", "lessons", ["club_id", "starts_at"], unique=False)
    op.create_table(
        "reminders",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("club_id", sa.BigInteger(), nullable=False),
        sa.Column("lesson_id", sa.BigInteger(), nullable=False),
        sa.Column(
            "kind",
            sa.Enum(
                "lesson_upcoming",
                "lesson_starting",
                "homework_deadline",
                "lesson_rescheduled",
                "lesson_cancelled",
                "homework_deadline_changed",
                "homework_removed",
                name="reminderkind",
                native_enum=False,
                length=32,
            ),
            nullable=False,
        ),
        sa.Column("send_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "pending", "sent", "failed", "skipped", "cancelled", name="reminderstatus", native_enum=False, length=32
            ),
            server_default="pending",
            nullable=False,
        ),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("sent_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("message_id", sa.BigInteger(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(
            ["club_id"], ["clubs.id"], name=op.f("fk_reminders_club_id_clubs"), ondelete="RESTRICT"
        ),
        sa.ForeignKeyConstraint(
            ["lesson_id"], ["lessons.id"], name=op.f("fk_reminders_lesson_id_lessons"), ondelete="CASCADE"
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_reminders")),
    )
    op.create_index("ix_reminders_club_id_send_at", "reminders", ["club_id", "send_at"], unique=False)
    op.create_index(op.f("ix_reminders_lesson_id"), "reminders", ["lesson_id"], unique=False)
    op.create_index("ix_reminders_status_send_at", "reminders", ["status", "send_at"], unique=False)
    op.add_column(
        "app_settings",
        sa.Column(
            "default_lesson_offsets", postgresql.ARRAY(sa.Integer()), server_default="{1440,60,0}", nullable=False
        ),
    )
    op.add_column(
        "app_settings",
        sa.Column(
            "default_homework_offsets", postgresql.ARRAY(sa.Integer()), server_default="{2880,1440,180}", nullable=False
        ),
    )


def downgrade() -> None:
    op.drop_column("app_settings", "default_homework_offsets")
    op.drop_column("app_settings", "default_lesson_offsets")
    op.drop_index("ix_reminders_status_send_at", table_name="reminders")
    op.drop_index(op.f("ix_reminders_lesson_id"), table_name="reminders")
    op.drop_index("ix_reminders_club_id_send_at", table_name="reminders")
    op.drop_table("reminders")
    op.drop_index("ix_lessons_club_id_starts_at", table_name="lessons")
    op.drop_table("lessons")
