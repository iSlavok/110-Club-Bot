from unittest.mock import AsyncMock, MagicMock

import pytest
from aiogram.enums import ChatType
from aiogram.types import EphemeralMessageParameters

from app import texts
from app.enums import Permission
from app.schemas import UserDTO
from app.services import BotAdminService, UserService
from bot.handlers import vk_lookup
from tests.factories import make_admin_user, make_role, make_user
from tests.providers import OWNER_TG_ID


def _reply(tg_id: int, *, is_bot: bool = False, topic_root: bool = False) -> MagicMock:
    return MagicMock(
        from_user=MagicMock(id=tg_id, full_name="Аня", is_bot=is_bot),
        forum_topic_created=MagicMock() if topic_root else None,
    )


def _message(tg_id: int, reply: MagicMock | None = None, chat_type: ChatType = ChatType.SUPERGROUP) -> AsyncMock:
    message = AsyncMock()
    message.from_user = MagicMock(id=tg_id)
    message.chat = MagicMock(type=chat_type)
    message.reply_to_message = reply
    return message


async def _passes_router_filters(message: AsyncMock, request_container) -> bool:
    passed, _ = await vk_lookup.router.message.check_root_filters(message, dishka_container=request_container)
    return passed


async def _answer(message: AsyncMock, request_container) -> str:
    await vk_lookup.vk_lookup(
        message,
        await request_container.get(BotAdminService),
        await request_container.get(UserService),
    )
    message.answer.assert_awaited_once()
    call = message.answer.await_args
    assert call.kwargs["ephemeral_message_parameters"] == EphemeralMessageParameters(
        receiver_user_id=message.from_user.id
    )
    return call.args[0]


async def test_only_admins_in_group_chats_pass_the_router_filters(request_container, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))
    disabled = await make_admin_user(db_session, await make_role(db_session), is_active=False)

    assert await _passes_router_filters(_message(admin.tg_id), request_container)
    assert await _passes_router_filters(_message(OWNER_TG_ID, chat_type=ChatType.GROUP), request_container)
    assert not await _passes_router_filters(_message(1), request_container)
    assert not await _passes_router_filters(_message(disabled.tg_id), request_container)
    assert not await _passes_router_filters(_message(OWNER_TG_ID, chat_type=ChatType.PRIVATE), request_container)


async def test_shows_the_linked_vk_of_the_student_replied_to(request_container, db_session) -> None:
    student = await make_user(db_session, vk_id=5005)

    text = await _answer(_message(OWNER_TG_ID, _reply(student.tg_id)), request_container)

    assert text == texts.vk_lookup.student_vk(student.tg_id, "Аня", UserDTO.from_orm_obj(student))


async def test_student_unknown_to_the_bot(request_container) -> None:
    text = await _answer(_message(OWNER_TG_ID, _reply(1)), request_container)

    assert text == texts.vk_lookup.student_vk(1, "Аня", None)


@pytest.mark.parametrize(
    "reply",
    [None, _reply(5, is_bot=True), _reply(5, topic_root=True)],
    ids=["no reply", "reply to a bot", "topic root"],
)
async def test_asks_to_reply_to_a_student(request_container, reply) -> None:
    assert await _answer(_message(OWNER_TG_ID, reply), request_container) == texts.vk_lookup.NO_TARGET


async def test_admin_without_users_view_is_refused(request_container, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session, Permission.CLUBS_VIEW))
    student = await make_user(db_session, vk_id=5005)

    text = await _answer(_message(admin.tg_id, _reply(student.tg_id)), request_container)

    assert text == texts.vk_lookup.NO_PERMISSION
