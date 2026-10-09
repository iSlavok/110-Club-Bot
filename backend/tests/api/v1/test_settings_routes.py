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
