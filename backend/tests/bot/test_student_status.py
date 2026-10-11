from unittest.mock import AsyncMock, MagicMock

from aiogram.types import ChatMemberLeft, InlineKeyboardMarkup
from aiogram.types import User as TelegramUser

from app.services import StudentStatusService
from bot.handlers.student_status import status
from tests.factories import make_block, make_club, make_membership, make_user

TG_ID = 42
VK_ID = 4242


async def test_status_shows_the_club_and_the_join_button(request_container, db_session, bot) -> None:
    await make_user(db_session, tg_id=TG_ID, vk_id=VK_ID)
    club = await make_club(db_session, title="Химия", chat_id=-100500)
    await make_membership(db_session, await make_block(db_session, club, title="5"), vk_id=VK_ID)
    bot.get_chat_member.return_value = ChatMemberLeft(user=TelegramUser(id=TG_ID, is_bot=False, first_name="S"))
    message = AsyncMock()
    message.from_user = MagicMock(id=TG_ID)

    await status(message, await request_container.get(StudentStatusService))

    text = message.answer.await_args.args[0]
    assert "<b>Клуб Химия, блок 5</b>" in text
    keyboard: InlineKeyboardMarkup = message.answer.await_args.kwargs["reply_markup"]
    assert keyboard.inline_keyboard[0][0].text == "Вступить в чат клуба Химия"
