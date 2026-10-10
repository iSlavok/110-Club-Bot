from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.database import BaseRepository
from app.enums import ChatAccessStatus
from app.models import ChatAccess


class ChatAccessRepository(BaseRepository[ChatAccess]):
    def __init__(self, session: AsyncSession) -> None:
        super().__init__(session, ChatAccess)

    async def get_for_user(self, *, club_id: int, user_id: int) -> ChatAccess | None:
        statement = (
            select(ChatAccess)
            .where(
                ChatAccess.club_id == club_id,
                ChatAccess.user_id == user_id,
            )
        )
        return await self._session.scalar(statement)

    async def get_by_invite_link_with_user(self, invite_link: str) -> ChatAccess | None:
        statement = (
            select(ChatAccess)
            .options(joinedload(ChatAccess.user))
            .where(ChatAccess.invite_link == invite_link)
        )
        return await self._session.scalar(statement)

    async def get_with_user(self, access_id: int) -> ChatAccess | None:
        statement = (
            select(ChatAccess)
            .options(joinedload(ChatAccess.user))
            .where(ChatAccess.id == access_id)
        )
        return await self._session.scalar(statement)

    async def count_by_status(self, *, club_id: int, chat_id: int) -> dict[ChatAccessStatus, int]:
        statement = (
            select(ChatAccess.status, func.count())
            .where(
                ChatAccess.club_id == club_id,
                ChatAccess.chat_id == chat_id,
            )
            .group_by(ChatAccess.status)
        )
        result = await self._session.execute(statement)
        return dict(result.all())
