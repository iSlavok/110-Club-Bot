from app.exceptions import ClubNotFoundError
from app.queries import ClubStatsQueries
from app.repositories import BlockRepository, ClubRepository
from app.schemas import BlockDTO, ClubStats, CurrentBlockStats
from app.utils import Clock


class ClubStatsService:
    def __init__(
        self,
        club_repository: ClubRepository,
        block_repository: BlockRepository,
        club_stats_queries: ClubStatsQueries,
        clock: Clock,
    ) -> None:
        self._club_repository = club_repository
        self._block_repository = block_repository
        self._club_stats_queries = club_stats_queries
        self._clock = clock

    async def get(self, club_id: int) -> ClubStats:
        if await self._club_repository.get_by_id(club_id) is None:
            raise ClubNotFoundError(club_id)
        block = await self._block_repository.get_current_for_club(club_id=club_id, now=self._clock.now())
        if block is None:
            return ClubStats(current_block=None)
        counts = await self._club_stats_queries.block_member_counts(block.id)
        current_block = CurrentBlockStats(
            block=BlockDTO.from_orm_obj(block),
            members=counts.members,
            members_with_tg=counts.members_with_tg,
        )
        return ClubStats(current_block=current_block)
