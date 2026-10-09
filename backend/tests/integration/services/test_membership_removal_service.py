import pytest
from sqlalchemy import select

from app.enums import Permission, RemovalDecision, RemovalRequestStatus
from app.exceptions import PermissionDeniedError, RemovalRequestDecidedError, RemovalRequestNotFoundError
from app.models import Block, MembershipRemovalItem, MembershipRemovalRequest
from app.repositories import MembershipRepository
from app.schemas import TelegramProfile
from app.services import MembershipRemovalService
from app.telegram import RemovalRequestCallback
from tests.factories import (
    make_admin_user,
    make_block,
    make_club,
    make_membership,
    make_removal_request,
    make_role,
    make_user,
)
from tests.providers import ALERT_MESSAGE_ID, ALERTS_CHAT_ID, DEFAULT_NOW, OWNER_TG_ID

OWNER = TelegramProfile(tg_id=OWNER_TG_ID, tg_username="owner", full_name="Владелец Клуба")


@pytest.fixture
async def service(request_container) -> MembershipRemovalService:
    return await request_container.get(MembershipRemovalService)


@pytest.fixture
async def block(db_session) -> Block:
    club = await make_club(db_session, title="Клуб 110")
    return await make_block(db_session, club, title="Блок 5")


@pytest.fixture
def members(request_container):
    async def vk_ids(block: Block) -> set[int]:
        repository = await request_container.get(MembershipRepository)
        return await repository.list_vk_ids(block.id)

    return vk_ids


async def _requests(db_session, block: Block) -> list[MembershipRemovalRequest]:
    statement = (
        select(MembershipRemovalRequest)
        .where(MembershipRemovalRequest.block_id == block.id)
        .order_by(MembershipRemovalRequest.id)
    )
    requests = await db_session.scalars(statement)
    return list(requests)


async def _items(db_session, request: MembershipRemovalRequest) -> set[int]:
    statement = select(MembershipRemovalItem.vk_id).where(MembershipRemovalItem.request_id == request.id)
    vk_ids = await db_session.scalars(statement)
    return set(vk_ids)


async def test_members_gone_from_sheet_are_asked_about(service, db_session, block, bot, members) -> None:
    await make_membership(db_session, block, vk_id=501)
    await make_membership(db_session, block, vk_id=502)
    await make_user(db_session, vk_id=501, full_name="Ученик Тестов", tg_username="pupil")

    requested = await service.reconcile_block(block.id, members={501, 502}, wanted=set())

    assert requested == 2
    assert await members(block) == {501, 502}
    [request] = await _requests(db_session, block)
    assert request.status is RemovalRequestStatus.PENDING
    assert request.alert_message_id == ALERT_MESSAGE_ID
    assert await _items(db_session, request) == {501, 502}
    chat_id, text = bot.send_message.await_args.args
    assert chat_id == ALERTS_CHAT_ID
    assert "Клуб 110 · Блок 5" in text
    assert "2 человека" in text
    assert "Ученик Тестов (@pupil)" in text
    buttons = bot.send_message.await_args.kwargs["reply_markup"].inline_keyboard[0]
    assert [RemovalRequestCallback.unpack(button.callback_data) for button in buttons] == [
        RemovalRequestCallback(request_id=request.id, decision=RemovalDecision.CONFIRM),
        RemovalRequestCallback(request_id=request.id, decision=RemovalDecision.REJECT),
    ]


async def test_members_still_in_sheet_are_not_asked_about(service, db_session, block, bot) -> None:
    requested = await service.reconcile_block(block.id, members={501}, wanted={501, 502})

    assert requested == 0
    assert await _requests(db_session, block) == []
    bot.send_message.assert_not_awaited()


async def test_open_request_is_not_repeated(service, db_session, block, bot) -> None:
    await make_removal_request(db_session, block, 501)

    requested = await service.reconcile_block(block.id, members={501, 502}, wanted=set())

    assert requested == 1
    first, second = await _requests(db_session, block)
    assert await _items(db_session, first) == {501}
    assert await _items(db_session, second) == {502}
    bot.send_message.assert_awaited_once()


async def test_member_back_in_sheet_leaves_the_request(service, db_session, block, bot) -> None:
    request = await make_removal_request(db_session, block, 501, 502, alert_message_id=77)

    await service.reconcile_block(block.id, members={501, 502}, wanted={501})

    assert request.status is RemovalRequestStatus.PENDING
    assert await _items(db_session, request) == {502}
    edit = bot.edit_message_text.await_args.kwargs
    assert edit["message_id"] == 77
    assert "1 человек" in edit["text"]
    assert edit["reply_markup"] is not None


