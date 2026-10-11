from datetime import datetime
from typing import Any

from sqlalchemy import ColumnElement, UnaryExpression, and_, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import BaseRepository, PageResult
from app.enums import LessonView
from app.models import Lesson


class LessonRepository(BaseRepository[Lesson]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Lesson)

    async def list_page_for_club(
        self,
        *,
        club_id: int,
        view: LessonView,
        include_cancelled: bool,
        now: datetime,
        limit: int,
        offset: int,
    ) -> PageResult[Lesson]:
        conditions: list[ColumnElement[bool]] = [Lesson.club_id == club_id]
        if not include_cancelled:
            conditions.append(Lesson.is_cancelled.is_(False))
        order_by: tuple[UnaryExpression[Any], ...]
        match view:
            case LessonView.UPCOMING:
                conditions.append(Lesson.starts_at >= now)
                order_by = (Lesson.starts_at.asc(), Lesson.id.asc())
            case LessonView.PAST:
                conditions.append(Lesson.starts_at < now)
                order_by = (Lesson.starts_at.desc(), Lesson.id.desc())
            case LessonView.ALL:
                order_by = (Lesson.starts_at.desc(), Lesson.id.desc())

        count_statement = (
            select(func.count())
            .select_from(Lesson)
            .where(*conditions)
        )
        total = await self._session.scalar(count_statement) or 0

        statement = (
            select(Lesson)
            .where(*conditions)
            .order_by(*order_by)
            .limit(limit)
            .offset(offset)
        )
        lessons = await self._session.scalars(statement)
        return PageResult(items=list(lessons), total=total)

    # A lesson is in the period if it starts there or its homework is due there.
    async def list_for_schedule(self, *, club_id: int, start: datetime, end: datetime) -> list[Lesson]:
        statement = (
            select(Lesson)
            .where(
                Lesson.club_id == club_id,
                Lesson.is_cancelled.is_(False),
                or_(
                    and_(Lesson.starts_at >= start, Lesson.starts_at < end),
                    and_(Lesson.homework_deadline_at >= start, Lesson.homework_deadline_at < end),
                ),
            )
            .order_by(Lesson.starts_at, Lesson.id)
        )
        lessons = await self._session.scalars(statement)
        return list(lessons)
