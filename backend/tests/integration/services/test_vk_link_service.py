from typing import TYPE_CHECKING, cast
from urllib.parse import parse_qs, urlsplit

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramForbiddenError, TelegramNetworkError
from aiogram.methods import GetMe, SendMessage
from sqlalchemy import select

from app import texts
from app.config import VkSettings
from app.enums import VkLinkMode
from app.exceptions import (
    InvalidVkLinkError,
    UserNotRegisteredError,
    VkAccountTakenError,
    VkAlreadyLinkedError,
    VkLinkModeChangedError,
    VkLinkUnavailableError,
    VkProfileNotFoundError,
    VkUnavailableError,
)
from app.models import VkAuthRequest
from app.schemas import ClubAccess, VkAlreadyLinked, VkCandidate, VkLinkByOAuth, VkLinkByProfile, VkLinkUnavailable
from app.services import VkLinkService
from app.services.vk_link_service import VK_AUTH_REQUEST_TTL
from app.utils import hash_secret, pkce_code_challenge
from tests.factories import make_block, make_club, make_membership, make_user, set_app_settings
from tests.providers import BOT_USERNAME, DEFAULT_NOW, PUBLIC_URL, VK_CLIENT_ID

if TYPE_CHECKING:
    from unittest.mock import AsyncMock

VK_ID = 4242
REDIRECT_URI = f"{PUBLIC_URL}/api/v1/vk/callback"


@pytest.fixture
async def service(request_container) -> VkLinkService:
    return await request_container.get(VkLinkService)


@pytest.fixture
async def bot(container) -> "AsyncMock":
    return cast("AsyncMock", await container.get(Bot))


@pytest.fixture
async def link_mode(db_session) -> None:
    await set_app_settings(db_session, vk_link_mode=VkLinkMode.LINK)


@pytest.fixture
async def kate(vk):
    return vk.add_user(VK_ID, "Катя", "Орлова", screen_name="kate.orlova")


async def test_linked_user_gets_access_status(service, db_session) -> None:
    user = await make_user(db_session, vk_id=VK_ID)
    block = await make_block(db_session, await make_club(db_session, title="Химия"), title="Блок 5")
    await make_membership(db_session, block, vk_id=VK_ID)

    offer = await service.offer(user.tg_id)

    assert offer == VkAlreadyLinked(vk_id=VK_ID, access=[ClubAccess(club_title="Химия", block_title="Блок 5")])


@pytest.mark.usefixtures("link_mode")
async def test_link_mode_asks_for_profile_link(service, db_session) -> None:
    user = await make_user(db_session)

    assert await service.offer(user.tg_id) == VkLinkByProfile()


@pytest.mark.usefixtures("link_mode")
async def test_unconfigured_mode_is_unavailable(service, db_session, container) -> None:
    (await container.get(VkSettings)).service_token = None
    user = await make_user(db_session)

    assert await service.offer(user.tg_id) == VkLinkUnavailable()


async def test_unknown_telegram_user_must_start_first(service) -> None:
    with pytest.raises(UserNotRegisteredError):
        await service.offer(1)


@pytest.mark.usefixtures("link_mode")
@pytest.mark.parametrize("text", ["https://vk.com/kate.orlova", "@Kate.Orlova", f"vk.com/id{VK_ID}", str(VK_ID)])
async def test_finds_candidate_by_link_or_id(service, db_session, kate, text) -> None:
    user = await make_user(db_session)

    candidate = await service.find_candidate(user.tg_id, text)

    assert candidate == VkCandidate(vk_id=kate.id, full_name="Катя Орлова")


@pytest.mark.usefixtures("link_mode")
async def test_candidate_is_not_linked_until_confirmed(service, db_session, kate) -> None:
    user = await make_user(db_session)

    await service.find_candidate(user.tg_id, "vk.com/kate.orlova")

    assert user.vk_id is None


@pytest.mark.usefixtures("link_mode")
async def test_garbage_is_not_a_link(service, db_session) -> None:
    user = await make_user(db_session)

    with pytest.raises(InvalidVkLinkError):
        await service.find_candidate(user.tg_id, "Привет, это я")


