from sqlalchemy import BigInteger, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

TG_USERNAME_MAX_LEN = 32
# Telegram allows 64 chars for each of first and last name, joined by a space.
TG_FULL_NAME_MAX_LEN = 129


class User(Base):
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    tg_username: Mapped[str | None] = mapped_column(String(TG_USERNAME_MAX_LEN))
    full_name: Mapped[str] = mapped_column(String(TG_FULL_NAME_MAX_LEN))
    vk_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
