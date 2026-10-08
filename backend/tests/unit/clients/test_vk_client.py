from collections.abc import AsyncIterator, Callable
from urllib.parse import parse_qs

import httpx
import pytest
from pydantic import SecretStr

from app.clients import HttpxVkClient, VkClientError, VkUser
from app.config import VkSettings

type Responder = Callable[[httpx.Request], httpx.Response]

SETTINGS = VkSettings(client_id=5100001, service_token=SecretStr("service-token"))


class Recorder:
    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []
        self.responder: Responder = lambda _: httpx.Response(200, json={"response": []})

    def handle(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        return self.responder(request)

    def form(self, index: int = -1) -> dict[str, str]:
        return {key: values[0] for key, values in parse_qs(self.requests[index].content.decode()).items()}


@pytest.fixture
def recorder() -> Recorder:
    return Recorder()


@pytest.fixture
async def client(recorder: Recorder) -> AsyncIterator[HttpxVkClient]:
    async with httpx.AsyncClient(transport=httpx.MockTransport(recorder.handle)) as http:
        yield HttpxVkClient(http, SETTINGS)


async def test_gets_user_by_screen_name_with_service_token(client, recorder) -> None:
    recorder.responder = lambda _: httpx.Response(
        200,
        json={"response": [{"id": 42, "first_name": "Катя", "last_name": "Орлова"}]},
    )

    user = await client.get_user("kate.orlova")

    assert user == VkUser(id=42, first_name="Катя", last_name="Орлова", is_deactivated=False)
    request = recorder.requests[0]
    assert request.method == "POST"
    assert str(request.url) == "https://api.vk.ru/method/users.get"
    assert recorder.form() == {"user_ids": "kate.orlova", "lang": "ru", "access_token": "service-token", "v": "5.199"}


async def test_community_or_unknown_screen_name_is_none(client, recorder) -> None:
    recorder.responder = lambda _: httpx.Response(200, json={"response": []})

    assert await client.get_user("chemistry.club") is None


async def test_gets_user_profile(client, recorder) -> None:
    recorder.responder = lambda _: httpx.Response(
        200,
        json={"response": [{"id": 42, "first_name": "Катя", "last_name": "Орлова", "can_access_closed": True}]},
    )

    user = await client.get_user(42)

    assert user == VkUser(id=42, first_name="Катя", last_name="Орлова", is_deactivated=False)
    assert recorder.form()["user_ids"] == "42"


async def test_deleted_profile_is_marked_deactivated(client, recorder) -> None:
    recorder.responder = lambda _: httpx.Response(
        200,
        json={"response": [{"id": 42, "first_name": "DELETED", "last_name": "", "deactivated": "deleted"}]},
    )

    user = await client.get_user(42)

    assert user is not None
    assert user.is_deactivated


async def test_invalid_user_id_is_none(client, recorder) -> None:
    recorder.responder = lambda _: httpx.Response(
        200,
        json={"error": {"error_code": 113, "error_msg": "Invalid user id"}},
    )

    assert await client.get_user(999) is None


async def test_api_error_is_a_client_error(client, recorder) -> None:
    recorder.responder = lambda _: httpx.Response(
        200,
        json={"error": {"error_code": 5, "error_msg": "User authorization failed"}},
    )

    with pytest.raises(VkClientError) as error:
        await client.get_user("kate")

    assert error.value.api_code == 5


async def test_network_failure_is_a_client_error(client, recorder) -> None:
    def fail(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("connection refused", request=request)

    recorder.responder = fail

    with pytest.raises(VkClientError):
        await client.get_user(42)


async def test_non_json_answer_is_a_client_error(client, recorder) -> None:
    recorder.responder = lambda _: httpx.Response(502, text="<html>Bad Gateway</html>")

    with pytest.raises(VkClientError):
        await client.get_user(42)


async def test_exchanges_code_for_vk_user_id(client, recorder) -> None:
    recorder.responder = lambda _: httpx.Response(
        200,
        json={"access_token": "token", "token_type": "Bearer", "user_id": 42, "state": "state-1"},
    )

    user_id = await client.exchange_code(
        code="code-1",
        code_verifier="verifier-1",
        device_id="device-1",
        state="state-1",
        redirect_uri="https://club.example.test/api/v1/vk/callback",
    )

    assert user_id == 42
    assert str(recorder.requests[0].url) == "https://id.vk.ru/oauth2/auth"
    assert recorder.form() == {
        "grant_type": "authorization_code",
        "code": "code-1",
        "code_verifier": "verifier-1",
        "client_id": "5100001",
        "device_id": "device-1",
        "redirect_uri": "https://club.example.test/api/v1/vk/callback",
        "state": "state-1",
    }


async def test_missing_credentials_fail_without_a_request(recorder) -> None:
    async with httpx.AsyncClient(transport=httpx.MockTransport(recorder.handle)) as http:
        client = HttpxVkClient(http, VkSettings())

        with pytest.raises(VkClientError, match="VK_SERVICE_TOKEN"):
            await client.get_user(42)
        with pytest.raises(VkClientError, match="VK_CLIENT_ID"):
            await client.exchange_code(
                code="code",
                code_verifier="verifier",
                device_id="device",
                state="state",
                redirect_uri="https://club.example.test/api/v1/vk/callback",
            )

    assert recorder.requests == []


async def test_rejected_code_is_a_client_error(client, recorder) -> None:
    recorder.responder = lambda _: httpx.Response(
        400,
        json={"error": "invalid_grant", "error_description": "code is expired"},
    )

    with pytest.raises(VkClientError, match="invalid_grant"):
        await client.exchange_code(
            code="old",
            code_verifier="verifier",
            device_id="device",
            state="state",
            redirect_uri="https://club.example.test/api/v1/vk/callback",
        )
