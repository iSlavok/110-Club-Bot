from dishka import AsyncContainer, FromDishka
from loguru import logger

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


async def _reconcile_club(container: AsyncContainer, club_id: int) -> None:
    try:
        async with container() as scope:
            service = await scope.get(ChatAccessService)
            await service.reconcile_club(club_id)
    except Exception:  # noqa: BLE001 - one broken club must not stop the others; the traceback goes to the log
        logger.exception("Chat reconcile of club {} crashed", club_id)
