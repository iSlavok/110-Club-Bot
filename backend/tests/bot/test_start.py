from unittest.mock import AsyncMock, MagicMock

from aiogram.types import BotCommandScopeChat, ChatMemberLeft
from aiogram.types import User as TelegramUser
from sqlalchemy import select

from app import texts
from app.enums import VkLinkMode
from app.models import User
from app.services import BotAdminService, StudentStatusService, UserService, VkLinkService
from app.telegram import ADMIN_COMMANDS
from bot.handlers.start import start
from bot.states import VkLinkStates
from tests.factories import make_block, make_club, make_membership, make_user, set_app_settings
from tests.providers import DEFAULT_NOW, OWNER_TG_ID


def _message(tg_id: int, full_name: str) -> AsyncMock:
    message = AsyncMock()
    message.from_user = MagicMock(id=tg_id, username="kate", full_name=full_name)
    return message


async def _start(message: AsyncMock, state, request_container) -> None:
    await start(
        message,
        state=state,
        user_service=await request_container.get(UserService),
        bot_admin_service=await request_container.get(BotAdminService),
        vk_link_service=await request_container.get(VkLinkService),
        student_status_service=await request_container.get(StudentStatusService),
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


async def test_start_of_a_linked_student_shows_the_status_with_the_join_button(
    request_container, db_session, state, bot
) -> None:
    user = await make_user(db_session, vk_id=4242, bot_blocked_at=DEFAULT_NOW)
    club = await make_club(db_session, title="Химия", chat_id=-100500)
    await make_membership(db_session, await make_block(db_session, club, title="5"), vk_id=4242)
    bot.get_chat_member.return_value = ChatMemberLeft(user=TelegramUser(id=user.tg_id, is_bot=False, first_name="S"))
    message = _message(tg_id=user.tg_id, full_name=user.full_name)

    await _start(message, state, request_container)

    [answer] = message.answer.await_args_list
    assert "<b>Клуб Химия, блок 5</b>" in answer.args[0]
    assert answer.kwargs["reply_markup"].inline_keyboard[0][0].text == "Вступить в чат клуба Химия"
    assert user.bot_blocked_at is None
