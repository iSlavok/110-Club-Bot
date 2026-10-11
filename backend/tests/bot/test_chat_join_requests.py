from unittest.mock import MagicMock

from app.enums import ChatAccessStatus
from app.services import ChatAccessService
from bot.handlers.chat_join_requests import join_request
from tests.factories import make_block, make_chat_access, make_club, make_membership, make_user

CHAT_ID = -100500
VK_ID = 4242


async def test_join_request_by_personal_link_is_approved(request_container, db_session, bot) -> None:
    club = await make_club(db_session, chat_id=CHAT_ID)
    user = await make_user(db_session, vk_id=VK_ID)
    await make_membership(db_session, await make_block(db_session, club), vk_id=VK_ID)
    row = await make_chat_access(db_session, club, user, status=ChatAccessStatus.INVITED)
    request = MagicMock()
    request.chat.id = CHAT_ID
    request.from_user.id = user.tg_id
    request.invite_link.invite_link = row.invite_link

    await join_request(request, await request_container.get(ChatAccessService))

    bot.approve_chat_join_request.assert_awaited_once_with(chat_id=CHAT_ID, user_id=user.tg_id)
    assert row.status is ChatAccessStatus.JOINED
