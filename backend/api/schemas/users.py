from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field

from app.schemas import PageParams, UserDTO


class UserListParams(PageParams):
    q: str | None = Field(default=None, max_length=100, description="Name, username, Telegram or VK id")


class UserResponse(BaseModel):
    id: int = Field(description="User id")
    tg_id: int = Field(description="Telegram user id")
    tg_username: str | None = Field(description="Telegram username without @")
    full_name: str = Field(description="Telegram display name")
    vk_id: int | None = Field(description="Linked VK id")
    created_at: datetime = Field(description="First /start, UTC")

    @classmethod
    def from_dto(cls, user: UserDTO) -> Self:
        return cls(
            id=user.id,
            tg_id=user.tg_id,
            tg_username=user.tg_username,
            full_name=user.full_name,
            vk_id=user.vk_id,
            created_at=user.created_at,
        )
