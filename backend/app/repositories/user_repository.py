from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import BaseRepository, PageResult
from app.models import User


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_tg_id(self, tg_id: int) -> User | None:
        statement = (
            select(User)
            .where(User.tg_id == tg_id)
        )
        return await self._session.scalar(statement)

    async def upsert_by_tg_id(self, *, tg_id: int, tg_username: str | None, full_name: str) -> User:
        values = {"tg_id": tg_id, "tg_username": tg_username, "full_name": full_name}
        # populate_existing refreshes a User already in the identity map; otherwise RETURNING yields the stale object.
        statement = (
            insert(User)
            .values(values)
            .on_conflict_do_update(index_elements=[User.tg_id], set_=values)
            .returning(User)
            .execution_options(populate_existing=True)
        )
        result = await self._session.scalars(statement)
        return result.one()

    async def search_page(self, *, query: str | None, limit: int, offset: int) -> PageResult[User]:
        conditions = self._search_conditions(query)

        count_statement = (
            select(func.count())
            .select_from(User)
            .where(*conditions)
        )
        total = await self._session.scalar(count_statement) or 0

        statement = (
            select(User).where(*conditions).order_by(User.created_at.desc(), User.id.desc()).limit(limit).offset(offset)
        )
        users = await self._session.scalars(statement)
        return PageResult(items=list(users), total=total)

    @staticmethod
    def _search_conditions(query: str | None) -> list[ColumnElement[bool]]:
        if not query:
            return []
        escaped = query.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        conditions = [User.full_name.ilike(f"%{escaped}%"), User.tg_username.ilike(f"%{escaped}%")]
        if query.isdecimal():
            conditions += [User.tg_id == int(query), User.vk_id == int(query)]
        return [or_(*conditions)]
