from sqlalchemy import BigInteger, String, Text, false, true
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

CLUB_TEXT_MAX_LEN = 100


class Club(Base):
    title: Mapped[str] = mapped_column(String(CLUB_TEXT_MAX_LEN), unique=True)
    chat_id: Mapped[int | None] = mapped_column(BigInteger)
    reminders_topic_id: Mapped[int | None]
    spreadsheet_id: Mapped[str | None] = mapped_column(String(CLUB_TEXT_MAX_LEN))
    sheet_name: Mapped[str | None] = mapped_column(String(CLUB_TEXT_MAX_LEN))
    is_active: Mapped[bool] = mapped_column(server_default=true())
    hide_service_messages: Mapped[bool] = mapped_column(server_default=false())
    # Chat state kept by the worker, so the owner is alerted on a change, not on every run.
    chat_kicks_on_hold: Mapped[bool] = mapped_column(server_default=false())
    chat_error: Mapped[str | None] = mapped_column(Text)
