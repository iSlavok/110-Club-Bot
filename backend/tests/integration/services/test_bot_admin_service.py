import pytest
from aiogram.types import BotCommandScopeChat, BotCommandScopeDefault

from app.services import BotAdminService
from app.telegram import ADMIN_COMMANDS, DEFAULT_COMMANDS
from tests.factories import make_admin_user, make_role
from tests.providers import OWNER_TG_ID


@pytest.fixture
async def service(request_container) -> BotAdminService:
    return await request_container.get(BotAdminService)


async def test_owner_is_admin_without_an_account(service) -> None:
    assert await service.is_admin(OWNER_TG_ID)


async def test_active_admin_with_role_is_admin(service, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))

    assert await service.is_admin(admin.tg_id)


async def test_inactive_or_roleless_admin_and_stranger_are_not_admins(service, db_session) -> None:
    inactive = await make_admin_user(db_session, await make_role(db_session), is_active=False)
    roleless = await make_admin_user(db_session)

    assert not await service.is_admin(inactive.tg_id)
    assert not await service.is_admin(roleless.tg_id)
    assert not await service.is_admin(1)


async def test_sync_command_menus_shows_admins_and_hides_former_ones(service, bot, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))
    disabled = await make_admin_user(db_session, await make_role(db_session), is_active=False)
    roleless = await make_admin_user(db_session)

    await service.sync_command_menus()

    default_call, *admin_calls = bot.set_my_commands.await_args_list
    assert default_call.args == (list(DEFAULT_COMMANDS),)
    assert default_call.kwargs == {"scope": BotCommandScopeDefault()}
    assert {call.kwargs["scope"].chat_id for call in admin_calls} == {admin.tg_id, OWNER_TG_ID}
    assert all(call.args == (list(ADMIN_COMMANDS),) for call in admin_calls)
    hidden = {call.kwargs["scope"].chat_id for call in bot.delete_my_commands.await_args_list}
    assert hidden == {disabled.tg_id, roleless.tg_id}


async def test_sync_command_menus_keeps_a_disabled_owner_account(service, bot, db_session) -> None:
    await make_admin_user(db_session, tg_id=OWNER_TG_ID, is_active=False)

    await service.sync_command_menus()

    bot.set_my_commands.assert_awaited_with(list(ADMIN_COMMANDS), scope=BotCommandScopeChat(chat_id=OWNER_TG_ID))
    bot.delete_my_commands.assert_not_awaited()


async def test_sync_command_menu_shows_the_menu_only_to_admins(service, bot, db_session) -> None:
    disabled = await make_admin_user(db_session, await make_role(db_session), is_active=False)

    await service.sync_command_menu(disabled.tg_id)
    await service.sync_command_menu(1)
    bot.set_my_commands.assert_not_awaited()

    await service.sync_command_menu(OWNER_TG_ID)
    bot.set_my_commands.assert_awaited_once_with(list(ADMIN_COMMANDS), scope=BotCommandScopeChat(chat_id=OWNER_TG_ID))
    bot.delete_my_commands.assert_not_awaited()
