from collections.abc import Collection

from sqlalchemy import delete, func, insert, select
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

    async def count_by_block(self, block_ids: Collection[int]) -> dict[int, int]:
        statement = (
            select(Membership.block_id, func.count())
            .where(Membership.block_id.in_(block_ids))
            .group_by(Membership.block_id)
        )
        result = await self._session.execute(statement)
        return dict(result.all())

    async def list_vk_ids(self, block_id: int) -> set[int]:
        statement = (
            select(Membership.vk_id)
            .where(Membership.block_id == block_id)
        )
        vk_ids = await self._session.scalars(statement)
        return set(vk_ids)

    async def add_many(self, *, block_id: int, vk_ids: Collection[int]) -> None:
        if not vk_ids:
            return
        statement = (
            insert(Membership)
        )
        await self._session.execute(statement, [{"block_id": block_id, "vk_id": vk_id} for vk_id in vk_ids])

    async def delete_many(self, *, block_id: int, vk_ids: Collection[int]) -> None:
        if not vk_ids:
            return
        statement = (
            delete(Membership)
            .where(
                Membership.block_id == block_id,
                Membership.vk_id.in_(vk_ids),
            )
        )
        await self._session.execute(statement)
