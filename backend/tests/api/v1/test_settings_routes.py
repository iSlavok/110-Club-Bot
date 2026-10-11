import pytest

from app.config import VkSettings
from app.enums import Permission
from tests.factories import make_admin_user, make_role


async def test_any_admin_reads_settings(api_client, login_as, db_session) -> None:
    await login_as(await make_admin_user(db_session, await make_role(db_session)))

    response = await api_client.get("/api/v1/settings")

    assert response.status_code == 200
    body = response.json()
    assert body["vk_link_mode"] == "oauth"
    assert body["configured_vk_link_modes"] == ["link", "oauth"]


async def test_settings_require_login(api_client) -> None:
    response = await api_client.get("/api/v1/settings")

    assert response.status_code == 401
    assert response.json()["code"] == "NOT_AUTHENTICATED"


async def test_editor_switches_vk_link_mode(api_client, login_as, db_session) -> None:
    await login_as(await make_admin_user(db_session, await make_role(db_session, Permission.SETTINGS_EDIT)))

    response = await api_client.patch("/api/v1/settings", json={"vk_link_mode": "link"})

    assert response.status_code == 200
    assert response.json()["vk_link_mode"] == "link"


async def test_switching_needs_permission(api_client, login_as, db_session) -> None:
    await login_as(await make_admin_user(db_session, await make_role(db_session)))

    response = await api_client.patch("/api/v1/settings", json={"vk_link_mode": "link"})

    assert response.status_code == 403
    assert response.json()["code"] == "PERMISSION_DENIED"


async def test_unconfigured_mode_is_rejected(api_client, login_as, db_session, container) -> None:
    (await container.get(VkSettings)).service_token = None
    await login_as(await make_admin_user(db_session, await make_role(db_session, Permission.SETTINGS_EDIT)))

    response = await api_client.patch("/api/v1/settings", json={"vk_link_mode": "link"})

    assert response.status_code == 400
    assert response.json()["code"] == "VK_LINK_MODE_NOT_CONFIGURED"


async def test_unknown_mode_fails_validation(api_client, login_as, db_session) -> None:
    await login_as(await make_admin_user(db_session, await make_role(db_session, Permission.SETTINGS_EDIT)))

    response = await api_client.patch("/api/v1/settings", json={"vk_link_mode": "sms"})

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_FAILED"


async def test_settings_include_default_reminder_offsets(api_client, login_as, db_session) -> None:
    await login_as(await make_admin_user(db_session, await make_role(db_session)))

    response = await api_client.get("/api/v1/settings")

    body = response.json()
    assert body["default_lesson_offsets"] == [1440, 60, 0]
    assert body["default_homework_offsets"] == [2880, 1440, 180]


async def test_editor_changes_default_reminder_offsets(api_client, login_as, db_session) -> None:
    await login_as(await make_admin_user(db_session, await make_role(db_session, Permission.SETTINGS_EDIT)))

    response = await api_client.patch("/api/v1/settings", json={"default_lesson_offsets": [60, 1440]})

    assert response.status_code == 200
    assert response.json()["default_lesson_offsets"] == [1440, 60]


@pytest.mark.parametrize(
    "offsets",
    [[60, 60], [-1], [43201], list(range(11))],
    ids=["duplicate", "negative", "over-30-days", "too-many"],
)
async def test_invalid_default_offsets_fail_validation(api_client, login_as, db_session, offsets) -> None:
    await login_as(await make_admin_user(db_session, await make_role(db_session, Permission.SETTINGS_EDIT)))

    response = await api_client.patch("/api/v1/settings", json={"default_homework_offsets": offsets})

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_FAILED"
