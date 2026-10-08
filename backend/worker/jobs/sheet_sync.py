from dishka import AsyncContainer, FromDishka
from loguru import logger

from app.exceptions import AppError
from app.services import SheetSyncService


# container is the app container, passed by the scheduler: every club is synced in its own scope (transaction),
# so a broken club rolls back alone.
async def sync_sheets(container: AsyncContainer, sheet_sync_service: FromDishka[SheetSyncService]) -> None:
    club_ids = await sheet_sync_service.list_syncable_club_ids()
    for club_id in club_ids:
        await _sync_club(container, club_id)


async def purge_sheet_syncs(sheet_sync_service: FromDishka[SheetSyncService]) -> None:
    await sheet_sync_service.purge_old()


async def _sync_club(container: AsyncContainer, club_id: int) -> None:
    try:
        async with container() as scope:
            service = await scope.get(SheetSyncService)
            await service.sync_club(club_id)
    except AppError as error:
        logger.warning("Sheet sync of club {} skipped: {}", club_id, error.message)
    except Exception:  # noqa: BLE001 - one broken club must not stop the others; the traceback goes to the log
        logger.exception("Sheet sync of club {} crashed", club_id)
        await _record_crash(container, club_id)


async def _record_crash(container: AsyncContainer, club_id: int) -> None:
    try:
        async with container() as scope:
            service = await scope.get(SheetSyncService)
            await service.record_internal_error(club_id)
    except Exception:  # noqa: BLE001 - the loop over clubs must go on
        logger.exception("Cannot record the crashed sheet sync of club {}", club_id)
