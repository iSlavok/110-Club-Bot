from collections.abc import Collection
from datetime import datetime
from typing import Any

from sqlalchemy import ColumnElement, UnaryExpression, and_, func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import BaseRepository, PageResult
from app.enums import ReminderKind, ReminderStatus, ReminderView
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

    async def get_with_lesson(self, reminder_id: int) -> Reminder | None:
        statement = (
            select(Reminder)
            .where(Reminder.id == reminder_id)
            .options(joinedload(Reminder.lesson))
        )
        return await self._session.scalar(statement)

    # Waits for a dispatch in progress, so a reminder being sent right now is seen as sent, not cancelled over.
    async def get_with_lesson_for_update(self, reminder_id: int) -> Reminder | None:
        statement = (
            select(Reminder)
            .where(Reminder.id == reminder_id)
            .options(joinedload(Reminder.lesson))
            .with_for_update(of=Reminder)
        )
        return await self._session.scalar(statement)

    async def list_page_for_club(
        self,
        *,
        club_id: int,
        view: ReminderView,
        include_cancelled: bool,
        lesson_id: int | None,
        now: datetime,
        limit: int,
        offset: int,
    ) -> PageResult[Reminder]:
        conditions: list[ColumnElement[bool]] = [Reminder.club_id == club_id]
        if lesson_id is not None:
            conditions.append(Reminder.lesson_id == lesson_id)
        order_by: tuple[UnaryExpression[Any], ...]
        match view:
            case ReminderView.PENDING:
                pending = Reminder.status == ReminderStatus.PENDING
                # Cancelled ones that would still be ahead: what the chat is no longer going to get.
                cancelled_ahead = and_(Reminder.status == ReminderStatus.CANCELLED, Reminder.send_at >= now)
                conditions.append(or_(pending, cancelled_ahead) if include_cancelled else pending)
                order_by = (Reminder.send_at.asc(), Reminder.id.asc())
            case ReminderView.SENT:
                conditions.append(Reminder.status == ReminderStatus.SENT)
                order_by = (Reminder.sent_at.desc(), Reminder.id.desc())
            case ReminderView.ALL:
                if not include_cancelled:
                    conditions.append(Reminder.status != ReminderStatus.CANCELLED)
                order_by = (Reminder.send_at.desc(), Reminder.id.desc())

        count_statement = (
            select(func.count())
            .select_from(Reminder)
            .where(*conditions)
        )
        total = await self._session.scalar(count_statement) or 0

        statement = (
            select(Reminder)
            .where(*conditions)
            .options(joinedload(Reminder.lesson))
            .order_by(*order_by)
            .limit(limit)
            .offset(offset)
        )
        reminders = await self._session.scalars(statement)
        return PageResult(items=list(reminders), total=total)

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
