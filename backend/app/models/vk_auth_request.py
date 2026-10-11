from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base
from app.models.admin_session import SHA256_HEX_LEN

if TYPE_CHECKING:
    from app.models.user import User

# RFC 7636 caps the PKCE code verifier at 128 characters.
CODE_VERIFIER_MAX_LEN = 128


class VkAuthRequest(Base):
    state_hash: Mapped[str] = mapped_column(String(SHA256_HEX_LEN), unique=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    code_verifier: Mapped[str] = mapped_column(String(CODE_VERIFIER_MAX_LEN))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(lazy="raise")
