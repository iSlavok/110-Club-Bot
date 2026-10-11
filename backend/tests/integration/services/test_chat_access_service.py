from datetime import UTC, datetime

import pytest
from aiogram.exceptions import TelegramBadRequest
from aiogram.methods import (
    ApproveChatJoinRequest,
    BanChatMember,
    CreateChatInviteLink,
    DeleteMessage,
    GetChatMember,
    UnbanChatMember,
)
from aiogram.types import ChatMemberAdministrator, ChatMemberLeft, ChatMemberMember, ChatMemberRestricted
from aiogram.types import User as TelegramUser
from sqlalchemy import select

from app import texts
from app.enums import ChatAccessStatus
from app.models import ChatAccess, User
from app.schemas import KickedMember
from app.services import ChatAccessService
from tests.factories import make_block, make_chat_access, make_club, make_membership, make_user
from tests.providers import ALERTS_CHAT_ID, DEFAULT_NOW, INVITE_LINK_PREFIX

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
    block = await make_block(db_session, club, title="5")
    await make_membership(db_session, block, vk_id=VK_ID)

    [access] = await service.access_for_user(user.id)
    again = await service.access_for_user(user.id)

    assert access.block_title == "5"
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

    assert access.block_title == upcoming.title


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


def _alerts(bot) -> list[str]:
    return [call.args[1] for call in bot.send_message.await_args_list if call.args[0] == ALERTS_CHAT_ID]


def _direct_messages(bot, tg_id: int) -> list[str]:
    return [call.args[1] for call in bot.send_message.await_args_list if call.args[0] == tg_id]


def _tg_user(tg_id: int) -> TelegramUser:
    return TelegramUser(id=tg_id, is_bot=False, first_name="Student")


async def _joined(db_session, club, vk_id: int, **overrides) -> tuple[ChatAccess, User]:
    user = await make_user(db_session, vk_id=vk_id, **overrides)
    access = await make_chat_access(db_session, club, user)
    return access, user


async def _statuses(db_session) -> dict[int, ChatAccessStatus]:
    rows = await db_session.scalars(select(ChatAccess))
    return {row.user_id: row.status for row in rows}


def _in_chat(bot) -> None:
    bot.get_chat_member.side_effect = lambda **kwargs: ChatMemberMember(user=_tg_user(kwargs["user_id"]))


async def test_reconcile_invites_new_members_and_kicks_those_out_of_the_block(service, db_session, club, bot) -> None:
    block = await make_block(db_session, club)
    await make_membership(db_session, block, vk_id=1)
    await make_membership(db_session, block, vk_id=2)
    new = await make_user(db_session, vk_id=1)
    _, stays = await _joined(db_session, club, 2)
    _, gone = await _joined(db_session, club, 3)
    _in_chat(bot)

    await service.reconcile_club(club.id)

    assert await _statuses(db_session) == {
        new.id: ChatAccessStatus.INVITED,
        stays.id: ChatAccessStatus.JOINED,
        gone.id: ChatAccessStatus.KICKED,
    }


async def test_unfilled_access_block_holds_kicks_and_alerts_once(service, db_session, club, bot) -> None:
    block = await make_block(db_session, club, title="6")
    access, _ = await _joined(db_session, club, 3)
    _in_chat(bot)

    await service.reconcile_club(club.id)
    await service.reconcile_club(club.id)

    assert access.status is ChatAccessStatus.JOINED
    assert club.chat_kicks_on_hold
    assert _alerts(bot) == [texts.alerts.chat_kicks_on_hold("Химия", "6", 1)]

    await make_membership(db_session, block, vk_id=1)
    await service.reconcile_club(club.id)

    assert access.status is ChatAccessStatus.KICKED
    assert not club.chat_kicks_on_hold
    assert texts.alerts.chat_kicks_resumed("Химия") in _alerts(bot)


async def test_club_without_any_next_block_holds_kicks(service, db_session, club, bot) -> None:
    await make_block(db_session, club, starts_at=datetime(2026, 6, 1, tzinfo=UTC))
    await _joined(db_session, club, 3)

    await service.reconcile_club(club.id)

    bot.get_chat_member.assert_not_awaited()
    assert _alerts(bot) == [texts.alerts.chat_kicks_on_hold("Химия", None, 1)]


async def test_empty_block_without_anyone_to_kick_is_not_alerted(service, db_session, club, bot) -> None:
    await make_block(db_session, club)

    await service.reconcile_club(club.id)

    assert not club.chat_kicks_on_hold
    assert _alerts(bot) == []


async def test_invite_sends_the_join_button_once(service, db_session, club, bot) -> None:
    user = await make_user(db_session, vk_id=VK_ID)
    await make_membership(db_session, await make_block(db_session, club, title="5"), vk_id=VK_ID)

    await service.reconcile_club(club.id)
    await service.reconcile_club(club.id)

    [message] = bot.send_message.await_args_list
    assert message.args[0] == user.tg_id
    assert message.args[1].startswith("Ты в клубе Химия, блок 5.")
    assert message.kwargs["reply_markup"].inline_keyboard[0][0].text == "Вступить в чат клуба Химия"