@pytest.mark.usefixtures("link_mode")
async def test_unknown_screen_name_is_not_found(service, db_session) -> None:
    user = await make_user(db_session)

    with pytest.raises(VkProfileNotFoundError):
        await service.find_candidate(user.tg_id, "vk.com/nobody")


@pytest.mark.usefixtures("link_mode")
async def test_unknown_id_is_not_found(service, db_session) -> None:
    user = await make_user(db_session)

    with pytest.raises(VkProfileNotFoundError):
        await service.find_candidate(user.tg_id, "vk.com/id999")


@pytest.mark.usefixtures("link_mode")
async def test_deleted_profile_is_not_found(service, db_session, vk) -> None:
    user = await make_user(db_session)
    vk.add_user(VK_ID, "DELETED", "", screen_name="gone", deactivated=True)

    with pytest.raises(VkProfileNotFoundError):
        await service.find_candidate(user.tg_id, "vk.com/gone")


@pytest.mark.usefixtures("link_mode")
async def test_community_link_is_not_found(service, db_session) -> None:
    user = await make_user(db_session)

    with pytest.raises(VkProfileNotFoundError):
        await service.find_candidate(user.tg_id, "vk.com/chemistry.club")


@pytest.mark.usefixtures("link_mode")
async def test_vk_outage_is_a_domain_error(service, db_session, vk) -> None:
    user = await make_user(db_session)
    vk.available = False

    with pytest.raises(VkUnavailableError):
        await service.find_candidate(user.tg_id, "vk.com/kate.orlova")


@pytest.mark.usefixtures("link_mode")
async def test_profile_of_another_telegram_is_refused_before_confirmation(service, db_session, kate) -> None:
    await make_user(db_session, vk_id=kate.id)
    user = await make_user(db_session)

    with pytest.raises(VkAccountTakenError):
        await service.find_candidate(user.tg_id, "vk.com/kate.orlova")


@pytest.mark.usefixtures("link_mode")
async def test_already_linked_user_cannot_pick_another_profile(service, db_session, kate) -> None:
    user = await make_user(db_session, vk_id=1)

    with pytest.raises(VkAlreadyLinkedError):
        await service.find_candidate(user.tg_id, "vk.com/kate.orlova")


async def test_profile_link_is_refused_in_oauth_mode(service, db_session, kate) -> None:
    user = await make_user(db_session)

    with pytest.raises(VkLinkModeChangedError):
        await service.find_candidate(user.tg_id, "vk.com/kate.orlova")


@pytest.mark.usefixtures("link_mode")
async def test_profile_link_needs_service_token(service, db_session, container, kate) -> None:
    (await container.get(VkSettings)).service_token = None
    user = await make_user(db_session)

    with pytest.raises(VkLinkUnavailableError):
        await service.find_candidate(user.tg_id, "vk.com/kate.orlova")


@pytest.mark.usefixtures("link_mode")
async def test_confirmation_links_vk_and_reports_access(service, db_session, kate) -> None:
    user = await make_user(db_session)
    block = await make_block(db_session, await make_club(db_session, title="Химия"), title="Блок 5")
    await make_membership(db_session, block, vk_id=kate.id)

    result = await service.confirm_candidate(user.tg_id, kate.id)

    assert result.vk_id == kate.id
    assert result.access == [ClubAccess(club_title="Химия", block_title="Блок 5")]
    assert user.vk_id == kate.id
    assert user.vk_linked_at == DEFAULT_NOW


@pytest.mark.usefixtures("link_mode")
async def test_confirmation_without_membership_reports_no_access(service, db_session, kate) -> None:
    user = await make_user(db_session)

    result = await service.confirm_candidate(user.tg_id, kate.id)

    assert result.access == []


@pytest.mark.usefixtures("link_mode")
async def test_link_is_final(service, db_session, kate) -> None:
    user = await make_user(db_session)
    await service.confirm_candidate(user.tg_id, kate.id)

    with pytest.raises(VkAlreadyLinkedError):
        await service.confirm_candidate(user.tg_id, 777)
    assert user.vk_id == kate.id


