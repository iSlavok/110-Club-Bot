import pytest
from pydantic import SecretStr

from app.config import PublicSettings, VkSettings
from app.enums import VkLinkMode
from app.services import VkLinkAvailability

CLIENT_ID = 5100001
PUBLIC_URL = "https://club.example.test"


def _availability(
    *,
    client_id: int | None = None,
    service_token: str | None = None,
    public_url: str | None = None,
) -> VkLinkAvailability:
    return VkLinkAvailability(
        VkSettings(
            client_id=client_id,
            service_token=SecretStr(service_token) if service_token is not None else None,
        ),
        PublicSettings(url=public_url),
    )


def test_nothing_is_configured_by_default() -> None:
    assert _availability().configured_modes() == []


def test_link_mode_needs_only_the_service_token() -> None:
    assert _availability(service_token="token").configured_modes() == [VkLinkMode.LINK]


@pytest.mark.parametrize(
    ("client_id", "public_url", "configured"),
    [
        (CLIENT_ID, PUBLIC_URL, True),
        (CLIENT_ID, None, False),
        (None, PUBLIC_URL, False),
    ],
)
def test_oauth_mode_needs_app_id_and_public_url(
    client_id: int | None, public_url: str | None, configured: bool
) -> None:
    availability = _availability(client_id=client_id, public_url=public_url)

    assert availability.is_configured(VkLinkMode.OAUTH) is configured
