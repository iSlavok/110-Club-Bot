from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.admin_user import AdminUser

SHA256_HEX_LEN = 64


class AdminSession(Base):
    token_hash: Mapped[str] = mapped_column(String(SHA256_HEX_LEN), unique=True)
    admin_user_id: Mapped[int] = mapped_column(ForeignKey("admin_users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    admin_user: Mapped["AdminUser"] = relationship(lazy="raise")
