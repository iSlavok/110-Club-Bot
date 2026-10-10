from dishka import AsyncContainer, FromDishka
from loguru import logger

from app.services import ReminderDispatchService


# container is the app container, passed by the scheduler: every reminder is sent in its own scope (transaction),
# so a broken one rolls back alone and the rest still go out.
async def dispatch_reminders(
    container: AsyncContainer,
    reminder_dispatch_service: FromDishka[ReminderDispatchService],
) -> None:
    reminder_ids = await reminder_dispatch_service.list_due_ids()
    for reminder_id in reminder_ids:
        await _dispatch(container, reminder_id)


async def _dispatch(container: AsyncContainer, reminder_id: int) -> None:
    try:
        async with container() as scope:
            service = await scope.get(ReminderDispatchService)
            await service.dispatch(reminder_id)
    except Exception as error:  # noqa: BLE001 - one broken reminder must not stop the others; the traceback goes to the log
        logger.exception("Reminder {} crashed while sending", reminder_id)
        await _record_failure(container, reminder_id, repr(error))


async def _record_failure(container: AsyncContainer, reminder_id: int, error: str) -> None:
    try:
        async with container() as scope:
            service = await scope.get(ReminderDispatchService)
            await service.record_failure(reminder_id, error)
    except Exception:  # noqa: BLE001 - the loop over reminders must go on
        logger.exception("Cannot record the failure of reminder {}", reminder_id)
