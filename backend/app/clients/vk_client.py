from dataclasses import dataclass
from typing import Any, Protocol

import httpx

from app.clients.exceptions import VkClientError
from app.config import VkSettings

VK_API_URL = "https://api.vk.ru/method"
VK_API_VERSION = "5.199"
VK_ID_AUTHORIZE_URL = "https://id.vk.ru/authorize"
VK_ID_CODE_EXCHANGE_URL = "https://id.vk.ru/oauth2/auth"
# users.get answers "Invalid user id" for an id nobody has.
VK_INVALID_USER_ID_ERROR = 113


@dataclass(frozen=True, slots=True)
class VkUser:
    id: int
    first_name: str
    last_name: str
    is_deactivated: bool


class VkClient(Protocol):
    async def get_user(self, user_ref: int | str) -> VkUser | None: ...

    async def exchange_code(
        self,
        *,
        code: str,
        code_verifier: str,
        device_id: str,
        state: str,
        redirect_uri: str,
    ) -> int: ...


class HttpxVkClient:
    def __init__(self, http: httpx.AsyncClient, settings: VkSettings) -> None:
        self._http = http
        self._settings = settings

    # users.get takes an id or a screen name; utils.resolveScreenName is closed to VK ID app service tokens
    # (error 1051). A community or unknown screen name comes back as an empty list.
    async def get_user(self, user_ref: int | str) -> VkUser | None:
        try:
            users = await self._call_method("users.get", {"user_ids": str(user_ref), "lang": "ru"})
        except VkClientError as error:
            if error.api_code == VK_INVALID_USER_ID_ERROR:
                return None
            raise
        if not users:
            return None
        try:
            user = users[0]
            return VkUser(
                id=int(user["id"]),
                first_name=str(user["first_name"]),
                last_name=str(user["last_name"]),
                is_deactivated="deactivated" in user,
            )
        except (KeyError, TypeError, ValueError, IndexError) as error:
            raise VkClientError(f"Unexpected users.get response: {users!r}") from error

    # https://id.vk.ru/about/business/go/docs/ru/vkid/latest/vk-id/connection/api-integration/api-description
    async def exchange_code(
        self,
        *,
        code: str,
        code_verifier: str,
        device_id: str,
        state: str,
        redirect_uri: str,
    ) -> int:
        if self._settings.client_id is None:
            raise VkClientError("VK_CLIENT_ID is not set")
        payload = await self._post(
            VK_ID_CODE_EXCHANGE_URL,
            {
                "grant_type": "authorization_code",
                "code": code,
                "code_verifier": code_verifier,
                "client_id": str(self._settings.client_id),
                "device_id": device_id,
                "redirect_uri": redirect_uri,
                "state": state,
            },
        )
        if "error" in payload:
            raise VkClientError(f"VK ID refused the code: {payload['error']} {payload.get('error_description', '')}")
        try:
            return int(payload["user_id"])
        except (KeyError, TypeError, ValueError) as error:
            raise VkClientError("VK ID token response has no user_id") from error

    async def _call_method(self, method: str, params: dict[str, str]) -> Any:  # noqa: ANN401 - VK returns any JSON
        if self._settings.service_token is None:
            raise VkClientError("VK_SERVICE_TOKEN is not set")
        payload = await self._post(
            f"{VK_API_URL}/{method}",
            {**params, "access_token": self._settings.service_token.get_secret_value(), "v": VK_API_VERSION},
        )
        if "error" in payload:
            error = payload["error"]
            code = error.get("error_code") if isinstance(error, dict) else None
            message = error.get("error_msg") if isinstance(error, dict) else error
            raise VkClientError(f"VK API {method} failed: {message}", api_code=code)
        if "response" not in payload:
            raise VkClientError(f"VK API {method} returned neither response nor error")
        return payload["response"]

    # Form POST, not GET: tokens stay out of URLs and proxy logs.
    async def _post(self, url: str, data: dict[str, str]) -> dict[str, Any]:
        try:
            response = await self._http.post(url, data=data)
            payload = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise VkClientError(f"VK request to {url} failed: {error!r}") from error
        if not isinstance(payload, dict):
            raise VkClientError(f"VK returned a non-object JSON from {url}")
        return payload
