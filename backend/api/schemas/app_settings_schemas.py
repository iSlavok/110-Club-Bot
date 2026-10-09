from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field

from app.enums import VkLinkMode
from app.schemas import AppSettingsOverview


class AppSettingsResponse(BaseModel):
    vk_link_mode: VkLinkMode = Field(description="How students link their VK profile in the bot")
    configured_vk_link_modes: list[VkLinkMode] = Field(
        description="Modes with credentials in the server environment; only these can be switched on",
    )
    updated_at: datetime = Field(description="Last change, UTC")

    @classmethod
    def from_overview(cls, overview: AppSettingsOverview) -> Self:
        return cls(
            vk_link_mode=overview.settings.vk_link_mode,
            configured_vk_link_modes=overview.configured_vk_link_modes,
            updated_at=overview.settings.updated_at,
        )
