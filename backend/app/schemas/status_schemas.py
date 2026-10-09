from pydantic import BaseModel

from app.schemas.club_schemas import ClubDTO
from app.schemas.club_stats_schemas import CurrentBlockStats
from app.schemas.sheet_sync_schemas import SheetSyncDTO


class ClubSyncStatus(BaseModel):
    last_sync: SheetSyncDTO | None
    pending_removal_requests: int


class ClubStatus(BaseModel):
    club: ClubDTO
    current_block: CurrentBlockStats | None
    sync: ClubSyncStatus


class StatusReport(BaseModel):
    clubs: list[ClubStatus]
