from typing import Self

from pydantic import BaseModel, Field

from app.schemas import DashboardStats


class DashboardStatsResponse(BaseModel):
    active_clubs: int = Field(description="Active clubs")
    current_blocks: int = Field(description="Blocks of active clubs running now")
    users: int = Field(description="Users who started the bot")
    users_with_vk: int = Field(description="Users with a linked VK profile")

    @classmethod
    def from_dto(cls, stats: DashboardStats) -> Self:
        return cls(
            active_clubs=stats.active_clubs,
            current_blocks=stats.current_blocks,
            users=stats.users,
            users_with_vk=stats.users_with_vk,
        )
