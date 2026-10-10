from collections.abc import Collection
from datetime import datetime

from sqlalchemy import ColumnElement, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import BaseRepository
from app.enums import ReminderKind, ReminderStatus
from app.models import Reminder


class ReminderRepository(BaseRepository[Reminder]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Reminder)

    async def list_due_ids(self, *, now: datetime, limit: int) -> list[int]:
        statement = (
            select(Reminder.id)
            .where(
                Reminder.status == ReminderStatus.PENDING,
                Reminder.send_at <= now,
            )
            .order_by(Reminder.send_at, Reminder.id)
            .limit(limit)
        )
        reminder_ids = await self._session.scalars(statement)
        return list(reminder_ids)

    # Locks the row until the transaction ends: a parallel run skips it instead of sending it twice.
    async def get_due_for_update(self, *, reminder_id: int, now: datetime) -> Reminder | None:
        statement = (
            select(Reminder)
            .where(
                Reminder.id == reminder_id,
                Reminder.status == ReminderStatus.PENDING,
                Reminder.send_at <= now,
            )
            .options(
                joinedload(Reminder.club),
                joinedload(Reminder.lesson),
            )
            .with_for_update(of=Reminder, skip_locked=True)
        )
        return await self._session.scalar(statement)

    async def get_with_club_and_lesson(self, reminder_id: int) -> Reminder | None:
        statement = (
            select(Reminder)
            .where(Reminder.id == reminder_id)
            .options(
                joinedload(Reminder.club),
                joinedload(Reminder.lesson),
            )
        )
        return await self._session.scalar(statement)

    async def cancel_pending(self, *, lesson_id: int, kinds: Collection[ReminderKind] | None = None) -> None:
        conditions: list[ColumnElement[bool]] = [
            Reminder.lesson_id == lesson_id,
            Reminder.status == ReminderStatus.PENDING,
        ]
        if kinds is not None:
            conditions.append(Reminder.kind.in_(kinds))
        statement = (
            update(Reminder)
            .where(*conditions)
            .values(status=ReminderStatus.CANCELLED)
        )
        await self._session.execute(statement)
