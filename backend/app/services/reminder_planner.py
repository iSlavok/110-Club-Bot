from datetime import datetime, timedelta

from app.enums import ReminderKind
from app.models import Lesson, Reminder
from app.repositories import ReminderRepository
from app.utils import Clock

LESSON_REMINDER_KINDS = (ReminderKind.LESSON_UPCOMING, ReminderKind.LESSON_STARTING)


# Keeps the outbox in step with a lesson. Sent reminders are history and never touched; only reminders still ahead
# are planned, so a change never resends what the chat has already got.
class ReminderPlanner:
    def __init__(self, reminder_repository: ReminderRepository, clock: Clock) -> None:
        self._reminder_repository = reminder_repository
        self._clock = clock

    def plan_lesson(self, lesson: Lesson) -> None:
        now = self._clock.now()
        for offset in lesson.reminder_offsets:
            kind = ReminderKind.LESSON_STARTING if offset == 0 else ReminderKind.LESSON_UPCOMING
            self._add_if_ahead(lesson, kind, lesson.starts_at - timedelta(minutes=offset), now)

    def plan_homework(self, lesson: Lesson) -> None:
        if lesson.homework_deadline_at is None:
            return
        now = self._clock.now()
        for offset in lesson.homework_reminder_offsets:
            send_at = lesson.homework_deadline_at - timedelta(minutes=offset)
            self._add_if_ahead(lesson, ReminderKind.HOMEWORK_DEADLINE, send_at, now)

    async def replan_lesson(self, lesson: Lesson) -> None:
        await self._reminder_repository.cancel_pending(lesson_id=lesson.id, kinds=LESSON_REMINDER_KINDS)
        self.plan_lesson(lesson)

    async def replan_homework(self, lesson: Lesson) -> None:
        await self._reminder_repository.cancel_pending(lesson_id=lesson.id, kinds=(ReminderKind.HOMEWORK_DEADLINE,))
        self.plan_homework(lesson)

    async def cancel_all(self, lesson: Lesson) -> None:
        await self._reminder_repository.cancel_pending(lesson_id=lesson.id)

    def notify_now(self, lesson: Lesson, kind: ReminderKind) -> None:
        self._add(lesson, kind, self._clock.now())

    def _add_if_ahead(self, lesson: Lesson, kind: ReminderKind, send_at: datetime, now: datetime) -> None:
        if send_at > now:
            self._add(lesson, kind, send_at)

    def _add(self, lesson: Lesson, kind: ReminderKind, send_at: datetime) -> None:
        reminder = Reminder(club_id=lesson.club_id, lesson_id=lesson.id, kind=kind, send_at=send_at)
        self._reminder_repository.add(reminder)
