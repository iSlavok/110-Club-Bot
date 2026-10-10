import pytest
from aiogram.types import ChatMemberMember
from aiogram.types import User as TelegramUser

from app.exceptions import UserNotRegisteredError
from app.services import StudentStatusService
from tests.factories import make_block, make_club, make_membership, make_user

TG_ID = 42
VK_ID = 4242


@pytest.fixture
async def service(request_container) -> StudentStatusService:
    return await request_container.get(StudentStatusService)


async def test_unregistered_user_is_sent_to_start(service) -> None:
    with pytest.raises(UserNotRegisteredError):
        await service.build(TG_ID)


async def test_unlinked_user_has_no_vk_and_no_clubs(service, db_session) -> None:
    await make_user(db_session, tg_id=TG_ID)

    status = await service.build(TG_ID)

    assert (status.vk_id, status.clubs) == (None, [])


async def test_linked_user_gets_vk_and_clubs(service, db_session, bot) -> None:
    await make_user(db_session, tg_id=TG_ID, vk_id=VK_ID)
    club = await make_club(db_session, title="Химия", chat_id=-100500)
    await make_membership(db_session, await make_block(db_session, club), vk_id=VK_ID)
    bot.get_chat_member.return_value = ChatMemberMember(user=TelegramUser(id=TG_ID, is_bot=False, first_name="S"))

    status = await service.build(TG_ID)

    assert status.vk_id == VK_ID
    assert [club_status.access.club_title for club_status in status.clubs] == ["Химия"]
