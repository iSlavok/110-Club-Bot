from unittest.mock import MagicMock

from aiogram.enums import ChatMemberStatus

from app.services import UserService
from bot.handlers.bot_blocking import bot_status_changed
from tests.factories import make_user
from tests.providers import DEFAULT_NOW


def _update(tg_id: int, status: ChatMemberStatus) -> MagicMock:
    update = MagicMock()
    update.from_user.id = tg_id
    update.new_chat_member.status = status
    return update


async def test_blocking_and_unblocking_the_bot_is_remembered(request_container, db_session) -> None:
    user = await make_user(db_session)
    service = await request_container.get(UserService)

    await bot_status_changed(_update(user.tg_id, ChatMemberStatus.KICKED), service)
    assert user.bot_blocked_at == DEFAULT_NOW

    await bot_status_changed(_update(user.tg_id, ChatMemberStatus.MEMBER), service)
    assert user.bot_blocked_at is None