@pytest.fixture
async def filled_block(db_session, club):
    block = await make_block(db_session, club)
    await make_membership(db_session, block, vk_id=1)
    return block


@pytest.mark.usefixtures("filled_block")
async def test_kick_bans_and_unbans_and_tells_the_student(service, db_session, club, bot) -> None:
    access, user = await _joined(db_session, club, VK_ID, full_name="Катя Орлова", tg_username="kate")
    _in_chat(bot)

    await service.reconcile_club(club.id)

    bot.ban_chat_member.assert_awaited_once_with(chat_id=CHAT_ID, user_id=user.tg_id)
    bot.unban_chat_member.assert_awaited_once_with(chat_id=CHAT_ID, user_id=user.tg_id, only_if_banned=True)
    assert access.status is ChatAccessStatus.KICKED
    assert access.kicked_at == DEFAULT_NOW
    assert _direct_messages(bot, user.tg_id) == [texts.chat_access.kicked("Химия")]
    kicked = [KickedMember(vk_id=VK_ID, full_name="Катя Орлова", tg_username="kate")]
    assert _alerts(bot) == [texts.alerts.chat_kicked("Химия", kicked)]


@pytest.mark.usefixtures("filled_block")
@pytest.mark.parametrize(
    "member",
    [
        ChatMemberLeft(user=_tg_user(1)),
        ChatMemberRestricted.model_construct(status="restricted", user=_tg_user(1), is_member=False),
        ChatMemberAdministrator.model_construct(status="administrator", user=_tg_user(1)),
    ],
)
async def test_student_out_of_the_chat_or_made_admin_is_left_alone(service, db_session, club, bot, member) -> None:
    access, _ = await _joined(db_session, club, VK_ID)
    bot.get_chat_member.return_value = member

    await service.reconcile_club(club.id)

    bot.ban_chat_member.assert_not_awaited()
    bot.send_message.assert_not_awaited()
    assert access.status is ChatAccessStatus.LEFT


@pytest.mark.usefixtures("filled_block")
async def test_failed_ban_skips_the_student_and_alerts_once(service, db_session, club, bot) -> None:
    broken, broken_user = await _joined(db_session, club, VK_ID)
    healthy, _ = await _joined(db_session, club, VK_ID + 1)
    _in_chat(bot)

    async def ban(chat_id: int, user_id: int) -> bool:
        if user_id == broken_user.tg_id:
            raise TelegramBadRequest(method=BanChatMember(chat_id=chat_id, user_id=user_id), message="no rights")
        return True

    bot.ban_chat_member.side_effect = ban

    await service.reconcile_club(club.id)
    await service.reconcile_club(club.id)

    assert broken.status is ChatAccessStatus.JOINED
    assert healthy.status is ChatAccessStatus.KICKED
    assert club.chat_error == "Telegram server says - no rights"
    assert _alerts(bot).count(texts.alerts.chat_failed("Химия", "Telegram server says - no rights")) == 1

    bot.ban_chat_member.side_effect = None
    await service.reconcile_club(club.id)

    assert broken.status is ChatAccessStatus.KICKED
    assert club.chat_error is None
    assert _alerts(bot)[-1] == texts.alerts.chat_recovered("Химия")


@pytest.mark.usefixtures("filled_block")
async def test_failed_unban_still_counts_as_kicked(service, db_session, club, bot) -> None:
    access, user = await _joined(db_session, club, VK_ID)
    _in_chat(bot)
    bot.unban_chat_member.side_effect = TelegramBadRequest(
        method=UnbanChatMember(chat_id=CHAT_ID, user_id=user.tg_id),
        message="Bad Request: method is available only for supergroups",
    )

    await service.reconcile_club(club.id)

    assert access.status is ChatAccessStatus.KICKED
    assert club.chat_error is None


async def test_failed_invite_link_is_alerted_and_others_still_invited(service, db_session, club, bot) -> None:
    block = await make_block(db_session, club)
    for vk_id in (1, 2):
        await make_membership(db_session, block, vk_id=vk_id)
    first = await make_user(db_session, vk_id=1)
    second = await make_user(db_session, vk_id=2)
    create = bot.create_chat_invite_link.side_effect

    async def create_link(**kwargs: object):
        if kwargs["name"] == f"user {first.id}":
            raise TelegramBadRequest(method=CreateChatInviteLink(chat_id=CHAT_ID), message="not enough rights")
        return await create(**kwargs)

    bot.create_chat_invite_link.side_effect = create_link

    await service.reconcile_club(club.id)

    assert await _statuses(db_session) == {second.id: ChatAccessStatus.INVITED}
    assert club.chat_error == "Telegram server says - not enough rights"


