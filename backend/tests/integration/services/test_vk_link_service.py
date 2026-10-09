import pytest

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
from app.schemas import ClubAccess, VkAlreadyLinked, VkCandidate, VkLinkByProfile, VkLinkUnavailable
from app.services import VkLinkService
from tests.factories import make_block, make_club, make_membership, make_user, set_app_settings
from tests.providers import DEFAULT_NOW

VK_ID = 4242


@pytest.fixture
async def service(request_container) -> VkLinkService:
    return await request_container.get(VkLinkService)


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
