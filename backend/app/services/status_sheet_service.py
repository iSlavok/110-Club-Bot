from itertools import zip_longest

from app import texts
from app.clients import SheetsClient, SheetsClientError, WrittenCell
from app.enums import BlockMemberSort, ChatAccessStatus, SortOrder
from app.exceptions import ClubNotFoundError, StatusSheetWriteError
from app.queries import MembershipQueries
from app.queries.rows import BlockMemberRow
from app.repositories import BlockRepository, ClubRepository
from app.utils import Clock

# A block holds about a thousand students; the cap only keeps one run from loading the whole table by mistake.
STATUS_SHEET_MAX_ROWS = 50_000
# Pixels: fits the longest header with a count and a VK link, so columns do not run into each other.
STATUS_SHEET_COLUMN_WIDTH = 320


# The sheet lists the access block's VK links by funnel step, one column each, so a curator copies a whole column.
class StatusSheetService:
    def __init__(
        self,
        club_repository: ClubRepository,
        block_repository: BlockRepository,
        membership_queries: MembershipQueries,
        sheets_client: SheetsClient,
        clock: Clock,
    ) -> None:
        self._club_repository = club_repository
        self._block_repository = block_repository
        self._membership_queries = membership_queries
        self._sheets_client = sheets_client
        self._clock = clock

    async def list_club_ids(self) -> list[int]:
        if not self._sheets_client.is_enabled:
            return []
        clubs = await self._club_repository.list_with_status_sheet()
        return [club.id for club in clubs]

    async def publish(self, club_id: int) -> None:
        club = await self._club_repository.get_by_id(club_id)
        if club is None:
            raise ClubNotFoundError(club_id)
        if club.spreadsheet_id is None or club.status_sheet_name is None:
            return
        now = self._clock.now()
        block = await self._block_repository.get_access_block(club_id=club_id, now=now)
        if block is None:
            rows: list[list[WrittenCell]] = [[texts.status_sheet.title(None, now)]]
        else:
            members = await self._membership_queries.list_block_members_page(
                block_id=block.id,
                club_id=club_id,
                state=None,
                query=None,
                sort=BlockMemberSort.VK,
                order=SortOrder.ASC,
                limit=STATUS_SHEET_MAX_ROWS,
                offset=0,
            )
            rows = [[texts.status_sheet.title(block.title, now)], [], *self._funnel_columns(members.items)]
        try:
            await self._sheets_client.replace_sheet(
                club.spreadsheet_id,
                club.status_sheet_name,
                rows,
                column_widths=[STATUS_SHEET_COLUMN_WIDTH] * 3,
            )
        except SheetsClientError as error:
            raise StatusSheetWriteError(club_id, error.message) from error

    @staticmethod
    def _funnel_columns(members: list[BlockMemberRow]) -> list[list[WrittenCell]]:
        no_bot = [texts.exports.vk_url(member.vk_id) for member in members if member.user_id is None]
        in_chat = [
            texts.exports.vk_url(member.vk_id) for member in members if member.chat_status is ChatAccessStatus.JOINED
        ]
        not_joined = [
            texts.exports.vk_url(member.vk_id)
            for member in members
            if member.user_id is not None and member.chat_status is not ChatAccessStatus.JOINED
        ]
        header: list[WrittenCell] = [
            texts.status_sheet.no_bot(len(no_bot)),
            texts.status_sheet.in_chat(len(in_chat)),
            texts.status_sheet.not_joined(len(not_joined)),
        ]
        return [header, *(list(row) for row in zip_longest(no_bot, in_chat, not_joined, fillvalue=""))]