async def test_request_is_cancelled_when_everyone_is_back(service, db_session, block, bot) -> None:
    request = await make_removal_request(db_session, block, 501, alert_message_id=77)

    await service.reconcile_block(block.id, members={501}, wanted={501})

    assert request.status is RemovalRequestStatus.CANCELLED
    edit = bot.edit_message_text.await_args.kwargs
    assert "Запрос отменён" in edit["text"]
    assert edit["reply_markup"] is None


async def test_rejected_member_is_asked_again_only_after_coming_back(service, db_session, block) -> None:
    rejected = await make_removal_request(db_session, block, 501, status=RemovalRequestStatus.REJECTED)

    still_gone = await service.reconcile_block(block.id, members={501}, wanted=set())
    back = await service.reconcile_block(block.id, members={501}, wanted={501})
    gone_again = await service.reconcile_block(block.id, members={501}, wanted=set())

    assert (still_gone, back, gone_again) == (0, 0, 1)
    assert await _items(db_session, rejected) == set()
    [_, new_request] = await _requests(db_session, block)
    assert await _items(db_session, new_request) == {501}


async def test_owner_confirms_the_removal(service, db_session, block, bot, members) -> None:
    await make_membership(db_session, block, vk_id=501)
    await make_membership(db_session, block, vk_id=502)
    request = await make_removal_request(db_session, block, 501, alert_message_id=77)

    status = await service.decide(request.id, RemovalDecision.CONFIRM, OWNER)

    assert status is RemovalRequestStatus.CONFIRMED
    assert await members(block) == {502}
    assert (request.decided_by_tg_id, request.decided_at) == (OWNER_TG_ID, DEFAULT_NOW)
    edit = bot.edit_message_text.await_args.kwargs
    assert "Удалены из блока — Владелец Клуба" in edit["text"]
    assert edit["reply_markup"] is None


async def test_rejected_members_stay_in_the_block(service, db_session, block, bot, members) -> None:
    await make_membership(db_session, block, vk_id=501)
    request = await make_removal_request(db_session, block, 501, alert_message_id=77)

    status = await service.decide(request.id, RemovalDecision.REJECT, OWNER)

    assert status is RemovalRequestStatus.REJECTED
    assert await members(block) == {501}
    assert "Остаются в блоке — Владелец Клуба" in bot.edit_message_text.await_args.kwargs["text"]


async def test_admin_with_sync_run_may_decide(service, db_session, block) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session, Permission.SYNC_RUN))
    request = await make_removal_request(db_session, block, 501)
    decider = TelegramProfile(tg_id=admin.tg_id, tg_username=None, full_name="Админ")

    status = await service.decide(request.id, RemovalDecision.REJECT, decider)

    assert status is RemovalRequestStatus.REJECTED


@pytest.mark.parametrize("kind", ["no_permission", "disabled", "stranger"])
async def test_others_may_not_decide(service, db_session, block, kind) -> None:
    role = await make_role(db_session, Permission.SYNC_RUN if kind == "disabled" else Permission.CLUBS_VIEW)
    admin = await make_admin_user(db_session, role, is_active=kind != "disabled")
    tg_id = 1 if kind == "stranger" else admin.tg_id
    request = await make_removal_request(db_session, block, 501)
    decider = TelegramProfile(tg_id=tg_id, tg_username=None, full_name="X")

    with pytest.raises(PermissionDeniedError):
        await service.decide(request.id, RemovalDecision.CONFIRM, decider)

    assert request.status is RemovalRequestStatus.PENDING


@pytest.mark.parametrize(
    "status",
    [RemovalRequestStatus.CONFIRMED, RemovalRequestStatus.REJECTED, RemovalRequestStatus.CANCELLED],
)
async def test_request_is_decided_once(service, db_session, block, status) -> None:
    request = await make_removal_request(db_session, block, 501, status=status)

    with pytest.raises(RemovalRequestDecidedError):
        await service.decide(request.id, RemovalDecision.CONFIRM, OWNER)


async def test_unknown_request(service) -> None:
    with pytest.raises(RemovalRequestNotFoundError):
        await service.decide(999_999, RemovalDecision.CONFIRM, OWNER)
