import pytest
from aiogram.types import (
    BotCommandScopeAllPrivateChats,
    BotCommandScopeChat,
    BotCommandScopeChatMember,
    BotCommandScopeDefault,
)

from app.enums import Permission
from app.services import BotAdminService
from app.telegram import ADMIN_COMMANDS, CHAT_ADMIN_COMMANDS, DEFAULT_COMMANDS
from tests.factories import make_admin_user, make_club, make_role
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
    assert default_call.kwargs == {"scope": BotCommandScopeAllPrivateChats()}
    assert {call.kwargs["scope"].chat_id for call in admin_calls} == {admin.tg_id, OWNER_TG_ID}
    assert all(call.args == (list(ADMIN_COMMANDS),) for call in admin_calls)
    clear_default, *hidden_calls = bot.delete_my_commands.await_args_list
    assert clear_default.kwargs == {"scope": BotCommandScopeDefault()}
    assert {call.kwargs["scope"].chat_id for call in hidden_calls} == {disabled.tg_id, roleless.tg_id}


async def test_sync_command_menus_covers_active_club_chats(service, bot, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))
    disabled = await make_admin_user(db_session, await make_role(db_session), is_active=False)
    await make_club(db_session, chat_id=-100)
    await make_club(db_session, chat_id=-200, is_active=False)
    await make_club(db_session)

    await service.sync_command_menus()

    shown = [call for call in bot.set_my_commands.await_args_list if call.args == (list(CHAT_ADMIN_COMMANDS),)]
    assert [call.kwargs["scope"] for call in shown] == [
        BotCommandScopeChatMember(chat_id=-100, user_id=tg_id) for tg_id in sorted({admin.tg_id, OWNER_TG_ID})
    ]
    bot.delete_my_commands.assert_any_await(scope=BotCommandScopeChatMember(chat_id=-100, user_id=disabled.tg_id))


async def test_show_chat_menus_shows_the_vk_lookup_to_every_admin(service, bot, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))
    await make_admin_user(db_session, await make_role(db_session), is_active=False)

    await service.show_chat_menus(-100)

    scopes = [call.kwargs["scope"] for call in bot.set_my_commands.await_args_list]
    assert scopes == [
        BotCommandScopeChatMember(chat_id=-100, user_id=tg_id) for tg_id in sorted({admin.tg_id, OWNER_TG_ID})
    ]


async def test_has_permission(service, db_session) -> None:
    viewer = await make_admin_user(db_session, await make_role(db_session, Permission.USERS_VIEW))
    other = await make_admin_user(db_session, await make_role(db_session, Permission.CLUBS_VIEW))
    disabled = await make_admin_user(db_session, await make_role(db_session, Permission.USERS_VIEW), is_active=False)

    assert await service.has_permission(OWNER_TG_ID, Permission.USERS_VIEW)
    assert await service.has_permission(viewer.tg_id, Permission.USERS_VIEW)
    assert not await service.has_permission(other.tg_id, Permission.USERS_VIEW)
    assert not await service.has_permission(disabled.tg_id, Permission.USERS_VIEW)
    assert not await service.has_permission(1, Permission.USERS_VIEW)


async def test_sync_command_menus_keeps_a_disabled_owner_account(service, bot, db_session) -> None:
    await make_admin_user(db_session, tg_id=OWNER_TG_ID, is_active=False)

    await service.sync_command_menus()

    bot.set_my_commands.assert_awaited_with(list(ADMIN_COMMANDS), scope=BotCommandScopeChat(chat_id=OWNER_TG_ID))
    bot.delete_my_commands.assert_awaited_once_with(scope=BotCommandScopeDefault())


async def test_sync_command_menu_shows_the_menu_only_to_admins(service, bot, db_session) -> None:
    disabled = await make_admin_user(db_session, await make_role(db_session), is_active=False)

    await service.sync_command_menu(disabled.tg_id)
    await service.sync_command_menu(1)
    bot.set_my_commands.assert_not_awaited()

    await service.sync_command_menu(OWNER_TG_ID)
    bot.set_my_commands.assert_awaited_once_with(list(ADMIN_COMMANDS), scope=BotCommandScopeChat(chat_id=OWNER_TG_ID))
    bot.delete_my_commands.assert_not_awaited()
