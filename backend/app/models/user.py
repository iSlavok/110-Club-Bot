from sqlalchemy import BigInteger, Computed, Index, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

TG_USERNAME_MAX_LEN = 32
# Telegram allows 64 chars for each of first and last name, joined by a space.
TG_FULL_NAME_MAX_LEN = 129

# Keep in sync with normalize_search_query: both sides of a fuzzy match must be normalized the same way.
_SEARCH_TEXT = "lower(translate(full_name || ' ' || coalesce(tg_username, ''), 'Ёё', 'Ее'))"


class User(Base):
    __table_args__ = (
        Index(
            "ix_users_search_text",
            "search_text",
            postgresql_using="gin",
            postgresql_ops={"search_text": "gin_trgm_ops"},
        ),
    )

    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    tg_username: Mapped[str | None] = mapped_column(String(TG_USERNAME_MAX_LEN))
    full_name: Mapped[str] = mapped_column(String(TG_FULL_NAME_MAX_LEN))
    vk_id: Mapped[int | None] = mapped_column(BigInteger, unique=True)
    # Service column for fuzzy search, maintained by Postgres; not part of UserDTO.
    search_text: Mapped[str] = mapped_column(Text, Computed(_SEARCH_TEXT, persisted=True))
