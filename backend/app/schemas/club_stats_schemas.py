from pydantic import BaseModel

from app.schemas.club_schemas import BlockDTO
from app.schemas.sheet_sync_schemas import SheetSyncDTO


class CurrentBlockStats(BaseModel):
    block: BlockDTO
    members: int
    members_with_tg: int


class ClubStats(BaseModel):
    current_block: CurrentBlockStats | None
    last_sync: SheetSyncDTO | None
