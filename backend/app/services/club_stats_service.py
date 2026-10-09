from app.exceptions import ClubNotFoundError
from app.queries import ClubStatsQueries
from app.repositories import BlockRepository, ClubRepository, SheetSyncRepository
from app.schemas import BlockDTO, ClubStats, CurrentBlockStats, SheetSyncDTO
from app.utils import Clock


class ClubStatsService:
    def __init__(
        self,
        club_repository: ClubRepository,
        block_repository: BlockRepository,
        sheet_sync_repository: SheetSyncRepository,
        club_stats_queries: ClubStatsQueries,
        clock: Clock,
    ) -> None:
        self._club_repository = club_repository
        self._block_repository = block_repository
        self._sheet_sync_repository = sheet_sync_repository
        self._club_stats_queries = club_stats_queries
        self._clock = clock

    async def get(self, club_id: int) -> ClubStats:
        if await self._club_repository.get_by_id(club_id) is None:
            raise ClubNotFoundError(club_id)
        current_block = await self._current_block(club_id)
        last_sync = await self._sheet_sync_repository.get_latest_for_club(club_id)
        return ClubStats(
            current_block=current_block,
            last_sync=SheetSyncDTO.from_orm_obj(last_sync) if last_sync else None,
        )

    async def _current_block(self, club_id: int) -> CurrentBlockStats | None:
        block = await self._block_repository.get_current_for_club(club_id=club_id, now=self._clock.now())
        if block is None:
            return None
        counts = await self._club_stats_queries.block_member_counts(block.id)
        return CurrentBlockStats(
            block=BlockDTO.from_orm_obj(block),
            members=counts.members,
            members_with_tg=counts.members_with_tg,
        )
