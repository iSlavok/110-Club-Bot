from urllib.parse import parse_qs, urlsplit

import pytest
from sqlalchemy import select

from app.models import User
from app.schemas import VkLinkByOAuth
from app.services import VkLinkService
from tests.factories import make_user
from tests.providers import BOT_USERNAME

VK_ID = 4242


@pytest.fixture
async def state(request_container, db_session) -> str:
    user = await make_user(db_session, tg_id=42)
    offer = await (await request_container.get(VkLinkService)).offer(user.tg_id)
    assert isinstance(offer, VkLinkByOAuth)
    return parse_qs(urlsplit(offer.authorize_url).query)["state"][0]


async def test_callback_links_and_redirects_to_the_bot(api_client, db_session, vk, state) -> None:
    vk.codes["code-1"] = VK_ID

    response = await api_client.get(
        "/api/v1/vk/callback",
        params={"code": "code-1", "state": state, "device_id": "device-1", "type": "code_v2"},
    )

    assert response.status_code == 302
    assert response.headers["location"] == f"https://t.me/{BOT_USERNAME}"
    user = await db_session.scalar(select(User).where(User.tg_id == 42))
    assert user.vk_id == VK_ID


async def test_cancelled_login_redirects_to_the_bot(api_client, state) -> None:
    response = await api_client.get(
        "/api/v1/vk/callback",
        params={"state": state, "error": "access_denied", "error_description": "User denied"},
    )

    assert response.status_code == 302


async def test_used_link_shows_expired_page(api_client, vk, state) -> None:
    vk.codes["code-1"] = VK_ID
    params = {"code": "code-1", "state": state, "device_id": "device-1"}
    await api_client.get("/api/v1/vk/callback", params=params)

    response = await api_client.get("/api/v1/vk/callback", params=params)

    assert response.status_code == 400
    assert response.headers["content-type"].startswith("text/html")
    assert "Ссылка устарела" in response.text


async def test_malformed_state_fails_validation(api_client) -> None:
    response = await api_client.get("/api/v1/vk/callback", params={"state": "<script>", "code": "x"})

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_FAILED"


async def test_callback_is_not_in_openapi(api_client) -> None:
    response = await api_client.get("/api/openapi.json")

    assert "/api/v1/vk/callback" not in response.json()["paths"]
