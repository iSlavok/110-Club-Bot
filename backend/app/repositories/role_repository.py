from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import BaseRepository
from app.models import Role


class RoleRepository(BaseRepository[Role]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, Role)

    async def get_by_title(self, title: str) -> Role | None:
        statement = (
            select(Role)
            .where(Role.title == title)
        )
        return await self._session.scalar(statement)

    async def list_all(self) -> list[Role]:
        statement = (
            select(Role)
            .order_by(Role.title)
        )
        result = await self._session.scalars(statement)
        return list(result)
