from typing import Any

from sqlalchemy import ColumnElement, UnaryExpression, and_, case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import PageResult
from app.enums import BlockMemberSort, ChatAccessStatus, SortOrder
from app.models import ChatAccess, Membership, User
from app.queries.rows import BlockMemberRow


class MembershipQueries:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # Members come from the sheet by VK id; the bot user appears once the student links that VK profile.
    async def list_block_members_page(
        self,
        *,
        block_id: int,
        club_id: int,
        sort: BlockMemberSort,
        order: SortOrder,
        limit: int,
        offset: int,
    ) -> PageResult[BlockMemberRow]:
        conditions = [Membership.block_id == block_id]

        count_statement = (
            select(func.count())
            .select_from(Membership)
            .where(*conditions)
        )
        total = await self._session.scalar(count_statement) or 0

        statement = (
            select(Membership.vk_id, User.id, User.full_name, User.tg_username, ChatAccess.status)
            .outerjoin(User, User.vk_id == Membership.vk_id)
            .outerjoin(
                ChatAccess,
                and_(
                    ChatAccess.club_id == club_id,
                    ChatAccess.user_id == User.id,
                ),
            )
            .where(*conditions)
            .order_by(*_member_ordering(sort, order), Membership.vk_id)
            .limit(limit)
            .offset(offset)
        )
        result = await self._session.execute(statement)
        rows = [
            BlockMemberRow(
                vk_id=vk_id,
                user_id=user_id,
                full_name=full_name,
                tg_username=tg_username,
                chat_status=chat_status,
            )
            for vk_id, user_id, full_name, tg_username, chat_status in result
        ]
        return PageResult(items=rows, total=total)


# Ascending: people in the chat first, the chat states in the order a student goes through them.
_CHAT_RANK = case(
    (ChatAccess.status == ChatAccessStatus.JOINED, 0),
    (ChatAccess.status == ChatAccessStatus.INVITED, 1),
    (ChatAccess.status == ChatAccessStatus.LEFT, 2),
    (ChatAccess.status == ChatAccessStatus.KICKED, 3),
    else_=4,
)


# Ascending "bot" puts those who linked the bot first, by name; ties fall back to the VK id.
def _member_ordering(sort: BlockMemberSort, order: SortOrder) -> list[UnaryExpression[Any]]:
    keys: list[ColumnElement[Any]]
    match sort:
        case BlockMemberSort.VK:
            keys = [Membership.vk_id.expression]
        case BlockMemberSort.BOT:
            keys = [User.id.is_(None), func.lower(User.full_name)]
        case BlockMemberSort.CHAT:
            keys = [_CHAT_RANK, func.lower(User.full_name)]
    return [key.desc() if order is SortOrder.DESC else key.asc() for key in keys]
