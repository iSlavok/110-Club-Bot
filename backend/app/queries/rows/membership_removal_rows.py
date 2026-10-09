from dataclasses import dataclass
from datetime import datetime

from app.enums import RemovalRequestStatus


@dataclass(frozen=True, slots=True)
class RemovalRequestRow:
    id: int
    club_id: int
    club_title: str
    block_id: int
    block_title: str
    status: RemovalRequestStatus
    alert_message_id: int | None
    created_at: datetime


@dataclass(frozen=True, slots=True)
class RemovalCandidateRow:
    vk_id: int
    full_name: str | None
    tg_username: str | None
