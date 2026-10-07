from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.admin_session import SHA256_HEX_LEN

if TYPE_CHECKING:
    from app.models.admin_user import AdminUser


class LoginCode(Base):
    code_hash: Mapped[str] = mapped_column(String(SHA256_HEX_LEN), index=True)
    admin_user_id: Mapped[int] = mapped_column(ForeignKey("admin_users.id", ondelete="CASCADE"), index=True)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    admin_user: Mapped["AdminUser"] = relationship(lazy="raise")
