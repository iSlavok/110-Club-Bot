import pytest

from api.core.auth import SESSION_COOKIE
from app.enums import Permission
from app.schemas import TelegramProfile
from app.services import LoginService
from tests.factories import make_admin_user, make_role
from tests.providers import BOT_USERNAME


@pytest.fixture
async def admin(db_session):
    return await make_admin_user(db_session, await make_role(db_session, Permission.USERS_VIEW, Permission.CLUBS_VIEW))


async def _issue_code(request_container, tg_id: int) -> str:
    service = await request_container.get(LoginService)
    issued = await service.issue_code(TelegramProfile(tg_id=tg_id, tg_username=None, full_name="Admin"))
    return issued.code


async def test_config(api_client) -> None:
    response = await api_client.get("/api/v1/auth/config")

    assert response.status_code == 200
    assert response.json() == {"widget_enabled": True, "bot_username": BOT_USERNAME}


async def test_code_login_sets_http_only_cookie(api_client, request_container, admin) -> None:
    code = await _issue_code(request_container, admin.tg_id)

    response = await api_client.post("/api/v1/auth/code", json={"code": code})

    assert response.status_code == 200
    assert response.json() == {
        "id": admin.id,
        "tg_id": admin.tg_id,
        "name": admin.name,
        "is_owner": False,
        "permissions": ["clubs.view", "users.view"],
    }
    cookie = response.headers["set-cookie"]
    assert cookie.startswith(f"{SESSION_COOKIE}=")
    assert "HttpOnly" in cookie
    assert "Path=/api" in cookie
    assert "SameSite=lax" in cookie


async def test_wrong_code(api_client) -> None:
    response = await api_client.post("/api/v1/auth/code", json={"code": "000000"})

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_LOGIN_CODE"


async def test_malformed_code(api_client) -> None:
    response = await api_client.post("/api/v1/auth/code", json={"code": "12ab"})

    assert response.status_code == 422
    assert response.json()["fields"][0]["loc"] == ["body", "code"]


async def test_me_requires_session(api_client) -> None:
    response = await api_client.get("/api/v1/auth/me")

    assert response.status_code == 401
    assert response.json()["code"] == "NOT_AUTHENTICATED"


async def test_me_after_login_and_logout(api_client, request_container, admin) -> None:
    code = await _issue_code(request_container, admin.tg_id)
    await api_client.post("/api/v1/auth/code", json={"code": code})

    me = await api_client.get("/api/v1/auth/me")
    logout = await api_client.post("/api/v1/auth/logout")
    after = await api_client.get("/api/v1/auth/me")

    assert me.status_code == 200
    assert me.json()["id"] == admin.id
    assert logout.status_code == 204
    assert after.status_code == 401


async def test_widget_with_bad_signature(api_client, admin) -> None:
    payload = {"id": admin.tg_id, "first_name": "A", "auth_date": 1, "hash": "0" * 64}

    response = await api_client.post("/api/v1/auth/widget", json=payload)

    assert response.status_code == 400
    assert response.json()["code"] == "INVALID_WIDGET_DATA"
