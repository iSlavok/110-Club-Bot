from unittest.mock import AsyncMock, MagicMock

import pytest

from app.exceptions import AdminAccessDeniedError
from app.services import LoginService
from bot import texts
from bot.handlers.admin_login import login
from tests.factories import make_admin_user, make_role


def _message(tg_id: int) -> AsyncMock:
    message = AsyncMock()
    message.from_user = MagicMock(id=tg_id, username=None, full_name="Админ")
    return message


async def test_login_sends_code_to_admin(request_container, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))
    message = _message(admin.tg_id)

    await login(message, await request_container.get(LoginService))

    text = message.answer.await_args.args[0]
    assert "<code>" in text
    assert "12:05" in text


async def test_login_refuses_stranger_with_readable_error(request_container) -> None:
    message = _message(1)

    with pytest.raises(AdminAccessDeniedError) as error:
        await login(message, await request_container.get(LoginService))

    message.answer.assert_not_awaited()
    assert texts.errors.for_error(error.value) == "У тебя нет доступа к админке."
