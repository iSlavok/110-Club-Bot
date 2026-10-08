from datetime import datetime

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import BaseRepository, PageResult
from app.models import SheetSync

# First key of the two-key advisory lock: keeps sync locks apart from other advisory locks on the same club id.
SHEET_SYNC_LOCK_NAMESPACE = 3


class SheetSyncRepository(BaseRepository[SheetSync]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, SheetSync)

    # Held until the transaction ends, so a manual and a scheduled sync of one club never interleave.
    async def lock_club(self, club_id: int) -> None:
        statement = (
            select(func.pg_advisory_xact_lock(SHEET_SYNC_LOCK_NAMESPACE, club_id))
        )
        await self._session.execute(statement)

    async def list_page_for_club(self, *, club_id: int, limit: int, offset: int) -> PageResult[SheetSync]:
        conditions = [SheetSync.club_id == club_id]

        count_statement = (
            select(func.count())
            .select_from(SheetSync)
            .where(*conditions)
        )
        total = await self._session.scalar(count_statement) or 0

        statement = (
            select(SheetSync)
            .where(*conditions)
            .order_by(SheetSync.started_at.desc(), SheetSync.id.desc())
            .limit(limit)
            .offset(offset)
        )
        syncs = await self._session.scalars(statement)
        return PageResult(items=list(syncs), total=total)

    async def delete_started_before(self, moment: datetime) -> None:
        statement = (
            delete(SheetSync)
            .where(SheetSync.started_at < moment)
        )
        await self._session.execute(statement)
