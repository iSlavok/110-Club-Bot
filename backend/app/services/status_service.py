from app.models import Club
from app.repositories import ClubRepository
from app.schemas import ClubDTO, ClubStatus, CurrentBlockStats, StatusReport
from app.services.club_stats_service import ClubStatsService


class StatusService:
    def __init__(self, club_repository: ClubRepository, club_stats_service: ClubStatsService) -> None:
        self._club_repository = club_repository
        self._club_stats_service = club_stats_service

    async def build(self) -> StatusReport:
        clubs = await self._club_repository.list_active()
        statuses: list[ClubStatus] = []
        for club in clubs:
            status = await self._club_status(club)
            statuses.append(status)
        return StatusReport(clubs=statuses)

    async def _club_status(self, club: Club) -> ClubStatus:
        current_block = await self._current_block_section(club)
        return ClubStatus(club=ClubDTO.from_orm_obj(club), current_block=current_block)

    async def _current_block_section(self, club: Club) -> CurrentBlockStats | None:
        stats = await self._club_stats_service.get(club.id)
        return stats.current_block
