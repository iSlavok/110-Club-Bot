from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import BaseRepository
from app.models import Membership


class MembershipRepository(BaseRepository[Membership]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Membership)

    async def exists_for_block(self, block_id: int) -> bool:
        block_members = (
            select(Membership.id)
            .where(Membership.block_id == block_id)
        )
        statement = select(block_members.exists())
        exists = await self._session.scalar(statement)
        return bool(exists)
