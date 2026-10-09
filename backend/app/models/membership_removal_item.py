from typing import TYPE_CHECKING

from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.membership_removal_request import MembershipRemovalRequest


class MembershipRemovalItem(Base):
    __table_args__ = (UniqueConstraint("request_id", "vk_id"),)

    request_id: Mapped[int] = mapped_column(ForeignKey("membership_removal_requests.id", ondelete="CASCADE"))
    vk_id: Mapped[int] = mapped_column(BigInteger)

    request: Mapped["MembershipRemovalRequest"] = relationship(lazy="raise")
