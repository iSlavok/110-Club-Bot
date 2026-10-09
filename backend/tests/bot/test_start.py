from unittest.mock import AsyncMock, MagicMock

from aiogram.types import BotCommandScopeChat
from sqlalchemy import select

from app.models import User
from app.services import BotAdminService, UserService
from app.telegram import ADMIN_COMMANDS
from bot.handlers.start import start
from tests.providers import OWNER_TG_ID


def _message(tg_id: int, full_name: str) -> AsyncMock:
    message = AsyncMock()
    message.from_user = MagicMock(id=tg_id, username="kate", full_name=full_name)
    return message


async def _start(message: AsyncMock, request_container) -> None:
    user_service = await request_container.get(UserService)
    bot_admin_service = await request_container.get(BotAdminService)
    await start(message, user_service, bot_admin_service)


async def test_start_registers_user_and_greets(request_container, db_session, bot) -> None:
    message = _message(tg_id=42, full_name="Катя Орлова")

    await _start(message, request_container)

    user = await db_session.scalar(select(User).where(User.tg_id == 42))
    assert user is not None
    assert user.tg_username == "kate"
    message.answer.assert_awaited_once()
    assert "Катя Орлова" in message.answer.await_args.args[0]
    bot.set_my_commands.assert_not_awaited()


async def test_start_shows_the_admin_menu_to_admins(request_container, bot) -> None:
    message = _message(tg_id=OWNER_TG_ID, full_name="Владелец")

    await _start(message, request_container)

    bot.set_my_commands.assert_awaited_once_with(list(ADMIN_COMMANDS), scope=BotCommandScopeChat(chat_id=OWNER_TG_ID))
    message.answer.assert_awaited_once()


async def test_start_ignores_messages_without_sender(request_container) -> None:
    message = AsyncMock()
    message.from_user = None

    await _start(message, request_container)

    message.answer.assert_not_awaited()
