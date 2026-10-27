from datetime import datetime

from app.enums import ReminderKind, ReminderStatus
from app.exceptions import (
    ClubMessageNotFoundError,
    ClubMessageNotPendingError,
    ClubMessageSendTimePassedError,
    ClubNotFoundError,
    ClubNotReachableError,
    EmptyUpdateError,
)
from app.models import Reminder
from app.repositories import ClubRepository, ReminderRepository
from app.schemas import ClubMessageCreate, ClubMessageUpdate, ReminderDTO, ReminderWithLessonDTO
from app.utils import Clock


# A message written by an admin goes through the reminders outbox, so it is sent, retried and listed like them.
class ClubMessageService:
    def __init__(
        self,
        reminder_repository: ReminderRepository,
        club_repository: ClubRepository,
        clock: Clock,
    ) -> None:
        self._reminder_repository = reminder_repository
        self._club_repository = club_repository
        self._clock = clock

    async def create(self, club_id: int, data: ClubMessageCreate) -> ReminderWithLessonDTO:
        club = await self._club_repository.get_by_id(club_id)
        if club is None:
            raise ClubNotFoundError(club_id)
        if not club.is_active or club.chat_id is None or club.reminders_topic_id is None:
            raise ClubNotReachableError
        reminder = Reminder(
            club_id=club_id,
            lesson_id=None,
            kind=ReminderKind.MESSAGE,
            text=data.text,
            send_at=self._send_at(data.send_at),
        )
        self._reminder_repository.add(reminder)
        await self._reminder_repository.flush()
        dto = ReminderDTO.from_orm_obj(reminder)
        return ReminderWithLessonDTO(**dto.model_dump(), lesson=None)

    async def update(self, message_id: int, patch: ClubMessageUpdate) -> ReminderWithLessonDTO:
        if patch.is_empty():
            raise EmptyUpdateError
        reminder = await self._get_pending_for_update(message_id)
        reminder.text = patch.text.apply(reminder.text)
        if patch.send_at.is_set:
            reminder.send_at = self._send_at(patch.send_at.value)
        await self._reminder_repository.flush()
        return ReminderWithLessonDTO.from_orm_obj_with_lesson(reminder)

    async def cancel(self, message_id: int) -> ReminderWithLessonDTO:
        reminder = await self._get_pending_for_update(message_id)
        reminder.status = ReminderStatus.CANCELLED
        await self._reminder_repository.flush()
        return ReminderWithLessonDTO.from_orm_obj_with_lesson(reminder)

    async def _get_pending_for_update(self, message_id: int) -> Reminder:
        reminder = await self._reminder_repository.get_with_lesson_for_update(message_id)
        if reminder is None or reminder.kind is not ReminderKind.MESSAGE:
            raise ClubMessageNotFoundError(message_id)
        if reminder.status != ReminderStatus.PENDING:
            raise ClubMessageNotPendingError
        return reminder

    def _send_at(self, requested: datetime | None) -> datetime:
        now = self._clock.now()
        if requested is None:
            return now
        if requested <= now:
            raise ClubMessageSendTimePassedError
        return requested
