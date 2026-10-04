from unittest.mock import AsyncMock, MagicMock

from sqlalchemy import select

from app.models import User
from app.services import UserService
from bot.handlers.start import start


def _message(tg_id: int, full_name: str) -> AsyncMock:
    message = AsyncMock()
    message.from_user = MagicMock(id=tg_id, username="kate", full_name=full_name)
    return message


async def test_start_registers_user_and_greets(request_container, db_session) -> None:
    message = _message(tg_id=42, full_name="Катя Орлова")

    await start(message, await request_container.get(UserService))

    user = await db_session.scalar(select(User).where(User.tg_id == 42))
    assert user is not None
    assert user.tg_username == "kate"
    message.answer.assert_awaited_once()
    assert "Катя Орлова" in message.answer.await_args.args[0]


async def test_start_ignores_messages_without_sender(request_container) -> None:
    message = AsyncMock()
    message.from_user = None

    await start(message, await request_container.get(UserService))

    message.answer.assert_not_awaited()
