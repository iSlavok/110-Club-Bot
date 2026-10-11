from collections.abc import Collection

from sqlalchemy import delete, insert, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import BaseRepository
from app.enums import RemovalRequestStatus
from app.models import MembershipRemovalItem, MembershipRemovalRequest


class MembershipRemovalItemRepository(BaseRepository[MembershipRemovalItem]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, MembershipRemovalItem)

    async def list_for_block(
        self,
        *,
        block_id: int,
        statuses: Collection[RemovalRequestStatus],
    ) -> list[MembershipRemovalItem]:
        statement = (
            select(MembershipRemovalItem)
            .join(MembershipRemovalItem.request)
            .where(
                MembershipRemovalRequest.block_id == block_id,
                MembershipRemovalRequest.status.in_(statuses),
            )
            .options(joinedload(MembershipRemovalItem.request))
        )
        items = await self._session.scalars(statement)
        return list(items)

    async def list_vk_ids(self, request_id: int) -> set[int]:
        statement = (
            select(MembershipRemovalItem.vk_id)
            .where(MembershipRemovalItem.request_id == request_id)
        )
        vk_ids = await self._session.scalars(statement)
        return set(vk_ids)

    async def add_many(self, *, request_id: int, vk_ids: Collection[int]) -> None:
        if not vk_ids:
            return
        statement = (
            insert(MembershipRemovalItem)
        )
        await self._session.execute(statement, [{"request_id": request_id, "vk_id": vk_id} for vk_id in vk_ids])

    async def delete_many(self, item_ids: Collection[int]) -> None:
        if not item_ids:
            return
        statement = (
            delete(MembershipRemovalItem)
            .where(MembershipRemovalItem.id.in_(item_ids))
        )
        await self._session.execute(statement)
