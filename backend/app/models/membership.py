from sqlalchemy import BigInteger, ForeignKey, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


# Keyed by vk_id, not user_id: the sheet lists students who may not have registered in the bot yet.
class Membership(Base):
    __table_args__ = (UniqueConstraint("block_id", "vk_id"),)

    block_id: Mapped[int] = mapped_column(ForeignKey("blocks.id", ondelete="CASCADE"))
    vk_id: Mapped[int] = mapped_column(BigInteger, index=True)
