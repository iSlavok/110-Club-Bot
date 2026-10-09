from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base, str_enum
from app.enums import ReminderKind, ReminderStatus

if TYPE_CHECKING:
    from app.models.club import Club
    from app.models.lesson import Lesson


# Outbox of chat messages: the worker sends the due rows, so plans survive restarts and never go out twice.
class Reminder(Base):
    __table_args__ = (
        Index("ix_reminders_status_send_at", "status", "send_at"),
        Index("ix_reminders_club_id_send_at", "club_id", "send_at"),
    )

    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id", ondelete="RESTRICT"))
    lesson_id: Mapped[int] = mapped_column(ForeignKey("lessons.id", ondelete="CASCADE"), index=True)
    kind: Mapped[ReminderKind] = mapped_column(str_enum(ReminderKind))
    send_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[ReminderStatus] = mapped_column(
        str_enum(ReminderStatus),
        server_default=ReminderStatus.PENDING.value,
    )
    attempts: Mapped[int] = mapped_column(server_default="0")
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    message_id: Mapped[int | None] = mapped_column(BigInteger)
    error: Mapped[str | None] = mapped_column(Text)

    club: Mapped["Club"] = relationship(lazy="raise")
    lesson: Mapped["Lesson"] = relationship(lazy="raise")
