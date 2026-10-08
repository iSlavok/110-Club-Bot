from datetime import datetime
from typing import Self

from pydantic import BaseModel

from app.models import User


class TelegramProfile(BaseModel):
    tg_id: int
    tg_username: str | None
    full_name: str


class UserDTO(BaseModel):
    id: int
    tg_id: int
    tg_username: str | None
    full_name: str
    vk_id: int | None
    vk_linked_at: datetime | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_obj(cls, user: User) -> Self:
        return cls(
            id=user.id,
            tg_id=user.tg_id,
            tg_username=user.tg_username,
            full_name=user.full_name,
            vk_id=user.vk_id,
            vk_linked_at=user.vk_linked_at,
            created_at=user.created_at,
            updated_at=user.updated_at,
        )
