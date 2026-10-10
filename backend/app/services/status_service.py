from datetime import timedelta

from app.models import Club
from app.queries import MembershipRemovalQueries
from app.repositories import ClubRepository, ReminderRepository, SheetSyncRepository
from app.schemas import (
    ClubDTO,
    ClubStatus,
    ClubSyncStatus,
    CurrentBlockStats,
    ReminderStatusSection,
    ReminderWithLessonDTO,
    SheetSyncDTO,
    StatusReport,
)
from app.services.club_stats_service import ClubStatsService
from app.utils import Clock

UPCOMING_REMINDERS = 3
FAILED_REMINDERS_WINDOW = timedelta(days=1)


class StatusService:
    def __init__(
        self,
        *,
        club_repository: ClubRepository,
        sheet_sync_repository: SheetSyncRepository,
        membership_removal_queries: MembershipRemovalQueries,
        club_stats_service: ClubStatsService,
        reminder_repository: ReminderRepository,
        clock: Clock,
    ) -> None:
        self._club_repository = club_repository
        self._sheet_sync_repository = sheet_sync_repository
        self._membership_removal_queries = membership_removal_queries
        self._club_stats_service = club_stats_service
        self._reminder_repository = reminder_repository
        self._clock = clock

    async def build(self) -> StatusReport:
        clubs = await self._club_repository.list_active()
        statuses: list[ClubStatus] = []
        for club in clubs:
            status = await self._club_status(club)
            statuses.append(status)
        return StatusReport(clubs=statuses)

    async def _club_status(self, club: Club) -> ClubStatus:
        current_block = await self._current_block_section(club)
        sync = await self._sync_section(club)
        reminders = await self._reminders_section(club)
        return ClubStatus(
            club=ClubDTO.from_orm_obj(club),
            current_block=current_block,
            sync=sync,
            reminders=reminders,
        )

    async def _current_block_section(self, club: Club) -> CurrentBlockStats | None:
        stats = await self._club_stats_service.get(club.id)
        return stats.current_block

    async def _sync_section(self, club: Club) -> ClubSyncStatus:
        last_sync = await self._sheet_sync_repository.get_latest_for_club(club.id)
        pending_removal_requests = await self._membership_removal_queries.count_pending_for_club(club.id)
        return ClubSyncStatus(
            last_sync=SheetSyncDTO.from_orm_obj(last_sync) if last_sync else None,
            pending_removal_requests=pending_removal_requests,
        )

    async def _reminders_section(self, club: Club) -> ReminderStatusSection:
        upcoming = await self._reminder_repository.list_pending_for_club(club_id=club.id, limit=UPCOMING_REMINDERS)
        failed = await self._reminder_repository.count_failed_since(
            club_id=club.id,
            since=self._clock.now() - FAILED_REMINDERS_WINDOW,
        )
        return ReminderStatusSection(
            upcoming=[ReminderWithLessonDTO.from_orm_obj_with_lesson(reminder) for reminder in upcoming],
            failed_last_day=failed,
        )
