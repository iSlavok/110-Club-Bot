from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field

from app.enums import VkLinkMode
from app.models import AppSettings
from app.schemas.patch_schemas import Maybe, PatchSchema


class AppSettingsDTO(BaseModel):
    id: int
    vk_link_mode: VkLinkMode
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_obj(cls, settings: AppSettings) -> Self:
        return cls(
            id=settings.id,
            vk_link_mode=settings.vk_link_mode,
            created_at=settings.created_at,
            updated_at=settings.updated_at,
        )


class AppSettingsOverview(BaseModel):
    settings: AppSettingsDTO
    # Modes whose credentials are present in the server environment; the others cannot be switched on.
    configured_vk_link_modes: list[VkLinkMode]


class AppSettingsUpdate(PatchSchema):
    vk_link_mode: Maybe[VkLinkMode] = Field(description="How students link their VK profile in the bot")
