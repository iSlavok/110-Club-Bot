import asyncio

from app import texts
from app.enums import BlockMemberSort, BlockMemberState, SortOrder
from app.exceptions import BlockNotFoundError
from app.queries import MembershipQueries
from app.queries.rows import BlockMemberRow
from app.repositories import BlockRepository, UserRepository
from app.schemas import ExportFile
from app.utils import XlsxCell, build_xlsx

# A block holds about a thousand students; the cap only keeps one export from loading the whole table by mistake.
EXPORT_MAX_ROWS = 50_000


class ExportService:
    def __init__(
        self,
        block_repository: BlockRepository,
        membership_queries: MembershipQueries,
        user_repository: UserRepository,
    ) -> None:
        self._block_repository = block_repository
        self._membership_queries = membership_queries
        self._user_repository = user_repository

    async def block_members(self, block_id: int, *, state: BlockMemberState | None, query: str | None) -> ExportFile:
        block = await self._block_repository.get_by_id(block_id)
        if block is None:
            raise BlockNotFoundError(block_id)
        members = await self._membership_queries.list_block_members_page(
            block_id=block_id,
            club_id=block.club_id,
            state=state,
            query=query,
            sort=BlockMemberSort.BOT,
            order=SortOrder.ASC,
            limit=EXPORT_MAX_ROWS,
            offset=0,
        )
        rows = [self._member_row(member) for member in members.items]
        content = await asyncio.to_thread(build_xlsx, texts.exports.BLOCK_MEMBER_HEADERS, rows)
        suffix = texts.exports.BLOCK_MEMBERS_FILE_SUFFIX[state]
        return ExportFile(filename=f"block-{block_id}-{suffix}.xlsx", content=content)

    async def users(self, query: str | None) -> ExportFile:
        users = await self._user_repository.search_page(query=query, limit=EXPORT_MAX_ROWS, offset=0)
        rows: list[list[XlsxCell]] = [
            [
                user.full_name,
                texts.exports.telegram(user.tg_username),
                user.tg_id,
                None if user.vk_id is None else texts.exports.vk_url(user.vk_id),
                texts.exports.moment(user.vk_linked_at),
                texts.exports.moment(user.created_at),
                texts.exports.moment(user.bot_blocked_at),
            ]
            for user in users.items
        ]
        content = await asyncio.to_thread(build_xlsx, texts.exports.USER_HEADERS, rows)
        return ExportFile(filename="users.xlsx", content=content)

    @staticmethod
    def _member_row(member: BlockMemberRow) -> list[XlsxCell]:
        return [
            texts.exports.vk_url(member.vk_id),
            member.vk_id,
            member.full_name,
            texts.exports.telegram(member.tg_username),
            _bot_state(member),
            None if member.chat_status is None else texts.exports.CHAT_STATUS[member.chat_status],
            texts.exports.moment(member.chat_joined_at),
        ]


def _bot_state(member: BlockMemberRow) -> str:
    if member.user_id is None:
        return texts.exports.BOT_MISSING
    if member.bot_blocked_at is not None:
        return texts.exports.BOT_BLOCKED
    return texts.exports.BOT_LINKED
