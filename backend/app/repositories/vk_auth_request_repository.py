from datetime import datetime

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import BaseRepository
from app.models import VkAuthRequest


class VkAuthRequestRepository(BaseRepository[VkAuthRequest]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, VkAuthRequest)

    # Locked: a double callback (browser retry, reload) waits here and then sees the request as used.
    async def get_for_update(self, state_hash: str) -> VkAuthRequest | None:
        statement = (
            select(VkAuthRequest)
            .where(VkAuthRequest.state_hash == state_hash)
            .options(joinedload(VkAuthRequest.user))
            .with_for_update(of=VkAuthRequest)
        )
        return await self._session.scalar(statement)

    async def expire_active_for_user(self, *, user_id: int, now: datetime) -> None:
        statement = (
            update(VkAuthRequest)
            .where(
                VkAuthRequest.user_id == user_id,
                VkAuthRequest.used_at.is_(None),
                VkAuthRequest.expires_at > now,
            )
            .values(expires_at=now)
        )
        await self._session.execute(statement)

    async def delete_spent(self, now: datetime) -> None:
        statement = (
            delete(VkAuthRequest)
            .where(
                or_(
                    VkAuthRequest.used_at.is_not(None),
                    VkAuthRequest.expires_at <= now,
                ),
            )
        )
        await self._session.execute(statement)
