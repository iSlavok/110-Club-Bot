from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import BaseRepository, PageResult
from app.models import Block


class BlockRepository(BaseRepository[Block]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Block)

    async def get_by_column(self, *, club_id: int, sheet_column_title: str) -> Block | None:
        statement = (
            select(Block)
            .where(
                Block.club_id == club_id,
                Block.sheet_column_title == sheet_column_title,
            )
        )
        return await self._session.scalar(statement)

    # Blocks should not overlap; if they do, the one started last is current.
    async def get_current_for_club(self, *, club_id: int, now: datetime) -> Block | None:
        statement = (
            select(Block)
            .where(
                Block.club_id == club_id,
                Block.starts_at <= now,
                Block.ends_at > now,
            )
            .order_by(Block.starts_at.desc(), Block.id.desc())
            .limit(1)
        )
        return await self._session.scalar(statement)

    async def list_for_club(self, club_id: int) -> list[Block]:
        statement = (
            select(Block)
            .where(Block.club_id == club_id)
            .order_by(Block.starts_at, Block.id)
        )
        blocks = await self._session.scalars(statement)
        return list(blocks)

    async def list_page_for_club(self, *, club_id: int, limit: int, offset: int) -> PageResult[Block]:
        conditions = [Block.club_id == club_id]

        count_statement = (
            select(func.count())
            .select_from(Block)
            .where(*conditions)
        )
        total = await self._session.scalar(count_statement) or 0

        statement = (
            select(Block)
            .where(*conditions)
            .order_by(Block.starts_at.desc(), Block.id.desc())
            .limit(limit)
            .offset(offset)
        )
        blocks = await self._session.scalars(statement)
        return PageResult(items=list(blocks), total=total)
