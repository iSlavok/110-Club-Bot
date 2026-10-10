from collections.abc import Collection

from sqlalchemy import ColumnElement, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import BaseRepository
from app.enums import ReminderKind, ReminderStatus
from app.models import Reminder


class ReminderRepository(BaseRepository[Reminder]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Reminder)

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
