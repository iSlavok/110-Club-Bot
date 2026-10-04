from sqlalchemy import BigInteger, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Club(Base):
    title: Mapped[str] = mapped_column(String(100), unique=True)
    chat_id: Mapped[int | None] = mapped_column(BigInteger)
    reminders_topic_id: Mapped[int | None]
    spreadsheet_id: Mapped[str | None] = mapped_column(String(100))
    sheet_name: Mapped[str | None] = mapped_column(String(100))
    is_active: Mapped[bool] = mapped_column(server_default=true())
