from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import BaseRepository, PageResult
from app.models import AdminUser


class AdminUserRepository(BaseRepository[AdminUser]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, AdminUser)

    async def get_with_role(self, admin_user_id: int) -> AdminUser | None:
        statement = (
            select(AdminUser)
            .where(AdminUser.id == admin_user_id)
            .options(selectinload(AdminUser.role))
        )
        return await self._session.scalar(statement)

    async def get_by_tg_id(self, tg_id: int) -> AdminUser | None:
        statement = (
            select(AdminUser)
            .where(AdminUser.tg_id == tg_id)
            .options(selectinload(AdminUser.role))
        )
        return await self._session.scalar(statement)

    async def list_page(self, *, limit: int, offset: int) -> PageResult[AdminUser]:
        count_statement = (
            select(func.count())
            .select_from(AdminUser)
        )
        total = await self._session.scalar(count_statement) or 0

        statement = (
            select(AdminUser)
            .options(selectinload(AdminUser.role))
            .order_by(AdminUser.is_active.desc(), AdminUser.name, AdminUser.id)
            .limit(limit)
            .offset(offset)
        )
        admins = await self._session.scalars(statement)
        return PageResult(items=list(admins), total=total)

    async def exists_with_role(self, role_id: int) -> bool:
        admins_with_role = (
            select(AdminUser.id)
            .where(AdminUser.role_id == role_id)
        )
        statement = select(admins_with_role.exists())
        exists = await self._session.scalar(statement)
        return bool(exists)
