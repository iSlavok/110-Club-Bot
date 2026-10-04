from sqlalchemy import BigInteger, String, true
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, str_enum
from app.enums import AdminRole


class AdminUser(Base):
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    name: Mapped[str] = mapped_column(String(100))
    role: Mapped[AdminRole] = mapped_column(str_enum(AdminRole))
    is_active: Mapped[bool] = mapped_column(server_default=true())
