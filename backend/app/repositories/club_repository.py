from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import BaseRepository, PageResult
from app.models import Club


class ClubRepository(BaseRepository[Club]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Club)

    async def get_by_title(self, title: str) -> Club | None:
        statement = (
            select(Club)
            .where(Club.title == title)
        )
        return await self._session.scalar(statement)

    async def list_page(self, *, limit: int, offset: int) -> PageResult[Club]:
        count_statement = (
            select(func.count())
            .select_from(Club)
        )
        total = await self._session.scalar(count_statement) or 0

        statement = (
            select(Club)
            .order_by(Club.is_active.desc(), Club.title)
            .limit(limit)
            .offset(offset)
        )
        clubs = await self._session.scalars(statement)
        return PageResult(items=list(clubs), total=total)
