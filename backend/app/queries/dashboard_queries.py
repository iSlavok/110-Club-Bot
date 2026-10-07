from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Block, Club, User
from app.queries.rows import DashboardCountsRow


class DashboardQueries:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def counts(self, now: datetime) -> DashboardCountsRow:
        active_clubs = (
            select(func.count())
            .select_from(Club)
            .where(Club.is_active)
            .scalar_subquery()
        )
        current_blocks = (
            select(func.count())
            .select_from(Block)
            .join(Club, Club.id == Block.club_id)
            .where(
                Club.is_active,
                Block.starts_at <= now,
                Block.ends_at > now,
            )
            .scalar_subquery()
        )
        users = (
            select(func.count())
            .select_from(User)
            .scalar_subquery()
        )
        users_with_vk = (
            select(func.count())
            .select_from(User)
            .where(User.vk_id.is_not(None))
            .scalar_subquery()
        )
        statement = select(active_clubs, current_blocks, users, users_with_vk)
        result = await self._session.execute(statement)
        row = result.one()
        return DashboardCountsRow(active_clubs=row[0], current_blocks=row[1], users=row[2], users_with_vk=row[3])
