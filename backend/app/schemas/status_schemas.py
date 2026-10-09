from pydantic import BaseModel

from app.schemas.club_schemas import ClubDTO
from app.schemas.club_stats_schemas import CurrentBlockStats


class ClubStatus(BaseModel):
    club: ClubDTO
    current_block: CurrentBlockStats | None


class StatusReport(BaseModel):
    clubs: list[ClubStatus]
