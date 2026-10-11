from unittest.mock import AsyncMock, MagicMock

import pytest

from app import texts
from app.enums import RemovalDecision, RemovalRequestStatus
from app.exceptions import PermissionDeniedError
from app.services import MembershipRemovalService
from app.telegram import RemovalRequestCallback
from bot.handlers.removal_requests import decide_removal
from tests.factories import make_block, make_club, make_membership, make_removal_request
from tests.providers import OWNER_TG_ID


def _callback(tg_id: int) -> AsyncMock:
    callback = AsyncMock()
    callback.from_user = MagicMock(id=tg_id, username=None, full_name="Владелец")
    return callback


async def test_owner_confirms_from_the_alert(request_container, db_session) -> None:
    block = await make_block(db_session, await make_club(db_session))
    await make_membership(db_session, block, vk_id=501)
    request = await make_removal_request(db_session, block, 501)
    callback = _callback(OWNER_TG_ID)
    data = RemovalRequestCallback(request_id=request.id, decision=RemovalDecision.CONFIRM)

    await decide_removal(callback, data, await request_container.get(MembershipRemovalService))

    assert request.status is RemovalRequestStatus.CONFIRMED
    assert request.decided_by_tg_id == OWNER_TG_ID
    callback.answer.assert_awaited_once_with("Удалены из блока.")


async def test_stranger_gets_a_readable_refusal(request_container, db_session) -> None:
    request = await make_removal_request(db_session, await make_block(db_session, await make_club(db_session)), 501)
    callback = _callback(1)
    data = RemovalRequestCallback(request_id=request.id, decision=RemovalDecision.REJECT)

    with pytest.raises(PermissionDeniedError) as error:
        await decide_removal(callback, data, await request_container.get(MembershipRemovalService))

    assert request.status is RemovalRequestStatus.PENDING
    callback.answer.assert_not_awaited()
    assert texts.errors.for_error(error.value) == "У тебя нет прав на это действие."
