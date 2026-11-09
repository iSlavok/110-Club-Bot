from unittest.mock import AsyncMock, MagicMock

from aiogram.types import ChatMemberMember
from aiogram.types import User as TelegramUser

from app import texts
from app.enums import ChatAccessStatus
from app.services import ChatAccessService
from app.telegram import KickApprovalCallback
from bot.handlers.kick_approvals import approve_kicks
from tests.factories import make_block, make_chat_access, make_club, make_membership, make_user
from tests.providers import OWNER_TG_ID


async def test_owner_approves_the_kicks_from_the_alert(request_container, db_session, bot) -> None:
    club = await make_club(db_session, chat_id=-100500)
    block = await make_block(db_session, club, kicks_approved_at=None)
    await make_membership(db_session, block, vk_id=1)
    access = await make_chat_access(db_session, club, await make_user(db_session, vk_id=2))
    bot.get_chat_member.return_value = ChatMemberMember(user=TelegramUser(id=1, is_bot=False, first_name="S"))
    callback = AsyncMock()
    callback.from_user = MagicMock(id=OWNER_TG_ID, username=None, full_name="Владелец")

    await approve_kicks(
        callback, KickApprovalCallback(block_id=block.id), await request_container.get(ChatAccessService)
    )

    assert access.status is ChatAccessStatus.KICKED
    callback.answer.assert_awaited_once_with(texts.alerts.KICKS_APPROVED_ANSWER)
