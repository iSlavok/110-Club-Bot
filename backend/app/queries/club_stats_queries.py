from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Membership, User
from app.queries.rows import BlockMemberCountsRow


class ClubStatsQueries:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # users.vk_id is unique, so the outer join never multiplies memberships.
    async def block_member_counts(self, block_id: int) -> BlockMemberCountsRow:
        statement = (
            select(func.count(Membership.id), func.count(User.id))
            .select_from(Membership)
            .outerjoin(User, User.vk_id == Membership.vk_id)
            .where(Membership.block_id == block_id)
        )
        result = await self._session.execute(statement)
        members, members_with_tg = result.one()
        return BlockMemberCountsRow(members=members, members_with_tg=members_with_tg)
