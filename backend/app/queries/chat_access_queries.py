from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import ChatAccessStatus
from app.models import ChatAccess, Membership, User

REINVITED_STATUSES = (ChatAccessStatus.LEFT, ChatAccessStatus.KICKED)


class ChatAccessQueries:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # Linked members of the access block the bot has not invited to this chat yet, or who are out of it again.
    async def list_users_to_invite(self, *, club_id: int, chat_id: int, block_id: int) -> list[int]:
        statement = (
            select(User.id)
            .join(Membership, Membership.vk_id == User.vk_id)
            .outerjoin(
                ChatAccess,
                and_(
                    ChatAccess.club_id == club_id,
                    ChatAccess.user_id == User.id,
                ),
            )
            .where(
                Membership.block_id == block_id,
                or_(
                    ChatAccess.id.is_(None),
                    ChatAccess.chat_id != chat_id,
                    ChatAccess.status.in_(REINVITED_STATUSES),
                ),
            )
            .order_by(User.id)
        )
        user_ids = await self._session.scalars(statement)
        return list(user_ids)

    # Without an access block every student the bot let in is out of it.
    async def list_joined_without_access(self, *, club_id: int, chat_id: int, block_id: int | None) -> list[int]:
        conditions = [
            ChatAccess.club_id == club_id,
            ChatAccess.chat_id == chat_id,
            ChatAccess.status == ChatAccessStatus.JOINED,
        ]
        if block_id is not None:
            block_member = (
                select(Membership.id)
                .where(
                    Membership.block_id == block_id,
                    Membership.vk_id == User.vk_id,
                )
            )
            conditions.append(~block_member.exists())
        statement = (
            select(ChatAccess.id)
            .join(User, User.id == ChatAccess.user_id)
            .where(*conditions)
            .order_by(ChatAccess.id)
        )
        access_ids = await self._session.scalars(statement)
        return list(access_ids)
