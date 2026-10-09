from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Block, Club, Membership
from app.queries.rows import CurrentBlockRow


class AccessQueries:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def current_blocks_for_vk(self, *, vk_id: int, now: datetime) -> list[CurrentBlockRow]:
        statement = (
            select(Club.title, Block.title)
            .select_from(Membership)
            .join(Block, Block.id == Membership.block_id)
            .join(Club, Club.id == Block.club_id)
            .where(
                Membership.vk_id == vk_id,
                Club.is_active,
                Block.starts_at <= now,
                Block.ends_at > now,
            )
            .order_by(Club.title, Block.starts_at)
        )
        result = await self._session.execute(statement)
        return [
            CurrentBlockRow(club_title=club_title, block_title=block_title)
            for club_title, block_title in result
        ]