async def test_service_message_is_deleted_when_the_club_hides_them(service, db_session, bot) -> None:
    await make_club(db_session, chat_id=CHAT_ID, hide_service_messages=True)

    await service.hide_service_message(chat_id=CHAT_ID, message_id=17)

    bot.delete_message.assert_awaited_once_with(chat_id=CHAT_ID, message_id=17)


async def test_service_message_stays_by_default_and_in_unknown_chats(service, club, bot) -> None:
    await service.hide_service_message(chat_id=CHAT_ID, message_id=17)
    await service.hide_service_message(chat_id=CHAT_ID - 1, message_id=17)

    bot.delete_message.assert_not_awaited()


async def test_failed_deletion_is_only_logged(service, db_session, bot) -> None:
    await make_club(db_session, chat_id=CHAT_ID, hide_service_messages=True)
    bot.delete_message.side_effect = TelegramBadRequest(
        method=DeleteMessage(chat_id=CHAT_ID, message_id=17),
        message="Bad Request: message can't be deleted",
    )

    await service.hide_service_message(chat_id=CHAT_ID, message_id=17)


async def test_student_in_the_chat_gets_no_join_link(service, db_session, club, bot) -> None:
    user = await make_user(db_session, vk_id=VK_ID)
    block = await make_block(db_session, club, title="5")
    await make_membership(db_session, block, vk_id=VK_ID)
    bot.get_chat_member.return_value = ChatMemberMember(user=_tg_user(user.tg_id))

    [status] = await service.student_clubs(user.id)

    assert status.in_chat is True
    assert status.access.block_title == "5"
    assert status.access.invite_link is None
    bot.get_chat_member.assert_awaited_once_with(chat_id=CHAT_ID, user_id=user.tg_id)
    bot.create_chat_invite_link.assert_not_awaited()


@pytest.mark.parametrize("telegram_fails", [False, True])
async def test_student_out_of_the_chat_gets_a_join_link(service, db_session, club, bot, telegram_fails) -> None:
    user = await make_user(db_session, vk_id=VK_ID)
    await make_membership(db_session, await make_block(db_session, club), vk_id=VK_ID)
    if telegram_fails:
        method = GetChatMember(chat_id=CHAT_ID, user_id=user.tg_id)
        bot.get_chat_member.side_effect = TelegramBadRequest(method=method, message="Bad Request: chat not found")
    else:
        bot.get_chat_member.return_value = ChatMemberLeft(user=_tg_user(user.tg_id))

    [status] = await service.student_clubs(user.id)

    assert status.in_chat is False
    assert status.access.invite_link is not None
    assert status.access.invite_link.startswith(INVITE_LINK_PREFIX)


async def test_club_without_chat_has_no_chat_state(service, db_session, bot) -> None:
    user = await make_user(db_session, vk_id=VK_ID)
    club = await make_club(db_session)
    await make_membership(db_session, await make_block(db_session, club), vk_id=VK_ID)

    [status] = await service.student_clubs(user.id)

    assert status.in_chat is None
    assert status.access.invite_link is None
    bot.get_chat_member.assert_not_awaited()


async def test_student_listed_for_the_next_block_is_told_so(service, db_session, club) -> None:
    user = await make_user(db_session, vk_id=VK_ID)
    running = await make_block(db_session, club, starts_at=datetime(2026, 9, 1, tzinfo=UTC))
    following = await make_block(db_session, club, title="6", starts_at=datetime(2026, 10, 31, tzinfo=UTC))
    await make_membership(db_session, running, vk_id=VK_ID)
    await make_membership(db_session, following, vk_id=VK_ID)
    other = await make_user(db_session, vk_id=VK_ID + 1)
    await make_membership(db_session, running, vk_id=VK_ID + 1)

    [status] = await service.student_clubs(user.id)
    [other_status] = await service.student_clubs(other.id)

    assert status.next_block_title == "6"
    assert other_status.next_block_title is None


async def test_upcoming_access_block_has_no_next_block(service, db_session, club) -> None:
    user = await make_user(db_session, vk_id=VK_ID)
    upcoming = await make_block(db_session, club, starts_at=datetime(2026, 10, 5, tzinfo=UTC))
    following = await make_block(db_session, club, starts_at=datetime(2026, 12, 5, tzinfo=UTC))
    await make_membership(db_session, upcoming, vk_id=VK_ID)
    await make_membership(db_session, following, vk_id=VK_ID)

    [status] = await service.student_clubs(user.id)

    assert status.next_block_title is None


async def test_unlinked_student_or_one_without_access_has_no_clubs(service, db_session, club) -> None:
    unlinked = await make_user(db_session)
    outsider = await make_user(db_session, vk_id=VK_ID)
    await make_block(db_session, club)

    assert await service.student_clubs(unlinked.id) == []
    assert await service.student_clubs(outsider.id) == []
