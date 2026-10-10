from datetime import UTC, datetime

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import ApproveChatJoinRequest, CreateChatInviteLink
from sqlalchemy import select

from app.enums import ChatAccessStatus
from app.models import ChatAccess
from app.services import ChatAccessService
from tests.factories import make_block, make_chat_access, make_club, make_membership, make_user
from tests.providers import DEFAULT_NOW, INVITE_LINK_PREFIX

CHAT_ID = -100500
VK_ID = 4242


@pytest.fixture
async def service(request_container) -> ChatAccessService:
    return await request_container.get(ChatAccessService)


@pytest.fixture
async def club(db_session):
    return await make_club(db_session, title="Химия", chat_id=CHAT_ID)


async def _access_row(db_session, user) -> ChatAccess | None:
    return await db_session.scalar(select(ChatAccess).where(ChatAccess.user_id == user.id))


async def test_access_comes_with_a_personal_join_link(service, db_session, club, bot) -> None:
    user = await make_user(db_session, vk_id=VK_ID)
    block = await make_block(db_session, club, title="Блок 5")
    await make_membership(db_session, block, vk_id=VK_ID)

    [access] = await service.access_for_user(user.id)
    again = await service.access_for_user(user.id)

    assert access.block_title == "Блок 5"
    assert not access.is_upcoming
    assert access.invite_link is not None
    assert access.invite_link.startswith(INVITE_LINK_PREFIX)
    assert again[0].invite_link == access.invite_link
    bot.create_chat_invite_link.assert_awaited_once_with(
        chat_id=CHAT_ID,
        name=f"user {user.id}",
        creates_join_request=True,
    )
    row = await _access_row(db_session, user)
    assert row is not None
    assert row.status is ChatAccessStatus.INVITED
    assert row.invited_at == DEFAULT_NOW


async def test_between_blocks_access_comes_from_the_next_block(service, db_session, club) -> None:
    user = await make_user(db_session, vk_id=VK_ID)
    await make_block(db_session, club, starts_at=datetime(2026, 7, 1, tzinfo=UTC))
    upcoming = await make_block(db_session, club, starts_at=datetime(2026, 10, 5, tzinfo=UTC))
    await make_membership(db_session, upcoming, vk_id=VK_ID)

    [access] = await service.access_for_user(user.id)

    assert access.is_upcoming
    assert access.block_starts_at == upcoming.starts_at


async def test_next_block_gives_no_access_while_a_block_runs(service, db_session, club, bot) -> None:
    user = await make_user(db_session, vk_id=VK_ID)
    await make_block(db_session, club, starts_at=datetime(2026, 9, 1, tzinfo=UTC))
    upcoming = await make_block(db_session, club, starts_at=datetime(2026, 10, 5, tzinfo=UTC))
    await make_membership(db_session, upcoming, vk_id=VK_ID)

    assert await service.access_for_user(user.id) == []
    bot.create_chat_invite_link.assert_not_awaited()


async def test_club_without_chat_gives_access_without_link(service, db_session) -> None:
    user = await make_user(db_session, vk_id=VK_ID)
    await make_membership(db_session, await make_block(db_session, await make_club(db_session)), vk_id=VK_ID)

    [access] = await service.access_for_user(user.id)

    assert access.invite_link is None
    assert await _access_row(db_session, user) is None


async def test_telegram_refusing_the_link_still_shows_access(service, db_session, club, bot) -> None:
    user = await make_user(db_session, vk_id=VK_ID)
    await make_membership(db_session, await make_block(db_session, club), vk_id=VK_ID)
    bot.create_chat_invite_link.side_effect = TelegramBadRequest(
        method=CreateChatInviteLink(chat_id=CHAT_ID),
        message="Bad Request: not enough rights",
    )

    [access] = await service.access_for_user(user.id)

    assert access.invite_link is None


