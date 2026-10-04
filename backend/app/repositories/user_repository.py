from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import BaseRepository
from app.models import User


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, User)

    async def get_by_tg_id(self, tg_id: int) -> User | None:
        statement = select(User).where(User.tg_id == tg_id)
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
