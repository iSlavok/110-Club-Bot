from typing import Self

from pydantic import BaseModel, Field

from api.schemas.club_schemas import BlockResponse
from app.schemas import ClubStats, CurrentBlockStats


class CurrentBlockStatsResponse(BaseModel):
    block: BlockResponse = Field(description="Block running now")
    members: int = Field(description="Students of the block from the sheet")
    members_with_tg: int = Field(description="Of them, linked to a Telegram user of the bot")

    @classmethod
    def from_dto(cls, stats: CurrentBlockStats) -> Self:
        return cls(
            block=BlockResponse.from_dto(stats.block),
            members=stats.members,
            members_with_tg=stats.members_with_tg,
        )


class ClubStatsResponse(BaseModel):
    current_block: CurrentBlockStatsResponse | None = Field(description="Block running now, null between blocks")

    @classmethod
    def from_dto(cls, stats: ClubStats) -> Self:
        current_block = CurrentBlockStatsResponse.from_dto(stats.current_block) if stats.current_block else None
        return cls(current_block=current_block)
