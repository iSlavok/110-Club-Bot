from datetime import datetime

from sqlalchemy import delete, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import BaseRepository
from app.models import AdminUser, LoginCode


class LoginCodeRepository(BaseRepository[LoginCode]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, LoginCode)

    async def get_active(self, *, code_hash: str, now: datetime) -> LoginCode | None:
        statement = (
            select(LoginCode)
            .where(
                LoginCode.code_hash == code_hash,
                LoginCode.used_at.is_(None),
                LoginCode.expires_at > now,
            )
            .options(joinedload(LoginCode.admin_user).joinedload(AdminUser.role))
            .with_for_update(of=LoginCode)
        )
        return await self._session.scalar(statement)

    async def exists_active(self, *, code_hash: str, now: datetime) -> bool:
        active_codes = (
            select(LoginCode.id)
            .where(
                LoginCode.code_hash == code_hash,
                LoginCode.used_at.is_(None),
                LoginCode.expires_at > now,
            )
        )
        statement = select(active_codes.exists())
        exists = await self._session.scalar(statement)
        return bool(exists)

    async def expire_active_for_admin(self, *, admin_user_id: int, now: datetime) -> None:
        statement = (
            update(LoginCode)
            .where(
                LoginCode.admin_user_id == admin_user_id,
                LoginCode.used_at.is_(None),
                LoginCode.expires_at > now,
            )
            .values(expires_at=now)
        )
        await self._session.execute(statement)

    async def delete_spent(self, now: datetime) -> None:
        statement = (
            delete(LoginCode)
            .where(
                or_(
                    LoginCode.used_at.is_not(None),
                    LoginCode.expires_at <= now,
                ),
            )
        )
        await self._session.execute(statement)
