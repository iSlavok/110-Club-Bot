from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import PageResult
from app.models import Membership, User
from app.queries.rows import BlockMemberRow


class MembershipQueries:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # Members come from the sheet by VK id; the bot user appears once the student links that VK profile.
    async def list_block_members_page(self, *, block_id: int, limit: int, offset: int) -> PageResult[BlockMemberRow]:
        conditions = [Membership.block_id == block_id]

        count_statement = (
            select(func.count())
            .select_from(Membership)
            .where(*conditions)
        )
        total = await self._session.scalar(count_statement) or 0

        statement = (
            select(Membership.vk_id, User.id, User.full_name, User.tg_username)
            .outerjoin(User, User.vk_id == Membership.vk_id)
            .where(*conditions)
            .order_by(Membership.vk_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(statement)
        rows = [
            BlockMemberRow(vk_id=vk_id, user_id=user_id, full_name=full_name, tg_username=tg_username)
            for vk_id, user_id, full_name, tg_username in result
        ]
        return PageResult(items=rows, total=total)
