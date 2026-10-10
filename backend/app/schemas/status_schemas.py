from pydantic import BaseModel

from app.schemas.club_schemas import ClubDTO
from app.schemas.club_stats_schemas import CurrentBlockStats
from app.schemas.reminder_schemas import ReminderWithLessonDTO
from app.schemas.sheet_sync_schemas import SheetSyncDTO


class ClubSyncStatus(BaseModel):
    last_sync: SheetSyncDTO | None
    pending_removal_requests: int


class ReminderStatusSection(BaseModel):
    upcoming: list[ReminderWithLessonDTO]
    # Counted by the planned send time: a reminder fails within minutes of it.
    failed_last_day: int


class ClubStatus(BaseModel):
    club: ClubDTO
    current_block: CurrentBlockStats | None
    sync: ClubSyncStatus
    reminders: ReminderStatusSection


class StatusReport(BaseModel):
    clubs: list[ClubStatus]
