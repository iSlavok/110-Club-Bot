from unittest.mock import AsyncMock, MagicMock

from aiogram.types import BotCommandScopeChat
from sqlalchemy import select

from app import texts
from app.enums import VkLinkMode
from app.models import User
from app.services import BotAdminService, UserService, VkLinkService
from app.telegram import ADMIN_COMMANDS
from bot.handlers.start import start
from bot.states import VkLinkStates
from tests.factories import set_app_settings
from tests.providers import OWNER_TG_ID


def _message(tg_id: int, full_name: str) -> AsyncMock:
    message = AsyncMock()
    message.from_user = MagicMock(id=tg_id, username="kate", full_name=full_name)
    return message


async def _start(message: AsyncMock, state, request_container) -> None:
    await start(
        message,
        state,
        await request_container.get(UserService),
        await request_container.get(BotAdminService),
        await request_container.get(VkLinkService),
    )


async def test_start_registers_user_greets_and_offers_vk_link(request_container, db_session, state, bot) -> None:
    await set_app_settings(db_session, vk_link_mode=VkLinkMode.LINK)
    message = _message(tg_id=42, full_name="Катя <Орлова>")

    await _start(message, state, request_container)

    user = await db_session.scalar(select(User).where(User.tg_id == 42))
    assert user is not None
    assert user.tg_username == "kate"
    greeting, offer = (call.args[0] for call in message.answer.await_args_list)
    assert "Катя &lt;Орлова&gt;" in greeting
    assert offer == texts.vk_link.ASK_PROFILE_LINK
    assert await state.get_state() == VkLinkStates.waiting_for_profile.state
    bot.set_my_commands.assert_not_awaited()


async def test_start_shows_the_admin_menu_to_admins(request_container, state, bot) -> None:
    message = _message(tg_id=OWNER_TG_ID, full_name="Владелец")

    await _start(message, state, request_container)

    bot.set_my_commands.assert_awaited_once_with(list(ADMIN_COMMANDS), scope=BotCommandScopeChat(chat_id=OWNER_TG_ID))


async def test_start_ignores_messages_without_sender(request_container, state) -> None:
    message = AsyncMock()
    message.from_user = None

    await _start(message, state, request_container)

    message.answer.assert_not_awaited()
