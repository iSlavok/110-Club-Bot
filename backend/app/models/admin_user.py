from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, String, true
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.user import TG_FULL_NAME_MAX_LEN

if TYPE_CHECKING:
    from app.models.role import Role


class AdminUser(Base):
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    name: Mapped[str] = mapped_column(String(TG_FULL_NAME_MAX_LEN))
    # NULL only for owners: their access comes from AUTH_OWNER_IDS, not from a role.
    role_id: Mapped[int | None] = mapped_column(ForeignKey("roles.id", ondelete="RESTRICT"), index=True)
    is_active: Mapped[bool] = mapped_column(server_default=true())

    role: Mapped["Role | None"] = relationship(lazy="raise")
