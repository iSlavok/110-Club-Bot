from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, DateTime, ForeignKey, Index, String, UniqueConstraint
from sqlalchemy.orm import Mapped, declared_attr, mapped_column, relationship

from app.database import Base, str_enum
from app.enums import ChatAccessStatus

if TYPE_CHECKING:
    from app.models.user import User

INVITE_LINK_MAX_LEN = 255


# The bot manages only the people it let in through their personal join link; everyone else in the chat is not its
# business. chat_id pins the link to the chat it was made for: a club moved to a new chat gets new links.
class ChatAccess(Base):
    __table_args__ = (
        UniqueConstraint("club_id", "user_id"),
        Index("ix_chat_accesses_club_id_status", "club_id", "status"),
    )

    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))
    chat_id: Mapped[int] = mapped_column(BigInteger)
    invite_link: Mapped[str] = mapped_column(String(INVITE_LINK_MAX_LEN), unique=True)
    status: Mapped[ChatAccessStatus] = mapped_column(str_enum(ChatAccessStatus))
    invited_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    joined_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    kicked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))

    user: Mapped["User"] = relationship(lazy="raise")

    # Base pluralizes the class name, which would give "chat_accesss".
    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        return "chat_accesses"
