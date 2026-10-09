import pytest
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

from app.enums import VkLinkMode
from app.models import AppSettings
from app.models.app_settings import APP_SETTINGS_ID


async def test_migration_seeds_the_only_row_with_oauth_mode(db_session) -> None:
    settings = await db_session.get(AppSettings, APP_SETTINGS_ID)

    assert settings is not None
    assert settings.vk_link_mode is VkLinkMode.OAUTH


async def test_second_settings_row_is_rejected(db_session) -> None:
    with pytest.raises(IntegrityError, match="ck_app_settings_single_row"):
        await db_session.execute(text("INSERT INTO app_settings (id) VALUES (2)"))


async def test_migration_seeds_default_reminder_offsets(db_session) -> None:
    settings = await db_session.get(AppSettings, APP_SETTINGS_ID)

    assert settings is not None
    assert settings.default_lesson_offsets == [1440, 60, 0]
    assert settings.default_homework_offsets == [2880, 1440, 180]
