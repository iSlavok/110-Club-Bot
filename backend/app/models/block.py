from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base
from app.models.club import CLUB_TEXT_MAX_LEN


class Block(Base):
    __table_args__ = (
        UniqueConstraint("club_id", "sheet_column_title"),
        CheckConstraint("ends_at > starts_at", name="ends_after_start"),
    )

    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id", ondelete="RESTRICT"), index=True)
    title: Mapped[str] = mapped_column(String(CLUB_TEXT_MAX_LEN))
    sheet_column_title: Mapped[str] = mapped_column(String(CLUB_TEXT_MAX_LEN))
    starts_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    ends_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    # The first kicks of a block wait for an admin: a half-filled sheet column would empty the chat.
    kicks_approved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    # The approval alert and how many students it listed, so it is edited only when the number changes.
    kick_approval_message_id: Mapped[int | None]
    kick_approval_waiting: Mapped[int | None]
