from app.exceptions import AppSettingsMissingError, EmptyUpdateError, VkLinkModeNotConfiguredError
from app.models import AppSettings
from app.repositories import AppSettingsRepository
from app.schemas import AppSettingsDTO, AppSettingsOverview, AppSettingsUpdate
from app.services.vk_link_availability import VkLinkAvailability


class AppSettingsService:
    def __init__(
        self,
        app_settings_repository: AppSettingsRepository,
        vk_link_availability: VkLinkAvailability,
    ) -> None:
        self._app_settings_repository = app_settings_repository
        self._vk_link_availability = vk_link_availability

    async def get(self) -> AppSettingsDTO:
        settings = await self._get()
        return AppSettingsDTO.from_orm_obj(settings)

    async def get_overview(self) -> AppSettingsOverview:
        settings = await self._get()
        return self._overview(settings)

    async def update(self, patch: AppSettingsUpdate) -> AppSettingsOverview:
        if patch.is_empty():
            raise EmptyUpdateError
        settings = await self._get()
        vk_link_mode = patch.vk_link_mode.apply(settings.vk_link_mode)
        if vk_link_mode != settings.vk_link_mode and not self._vk_link_availability.is_configured(vk_link_mode):
            raise VkLinkModeNotConfiguredError(vk_link_mode)
        settings.vk_link_mode = vk_link_mode
        settings.default_lesson_offsets = patch.default_lesson_offsets.apply(settings.default_lesson_offsets)
        settings.default_homework_offsets = patch.default_homework_offsets.apply(settings.default_homework_offsets)
        await self._app_settings_repository.flush()
        return self._overview(settings)

    async def _get(self) -> AppSettings:
        settings = await self._app_settings_repository.get()
        if settings is None:
            raise AppSettingsMissingError
        return settings

    def _overview(self, settings: AppSettings) -> AppSettingsOverview:
        return AppSettingsOverview(
            settings=AppSettingsDTO.from_orm_obj(settings),
            configured_vk_link_modes=self._vk_link_availability.configured_modes(),
        )