@pytest.mark.usefixtures("link_mode")
async def test_confirmation_refuses_profile_taken_meanwhile(service, db_session, kate) -> None:
    user = await make_user(db_session)
    await make_user(db_session, vk_id=kate.id)

    with pytest.raises(VkAccountTakenError):
        await service.confirm_candidate(user.tg_id, kate.id)
    assert user.vk_id is None


def _query(offer: VkLinkByOAuth) -> dict[str, str]:
    parts = urlsplit(offer.authorize_url)
    assert f"{parts.scheme}://{parts.netloc}{parts.path}" == "https://id.vk.ru/authorize"
    return {key: values[0] for key, values in parse_qs(parts.query).items()}


async def _offer(service: VkLinkService, tg_id: int) -> VkLinkByOAuth:
    offer = await service.offer(tg_id)
    assert isinstance(offer, VkLinkByOAuth)
    return offer


def _sent_text(bot: "AsyncMock") -> str:
    bot.send_message.assert_awaited_once()
    return bot.send_message.await_args.args[1]


async def test_offer_builds_vk_id_authorize_url_with_pkce(service, db_session) -> None:
    user = await make_user(db_session)

    offer = await _offer(service, user.tg_id)

    query = _query(offer)
    assert query["response_type"] == "code"
    assert query["client_id"] == str(VK_CLIENT_ID)
    assert query["redirect_uri"] == REDIRECT_URI
    assert query["code_challenge_method"] == "S256"
    assert query["scope"] == "vkid.personal_info"
    assert offer.expires_at == DEFAULT_NOW + VK_AUTH_REQUEST_TTL
    request = await db_session.scalar(select(VkAuthRequest).where(VkAuthRequest.user_id == user.id))
    assert request.state_hash == hash_secret(query["state"])
    assert query["code_challenge"] == pkce_code_challenge(request.code_verifier)


async def test_oauth_needs_app_id(service, db_session, container) -> None:
    (await container.get(VkSettings)).client_id = None
    user = await make_user(db_session)

    assert await service.offer(user.tg_id) == VkLinkUnavailable()


async def test_callback_links_vk_and_writes_to_the_student(service, db_session, vk, bot) -> None:
    user = await make_user(db_session)
    block = await make_block(db_session, await make_club(db_session, title="Химия"), title="Блок 5")
    await make_membership(db_session, block, vk_id=VK_ID)
    state = _query(await _offer(service, user.tg_id))["state"]
    vk.codes["code-1"] = VK_ID

    completion = await service.complete_oauth(state=state, code="code-1", device_id="device-1", error=None)

    assert not completion.is_expired
    assert completion.bot_username == BOT_USERNAME
    assert user.vk_id == VK_ID
    assert user.vk_linked_at == DEFAULT_NOW
    exchange = vk.exchanges[0]
    assert exchange["device_id"] == "device-1"
    assert exchange["state"] == state
    assert exchange["redirect_uri"] == REDIRECT_URI
    assert bot.send_message.await_args.args[0] == user.tg_id
    text = _sent_text(bot)
    assert text.startswith(texts.vk_link.LINKED)
    assert "Ты в клубе Химия, блок Блок 5." in text


async def test_state_works_once(service, db_session, vk) -> None:
    user = await make_user(db_session)
    state = _query(await _offer(service, user.tg_id))["state"]
    vk.codes["code-1"] = VK_ID
    await service.complete_oauth(state=state, code="code-1", device_id="device-1", error=None)

    again = await service.complete_oauth(state=state, code="code-1", device_id="device-1", error=None)

    assert again.is_expired


async def test_expired_state_does_nothing(service, db_session, vk, clock, bot) -> None:
    user = await make_user(db_session)
    state = _query(await _offer(service, user.tg_id))["state"]
    vk.codes["code-1"] = VK_ID
    clock.set(DEFAULT_NOW + VK_AUTH_REQUEST_TTL)

    completion = await service.complete_oauth(state=state, code="code-1", device_id="device-1", error=None)

    assert completion.is_expired
    assert user.vk_id is None
    assert vk.exchanges == []
    bot.send_message.assert_not_awaited()


