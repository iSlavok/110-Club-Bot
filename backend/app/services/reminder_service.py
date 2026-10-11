from app import texts
from app.enums import ReminderKind, ReminderStatus, ReminderView
from app.exceptions import (
    ClubNotFoundError,
    ReminderNotFoundError,
    ReminderNotPendingError,
    ReminderPreviewUnavailableError,
)
from app.repositories import ClubRepository, ReminderRepository
from app.schemas import PageParams, Paginated, ReminderWithLessonDTO
from app.utils import Clock

HOMEWORK_DEADLINE_KINDS = frozenset({ReminderKind.HOMEWORK_DEADLINE, ReminderKind.HOMEWORK_DEADLINE_CHANGED})


class ReminderService:
    def __init__(
        self,
        reminder_repository: ReminderRepository,
        club_repository: ClubRepository,
        clock: Clock,
    ) -> None:
        self._reminder_repository = reminder_repository
        self._club_repository = club_repository
        self._clock = clock

    async def list_page(
        self,
        club_id: int,
        page: PageParams,
        *,
        view: ReminderView,
        include_cancelled: bool,
        lesson_id: int | None = None,
    ) -> Paginated[ReminderWithLessonDTO]:
        if await self._club_repository.get_by_id(club_id) is None:
            raise ClubNotFoundError(club_id)
        reminders = await self._reminder_repository.list_page_for_club(
            club_id=club_id,
            view=view,
            include_cancelled=include_cancelled,
            lesson_id=lesson_id,
            now=self._clock.now(),
            limit=page.per_page,
            offset=page.offset,
        )
        items = [ReminderWithLessonDTO.from_orm_obj_with_lesson(reminder) for reminder in reminders.items]
        return Paginated(items=items, total=reminders.total)

    # Rendered for the moment it went or will go out, so "через час" reads as it does in the chat.
    async def preview(self, reminder_id: int) -> str:
        reminder = await self._reminder_repository.get_with_lesson(reminder_id)
        if reminder is None:
            raise ReminderNotFoundError(reminder_id)
        if reminder.kind in HOMEWORK_DEADLINE_KINDS and reminder.lesson.homework_deadline_at is None:
            raise ReminderPreviewUnavailableError
        if reminder.sent_at is not None:
            moment = reminder.sent_at
        elif reminder.status == ReminderStatus.PENDING:
            moment = max(reminder.send_at, self._clock.now())
        else:
            moment = reminder.send_at
        return texts.reminders.render(ReminderWithLessonDTO.from_orm_obj_with_lesson(reminder), moment)

    async def cancel(self, reminder_id: int) -> ReminderWithLessonDTO:
        reminder = await self._reminder_repository.get_with_lesson_for_update(reminder_id)
        if reminder is None:
            raise ReminderNotFoundError(reminder_id)
        if reminder.status != ReminderStatus.PENDING:
            raise ReminderNotPendingError
        reminder.status = ReminderStatus.CANCELLED
        await self._reminder_repository.flush()
        return ReminderWithLessonDTO.from_orm_obj_with_lesson(reminder)
