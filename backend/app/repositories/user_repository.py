from sqlalchemy import ColumnElement, func, or_, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import BaseRepository, PageResult
from app.models import User
from app.types import INT64_MAX
from app.utils import normalize_search_query

# pg_trgm word_similarity: 1 = exact word match. Lower finds more typos and more noise.
FUZZY_SEARCH_THRESHOLD = 0.4


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
            select(User)
            .where(*conditions)
            .order_by(*self._search_order(query), User.created_at.desc(), User.id.desc())
            .limit(limit)
            .offset(offset)
        )
        users = await self._session.scalars(statement)
        return PageResult(items=list(users), total=total)

    # Substring match, or a fuzzy one that survives typos and word order; digits also hit Telegram and VK ids.
    @staticmethod
    def _search_conditions(query: str | None) -> list[ColumnElement[bool]]:
        normalized = normalize_search_query(query or "")
        if not normalized:
            return []
        escaped = normalized.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")
        conditions = [
            User.search_text.like(f"%{escaped}%"),
            func.word_similarity(normalized, User.search_text) >= FUZZY_SEARCH_THRESHOLD,
        ]
        if normalized.isdecimal() and int(normalized) <= INT64_MAX:
            conditions += [User.tg_id == int(normalized), User.vk_id == int(normalized)]
        return [or_(*conditions)]

    @staticmethod
    def _search_order(query: str | None) -> list[ColumnElement[float]]:
        normalized = normalize_search_query(query or "")
        if not normalized:
            return []
        return [func.word_similarity(normalized, User.search_text).desc()]
