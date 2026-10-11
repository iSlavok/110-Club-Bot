from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base, str_enum
from app.enums import SheetSyncStatus


class SheetSync(Base):
    club_id: Mapped[int] = mapped_column(ForeignKey("clubs.id", ondelete="CASCADE"))
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    status: Mapped[SheetSyncStatus] = mapped_column(str_enum(SheetSyncStatus))
    added: Mapped[int]
    removal_requested: Mapped[int]
    # SheetIssue dicts; the shape is owned by app.schemas, the column only stores it.
    issues: Mapped[list[dict[str, Any]]] = mapped_column(JSONB, server_default=text("'[]'::jsonb"))
    error: Mapped[str | None] = mapped_column(Text)


Index("ix_sheet_syncs_club_id_started_at", SheetSync.club_id, SheetSync.started_at.desc())
