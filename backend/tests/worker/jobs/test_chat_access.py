import pytest
from aiogram.types import ChatMemberMember
from aiogram.types import User as TelegramUser
from sqlalchemy import select

from app.enums import ChatAccessStatus
from app.models import ChatAccess
from app.services import ChatAccessService
from tests.factories import make_block, make_chat_access, make_club, make_membership, make_user
from worker.jobs import reconcile_chat_access

CHAT_ID = -100500


@pytest.fixture
async def service(request_container) -> ChatAccessService:
    return await request_container.get(ChatAccessService)


async def _statuses(db_session) -> dict[int, ChatAccessStatus]:
    rows = await db_session.scalars(select(ChatAccess))
    return {row.user_id: row.status for row in rows}


async def test_invites_and_kicks_in_every_club_with_a_chat(container, service, db_session, bot) -> None:
    club = await make_club(db_session, title="Химия", chat_id=CHAT_ID)
    block = await make_block(db_session, club)
    await make_membership(db_session, block, vk_id=1)
    new = await make_user(db_session, vk_id=1)
    gone = await make_user(db_session, vk_id=2)
    await make_chat_access(db_session, club, gone)
    await make_club(db_session, chat_id=CHAT_ID - 1, is_active=False)
    bot.get_chat_member.return_value = ChatMemberMember(user=TelegramUser(id=gone.tg_id, is_bot=False, first_name="S"))

    await reconcile_chat_access(container, service)

    assert await _statuses(db_session) == {new.id: ChatAccessStatus.INVITED, gone.id: ChatAccessStatus.KICKED}
    bot.ban_chat_member.assert_awaited_once_with(chat_id=CHAT_ID, user_id=gone.tg_id)


async def test_crashed_club_does_not_stop_the_others(container, service, db_session, bot) -> None:
    broken = await make_club(db_session, chat_id=CHAT_ID)
    healthy = await make_club(db_session, chat_id=CHAT_ID - 1)
    for vk_id, club in enumerate((broken, healthy), start=2):
        await make_membership(db_session, await make_block(db_session, club), vk_id=1)
        await make_chat_access(db_session, club, await make_user(db_session, vk_id=vk_id))

    def chat_member(chat_id: int, user_id: int) -> ChatMemberMember:
        if chat_id == CHAT_ID:
            raise RuntimeError("bug")
        return ChatMemberMember(user=TelegramUser(id=user_id, is_bot=False, first_name="S"))

    bot.get_chat_member.side_effect = chat_member

    await reconcile_chat_access(container, service)

    statuses = {row.club_id: row.status for row in await db_session.scalars(select(ChatAccess))}
    assert statuses == {broken.id: ChatAccessStatus.JOINED, healthy.id: ChatAccessStatus.KICKED}
