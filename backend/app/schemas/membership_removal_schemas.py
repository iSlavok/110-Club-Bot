from datetime import datetime

from pydantic import BaseModel

from app.enums import RemovalRequestStatus


class RemovalCandidate(BaseModel):
    vk_id: int
    full_name: str | None
    tg_username: str | None


class RemovalRequestAlert(BaseModel):
    club_title: str
    block_title: str
    status: RemovalRequestStatus
    created_at: datetime
    candidates: list[RemovalCandidate]
    decided_by: str | None = None
    decided_at: datetime | None = None
