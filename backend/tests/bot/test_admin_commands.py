from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

from aiogram.enums import ChatType

from app import texts
from app.config import PublicSettings
from app.services import LoginService, StatusService
from bot.handlers import admin_commands
from bot.handlers.admin_commands import adminka, login, status
from tests.factories import make_admin_user, make_block, make_club, make_role
from tests.providers import OWNER_TG_ID, PUBLIC_URL


def _message(tg_id: int, chat_type: ChatType = ChatType.PRIVATE) -> AsyncMock:
    message = AsyncMock()
    message.from_user = MagicMock(id=tg_id)
    message.chat = MagicMock(type=chat_type)
    return message


async def _passes_router_filters(message: AsyncMock, request_container) -> bool:
    passed, _ = await admin_commands.router.message.check_root_filters(message, dishka_container=request_container)
    return passed


async def test_admins_and_owners_pass_the_router_filters(request_container, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))

    assert await _passes_router_filters(_message(admin.tg_id), request_container)
    assert await _passes_router_filters(_message(OWNER_TG_ID), request_container)


async def test_non_admin_command_is_left_unhandled(request_container, db_session) -> None:
    disabled = await make_admin_user(db_session, await make_role(db_session), is_active=False)

    assert not await _passes_router_filters(_message(1), request_container)
    assert not await _passes_router_filters(_message(disabled.tg_id), request_container)


async def test_admin_commands_only_in_private_chat(request_container) -> None:
    message = _message(OWNER_TG_ID, chat_type=ChatType.SUPERGROUP)

    assert not await _passes_router_filters(message, request_container)


async def test_message_without_sender_is_left_unhandled(request_container) -> None:
    message = _message(OWNER_TG_ID)
    message.from_user = None

    assert not await _passes_router_filters(message, request_container)


async def test_login_sends_code_to_admin(request_container, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))
    message = _message(admin.tg_id)
    message.from_user = MagicMock(id=admin.tg_id, username=None, full_name="Админ")

    await login(message, await request_container.get(LoginService))

    text = message.answer.await_args.args[0]
    assert "<code>" in text
    assert "12:05" in text


async def test_adminka_replies_with_the_admin_panel_link(request_container) -> None:
    message = _message(OWNER_TG_ID)

    await adminka(message, await request_container.get(PublicSettings))

    assert PUBLIC_URL in message.answer.await_args.args[0]


async def test_adminka_without_configured_address() -> None:
    message = _message(OWNER_TG_ID)

    await adminka(message, PublicSettings(url=None))

    message.answer.assert_awaited_once_with(texts.auth.ADMIN_PANEL_URL_MISSING)


async def test_status_replies_with_active_clubs(request_container, db_session) -> None:
    club = await make_club(db_session, title="Химия")
    await make_block(db_session, club, title="Блок 5", starts_at=datetime(2026, 9, 1, tzinfo=UTC))
    message = _message(OWNER_TG_ID)

    await status(message, await request_container.get(StatusService))

    text = message.answer.await_args.args[0]
    assert "<b>Химия</b>" in text
    assert "Блок 5" in text
    assert "Участников: 0, из них в боте: 0" in text
    assert "Синков ещё не было." in text
