from unittest.mock import MagicMock

from app.services import ChatAccessService
from bot.handlers.chat_service_messages import hide_service_message
from tests.factories import make_club

CHAT_ID = -100500


async def test_join_message_is_deleted_in_a_club_that_hides_them(request_container, db_session, bot) -> None:
    await make_club(db_session, chat_id=CHAT_ID, hide_service_messages=True)
    message = MagicMock()
    message.chat.id = CHAT_ID
    message.message_id = 17

    await hide_service_message(message, await request_container.get(ChatAccessService))

    bot.delete_message.assert_awaited_once_with(chat_id=CHAT_ID, message_id=17)
