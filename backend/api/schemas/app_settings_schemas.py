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
    default_lesson_offsets: list[int] = Field(
        description="Minutes before the start prefilled in a new lesson, latest first; 0 means at the start",
    )
    default_homework_offsets: list[int] = Field(
        description="Minutes before the homework deadline prefilled in a new lesson, latest first",
    )
    updated_at: datetime = Field(description="Last change, UTC")

    @classmethod
    def from_overview(cls, overview: AppSettingsOverview) -> Self:
        return cls(
            vk_link_mode=overview.settings.vk_link_mode,
            configured_vk_link_modes=overview.configured_vk_link_modes,
            default_lesson_offsets=overview.settings.default_lesson_offsets,
            default_homework_offsets=overview.settings.default_homework_offsets,
            updated_at=overview.settings.updated_at,
        )
