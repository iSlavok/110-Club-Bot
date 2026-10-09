from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text, false
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, str_enum
from app.enums import LessonKind

LESSON_TITLE_MAX_LEN = 200
CALL_URL_MAX_LEN = 1000


class Lesson(Base):
    __table_args__ = (Index("ix_lessons_club_id_starts_at", "club_id", "starts_at"),)

    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id", ondelete="RESTRICT"))
    kind: Mapped[LessonKind] = mapped_column(str_enum(LessonKind))
    title: Mapped[str] = mapped_column(String(LESSON_TITLE_MAX_LEN))
    description: Mapped[str | None] = mapped_column(Text)
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    call_url: Mapped[str | None] = mapped_column(String(CALL_URL_MAX_LEN))
    is_cancelled: Mapped[bool] = mapped_column(server_default=false())
    # Minutes before starts_at, one reminder each; 0 is the "lesson is starting" message.
    reminder_offsets: Mapped[list[int]] = mapped_column(ARRAY(Integer), server_default="{}")
    # The homework is these two fields: NULL deadline means the lesson has none.
    homework_deadline_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    homework_reminder_offsets: Mapped[list[int]] = mapped_column(ARRAY(Integer), server_default="{}")
