from datetime import datetime

from sqlalchemy import BigInteger, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, str_enum
from app.enums import RemovalRequestStatus


# Members gone from a ready sheet column stay in the block until the removal is confirmed in the alerts chat.
class MembershipRemovalRequest(Base):
    block_id: Mapped[int] = mapped_column(ForeignKey("blocks.id", ondelete="CASCADE"), index=True)
    status: Mapped[RemovalRequestStatus] = mapped_column(str_enum(RemovalRequestStatus))
    alert_message_id: Mapped[int | None] = mapped_column(BigInteger)
    decided_by_tg_id: Mapped[int | None] = mapped_column(BigInteger)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
