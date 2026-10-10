from datetime import datetime
from typing import Any

from sqlalchemy import ColumnElement, UnaryExpression, func, select
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
