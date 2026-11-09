from dishka import AsyncContainer, FromDishka
from loguru import logger

from app.enums import MessageDelivery
from app.services import ChatAccessService


# container is the app container, passed by the scheduler: every club is reconciled in its own scope (transaction),
# so a broken club rolls back alone. Catches block changes by date, which no sync or removal reports.
async def reconcile_chat_access(
    container: AsyncContainer,
    chat_access_service: FromDishka[ChatAccessService],
) -> None:
    club_ids = await chat_access_service.list_chat_club_ids()
    for club_id in club_ids:
        await _reconcile_club(container, club_id)
        await invite_students(container, club_id)


# Every invite is its own scope: a sent message stays recorded even if a later one crashes.
async def invite_students(container: AsyncContainer, club_id: int) -> None:
    try:
        async with container() as scope:
            service = await scope.get(ChatAccessService)
            user_ids = await service.list_invitees(club_id)
    except Exception:  # noqa: BLE001 - one broken club must not stop the others; the traceback goes to the log
        logger.exception("Listing chat invites of club {} crashed", club_id)
        return
    deliveries: dict[int, MessageDelivery] = {}
    for user_id in user_ids:
        delivery = await _invite(container, club_id, user_id)
        if delivery is not None:
            deliveries[user_id] = delivery
    try:
        async with container() as scope:
            service = await scope.get(ChatAccessService)
            await service.report_invites(club_id, deliveries)
    except Exception:  # noqa: BLE001 - the report must not stop the other clubs
        logger.exception("Reporting chat invites of club {} crashed", club_id)


async def _reconcile_club(container: AsyncContainer, club_id: int) -> None:
    try:
        async with container() as scope:
            service = await scope.get(ChatAccessService)
            await service.reconcile_club(club_id)
    except Exception:  # noqa: BLE001 - one broken club must not stop the others; the traceback goes to the log
        logger.exception("Chat reconcile of club {} crashed", club_id)


async def _invite(container: AsyncContainer, club_id: int, user_id: int) -> MessageDelivery | None:
    try:
        async with container() as scope:
            service = await scope.get(ChatAccessService)
            return await service.invite(club_id, user_id)
    except Exception:  # noqa: BLE001 - one broken invite must not stop the others; the traceback goes to the log
        logger.exception("Chat invite of user {} to club {} crashed", user_id, club_id)
        return MessageDelivery.FAILED
