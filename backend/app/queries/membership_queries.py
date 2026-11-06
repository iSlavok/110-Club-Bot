from typing import Any

from sqlalchemy import ColumnElement, Select, UnaryExpression, and_, case, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import PageResult
from app.enums import BlockMemberSort, BlockMemberState, ChatAccessStatus, SortOrder
from app.models import ChatAccess, Membership, User
from app.queries.rows import BlockMemberFunnelRow, BlockMemberRow
from app.types import INT64_MAX
from app.utils import normalize_search_query

# Same threshold as the users search: both match the same search_text.
FUZZY_SEARCH_THRESHOLD = 0.4


class MembershipQueries:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    # Members come from the sheet by VK id; the bot user appears once the student links that VK profile.
    async def list_block_members_page(
        self,
        *,
        block_id: int,
        club_id: int,
        state: BlockMemberState | None,
        query: str | None,
        sort: BlockMemberSort,
        order: SortOrder,
        limit: int,
        offset: int,
    ) -> PageResult[BlockMemberRow]:
        conditions = [Membership.block_id == block_id, *_state_conditions(state), *_search_conditions(query)]

        count_statement = (
            _with_user_and_chat(select(func.count()), club_id)
            .where(*conditions)
        )
        total = await self._session.scalar(count_statement) or 0

        statement = (
            _with_user_and_chat(
                select(
                    Membership.vk_id,
                    User.id,
                    User.full_name,
                    User.tg_username,
                    ChatAccess.status,
                    ChatAccess.joined_at,
                ),
                club_id,
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
                chat_joined_at=chat_joined_at,
            )
            for vk_id, user_id, full_name, tg_username, chat_status, chat_joined_at in result
        ]
        return PageResult(items=rows, total=total)

    async def block_member_funnel(self, *, block_id: int, club_id: int) -> BlockMemberFunnelRow:
        statement = (
            _with_user_and_chat(
                select(
                    func.count(),
                    func.count(User.id),
                    func.count().filter(ChatAccess.status == ChatAccessStatus.JOINED),
                ),
                club_id,
            )
            .where(Membership.block_id == block_id)
        )
        result = await self._session.execute(statement)
        total, with_bot, in_chat = result.one()
        return BlockMemberFunnelRow(total=total, with_bot=with_bot, in_chat=in_chat)


def _with_user_and_chat[*Ts](statement: Select[*Ts], club_id: int) -> Select[*Ts]:
    return (
        statement
        .select_from(Membership)
        .outerjoin(User, User.vk_id == Membership.vk_id)
        .outerjoin(
            ChatAccess,
            and_(
                ChatAccess.club_id == club_id,
                ChatAccess.user_id == User.id,
            ),
        )
    )


def _state_conditions(state: BlockMemberState | None) -> list[ColumnElement[bool]]:
    not_joined = or_(ChatAccess.status.is_(None), ChatAccess.status != ChatAccessStatus.JOINED)
    match state:
        case None:
            return []
        case BlockMemberState.IN_CHAT:
            return [ChatAccess.status == ChatAccessStatus.JOINED]
        case BlockMemberState.NOT_IN_CHAT:
            return [not_joined]
        case BlockMemberState.NO_BOT:
            return [User.id.is_(None)]
        case BlockMemberState.NOT_JOINED:
            return [User.id.is_not(None), not_joined]


# Matches the users search; digits also hit the VK id from the sheet, which has no bot user behind it.
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
        conditions += [Membership.vk_id == int(normalized), User.tg_id == int(normalized)]
    return [or_(*conditions)]


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