async def test_unknown_state_is_expired(service) -> None:
    completion = await service.complete_oauth(state="forged", code="code-1", device_id="device-1", error=None)

    assert completion.is_expired


async def test_new_offer_replaces_the_previous_one(service, db_session, vk) -> None:
    user = await make_user(db_session)
    first = _query(await _offer(service, user.tg_id))["state"]
    second = _query(await _offer(service, user.tg_id))["state"]
    vk.codes["code-1"] = VK_ID

    assert (await service.complete_oauth(state=first, code="code-1", device_id="d", error=None)).is_expired
    assert not (await service.complete_oauth(state=second, code="code-1", device_id="d", error=None)).is_expired


async def test_cancelled_login_is_reported(service, db_session, vk, bot) -> None:
    user = await make_user(db_session)
    state = _query(await _offer(service, user.tg_id))["state"]

    completion = await service.complete_oauth(state=state, code=None, device_id=None, error="access_denied")

    assert not completion.is_expired
    assert user.vk_id is None
    assert vk.exchanges == []
    assert _sent_text(bot) == texts.vk_link.OAUTH_CANCELLED


async def test_rejected_code_is_reported(service, db_session, bot) -> None:
    user = await make_user(db_session)
    state = _query(await _offer(service, user.tg_id))["state"]

    await service.complete_oauth(state=state, code="unknown", device_id="device-1", error=None)

    assert user.vk_id is None
    assert "Не получилось подтвердить вход через VK" in _sent_text(bot)


async def test_vk_taken_by_another_telegram_is_refused(service, db_session, vk, bot) -> None:
    await make_user(db_session, vk_id=VK_ID)
    user = await make_user(db_session)
    state = _query(await _offer(service, user.tg_id))["state"]
    vk.codes["code-1"] = VK_ID

    await service.complete_oauth(state=state, code="code-1", device_id="device-1", error=None)

    assert user.vk_id is None
    assert _sent_text(bot) == "Этот VK уже привязан к другому Telegram. Напиши куратору."


async def test_link_made_meanwhile_is_kept(service, db_session, vk, bot) -> None:
    user = await make_user(db_session)
    state = _query(await _offer(service, user.tg_id))["state"]
    user.vk_id = 1
    vk.codes["code-1"] = VK_ID

    await service.complete_oauth(state=state, code="code-1", device_id="device-1", error=None)

    assert user.vk_id == 1
    assert vk.exchanges == []
    assert "Изменить привязку нельзя" in _sent_text(bot)


async def test_unreachable_telegram_still_completes(service, db_session, vk, bot) -> None:
    bot.me.side_effect = TelegramNetworkError(method=GetMe(), message="timeout")
    user = await make_user(db_session)
    state = _query(await _offer(service, user.tg_id))["state"]
    vk.codes["code-1"] = VK_ID

    completion = await service.complete_oauth(state=state, code="code-1", device_id="device-1", error=None)

    assert completion.bot_username is None
    assert user.vk_id == VK_ID


async def test_service_token_is_not_needed_for_oauth(service, db_session, container) -> None:
    (await container.get(VkSettings)).service_token = None
    user = await make_user(db_session)

    assert isinstance(await service.offer(user.tg_id), VkLinkByOAuth)


async def test_blocked_bot_does_not_undo_the_link(service, db_session, vk, bot) -> None:
    bot.send_message.side_effect = TelegramForbiddenError(
        method=SendMessage(chat_id=1, text="x"),
        message="bot was blocked by the user",
    )
    user = await make_user(db_session)
    state = _query(await _offer(service, user.tg_id))["state"]
    vk.codes["code-1"] = VK_ID

    completion = await service.complete_oauth(state=state, code="code-1", device_id="device-1", error=None)

    assert completion.bot_username == BOT_USERNAME
    assert user.vk_id == VK_ID
