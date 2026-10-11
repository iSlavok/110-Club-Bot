from sqlalchemy import String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base

ROLE_TITLE_MAX_LEN = 64


class Role(Base):
    title: Mapped[str] = mapped_column(String(ROLE_TITLE_MAX_LEN), unique=True)
    # Permission values; ones removed from the code are ignored on read, so no data migration is needed.
    permissions: Mapped[list[str]] = mapped_column(ARRAY(String(64)), server_default="{}")
