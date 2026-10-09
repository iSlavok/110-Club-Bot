from pydantic import BaseModel

from app.schemas.club_schemas import BlockDTO


class CurrentBlockStats(BaseModel):
    block: BlockDTO
    members: int
    members_with_tg: int


class ClubStats(BaseModel):
    current_block: CurrentBlockStats | None
