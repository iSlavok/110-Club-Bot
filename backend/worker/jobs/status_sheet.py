from dishka import AsyncContainer, FromDishka
from loguru import logger

from app.exceptions import AppError
from app.services import StatusSheetService


# container is the app container, passed by the scheduler: a club whose sheet fails must not stop the others.
async def publish_status_sheets(
    container: AsyncContainer, status_sheet_service: FromDishka[StatusSheetService]
) -> None:
    club_ids = await status_sheet_service.list_club_ids()
    for club_id in club_ids:
        await _publish_club(container, club_id)


async def _publish_club(container: AsyncContainer, club_id: int) -> None:
    try:
        async with container() as scope:
            service = await scope.get(StatusSheetService)
            await service.publish(club_id)
    except AppError as error:
        logger.warning("Status sheet of club {} skipped: {}", club_id, error.message)
    except Exception:  # noqa: BLE001 - one broken club must not stop the others; the traceback goes to the log
        logger.exception("Status sheet of club {} crashed", club_id)
