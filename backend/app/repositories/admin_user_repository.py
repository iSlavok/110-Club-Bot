from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import BaseRepository
from app.models import AdminUser


class AdminUserRepository(BaseRepository[AdminUser]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AdminUser)

    async def get_by_tg_id(self, tg_id: int) -> AdminUser | None:
        statement = (
            select(AdminUser)
            .where(AdminUser.tg_id == tg_id)
            .options(selectinload(AdminUser.role))
        )
        return await self._session.scalar(statement)
