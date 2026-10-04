from typing import Self

from pydantic import BaseModel

from app.models import User


class TelegramProfile(BaseModel):
    tg_id: int
    tg_username: str | None
    full_name: str


class UserSchema(BaseModel):
    id: int
    tg_id: int
    tg_username: str | None
    full_name: str
    vk_id: int | None

    @classmethod
    def from_orm_obj(cls, user: User) -> Self:
        return cls(
            id=user.id,
            tg_id=user.tg_id,
            tg_username=user.tg_username,
            full_name=user.full_name,
            vk_id=user.vk_id,
        )
