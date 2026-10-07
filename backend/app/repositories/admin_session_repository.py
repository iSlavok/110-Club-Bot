from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import BaseRepository
from app.models import AdminSession, AdminUser


class AdminSessionRepository(BaseRepository[AdminSession]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AdminSession)

    async def get_active(self, *, token_hash: str, now: datetime) -> AdminSession | None:
        statement = (
            select(AdminSession)
            .where(
                AdminSession.token_hash == token_hash,
                AdminSession.expires_at > now,
            )
            .options(selectinload(AdminSession.admin_user).selectinload(AdminUser.role))
        )
        return await self._session.scalar(statement)

    async def delete_by_token_hash(self, token_hash: str) -> None:
        statement = (
            delete(AdminSession)
            .where(AdminSession.token_hash == token_hash)
        )
        await self._session.execute(statement)

    async def delete_for_admin(self, admin_user_id: int) -> None:
        statement = (
            delete(AdminSession)
            .where(AdminSession.admin_user_id == admin_user_id)
        )
        await self._session.execute(statement)

    async def delete_expired_for_admin(self, *, admin_user_id: int, now: datetime) -> None:
        statement = (
            delete(AdminSession)
            .where(
                AdminSession.admin_user_id == admin_user_id,
                AdminSession.expires_at <= now,
            )
        )
        await self._session.execute(statement)