async def test_kicked_student_back_in_a_block_is_unbanned_and_reinvited(service, db_session, club, bot) -> None:
    user = await make_user(db_session, vk_id=VK_ID)
    await make_membership(db_session, await make_block(db_session, club), vk_id=VK_ID)
    row = await make_chat_access(db_session, club, user, status=ChatAccessStatus.KICKED)

    [access] = await service.access_for_user(user.id)

    assert access.invite_link == row.invite_link
    bot.unban_chat_member.assert_awaited_once_with(chat_id=CHAT_ID, user_id=user.tg_id, only_if_banned=True)
    assert row.status is ChatAccessStatus.INVITED
    bot.create_chat_invite_link.assert_not_awaited()


async def test_club_moved_to_another_chat_gets_a_new_link(service, db_session, club) -> None:
    user = await make_user(db_session, vk_id=VK_ID)
    await make_membership(db_session, await make_block(db_session, club), vk_id=VK_ID)
    row = await make_chat_access(db_session, club, user, chat_id=CHAT_ID - 1)
    old_link = row.invite_link

    [access] = await service.access_for_user(user.id)

    assert access.invite_link != old_link
    assert row.chat_id == CHAT_ID
    assert row.status is ChatAccessStatus.INVITED


async def test_join_request_of_the_link_owner_with_access_is_approved(service, db_session, club, bot) -> None:
    user = await make_user(db_session, vk_id=VK_ID)
    await make_membership(db_session, await make_block(db_session, club), vk_id=VK_ID)
    row = await make_chat_access(db_session, club, user, status=ChatAccessStatus.INVITED)

    await service.handle_join_request(chat_id=CHAT_ID, tg_id=user.tg_id, invite_link=row.invite_link)

    bot.approve_chat_join_request.assert_awaited_once_with(chat_id=CHAT_ID, user_id=user.tg_id)
    assert row.status is ChatAccessStatus.JOINED
    assert row.joined_at == DEFAULT_NOW


async def test_join_request_through_someone_elses_link_is_left_to_admins(service, db_session, club, bot) -> None:
    user = await make_user(db_session, vk_id=VK_ID)
    await make_membership(db_session, await make_block(db_session, club), vk_id=VK_ID)
    row = await make_chat_access(db_session, club, user, status=ChatAccessStatus.INVITED)
    stranger = await make_user(db_session)

    await service.handle_join_request(chat_id=CHAT_ID, tg_id=stranger.tg_id, invite_link=row.invite_link)
    await service.handle_join_request(chat_id=CHAT_ID, tg_id=stranger.tg_id, invite_link="https://t.me/+admins")
    await service.handle_join_request(chat_id=CHAT_ID, tg_id=stranger.tg_id, invite_link=None)

    bot.approve_chat_join_request.assert_not_awaited()
    bot.decline_chat_join_request.assert_not_awaited()
    assert row.status is ChatAccessStatus.INVITED


async def test_join_request_without_access_is_left_to_admins(service, db_session, club, bot) -> None:
    user = await make_user(db_session, vk_id=VK_ID)
    await make_block(db_session, club)
    row = await make_chat_access(db_session, club, user, status=ChatAccessStatus.INVITED)

    await service.handle_join_request(chat_id=CHAT_ID, tg_id=user.tg_id, invite_link=row.invite_link)

    bot.approve_chat_join_request.assert_not_awaited()
    bot.decline_chat_join_request.assert_not_awaited()


async def test_failed_approval_keeps_the_student_invited(service, db_session, club, bot) -> None:
    user = await make_user(db_session, vk_id=VK_ID)
    await make_membership(db_session, await make_block(db_session, club), vk_id=VK_ID)
    row = await make_chat_access(db_session, club, user, status=ChatAccessStatus.INVITED)
    bot.approve_chat_join_request.side_effect = TelegramBadRequest(
        method=ApproveChatJoinRequest(chat_id=CHAT_ID, user_id=user.tg_id),
        message="Bad Request: HIDE_REQUESTER_MISSING",
    )

    await service.handle_join_request(chat_id=CHAT_ID, tg_id=user.tg_id, invite_link=row.invite_link)

    assert row.status is ChatAccessStatus.INVITED
