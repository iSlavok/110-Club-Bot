from aiogram.types import BotCommandScopeChat, BotCommandScopeDefault

from app.telegram import ADMIN_COMMANDS, DEFAULT_COMMANDS
from bot.startup import sync_command_menus
from tests.factories import make_admin_user, make_role
from tests.providers import OWNER_TG_ID


async def test_startup_syncs_command_menus(container, db_session, bot) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))
    disabled = await make_admin_user(db_session, await make_role(db_session), is_active=False)

    await sync_command_menus(container)

    bot.set_my_commands.assert_any_await(list(DEFAULT_COMMANDS), scope=BotCommandScopeDefault())
    bot.set_my_commands.assert_any_await(list(ADMIN_COMMANDS), scope=BotCommandScopeChat(chat_id=OWNER_TG_ID))
    bot.set_my_commands.assert_any_await(list(ADMIN_COMMANDS), scope=BotCommandScopeChat(chat_id=admin.tg_id))
    bot.delete_my_commands.assert_awaited_once_with(scope=BotCommandScopeChat(chat_id=disabled.tg_id))
