import pytest

from app.config import VkSettings
from app.enums import VkLinkMode
from app.exceptions import EmptyUpdateError, VkLinkModeNotConfiguredError
from app.schemas import AppSettingsUpdate
from app.services import AppSettingsService
from tests.factories import set_app_settings


@pytest.fixture
async def service(request_container) -> AppSettingsService:
    return await request_container.get(AppSettingsService)


@pytest.fixture
async def vk_settings(container) -> VkSettings:
    return await container.get(VkSettings)


async def test_overview_lists_configured_modes(service) -> None:
    overview = await service.get_overview()

    assert overview.settings.vk_link_mode is VkLinkMode.OAUTH
    assert overview.configured_vk_link_modes == [VkLinkMode.LINK, VkLinkMode.OAUTH]


async def test_switches_vk_link_mode(service) -> None:
    overview = await service.update(AppSettingsUpdate.model_validate({"vk_link_mode": "link"}))

    assert overview.settings.vk_link_mode is VkLinkMode.LINK
    settings = await service.get()
    assert settings.vk_link_mode is VkLinkMode.LINK


async def test_refuses_mode_without_credentials(service, vk_settings) -> None:
    vk_settings.service_token = None

    with pytest.raises(VkLinkModeNotConfiguredError):
        await service.update(AppSettingsUpdate.model_validate({"vk_link_mode": "link"}))


async def test_keeping_the_current_mode_is_allowed_even_without_credentials(service, db_session, vk_settings) -> None:
    await set_app_settings(db_session, vk_link_mode=VkLinkMode.LINK)
    vk_settings.service_token = None

    overview = await service.update(AppSettingsUpdate.model_validate({"vk_link_mode": "link"}))

    assert overview.settings.vk_link_mode is VkLinkMode.LINK
    assert overview.configured_vk_link_modes == [VkLinkMode.OAUTH]


async def test_empty_patch_is_rejected(service) -> None:
    with pytest.raises(EmptyUpdateError):
        await service.update(AppSettingsUpdate.model_validate({}))
