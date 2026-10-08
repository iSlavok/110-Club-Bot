from collections.abc import Sequence
from datetime import datetime

from loguru import logger

from app.clients import SheetsClient, SheetsClientError
from app.enums import SheetSyncStatus
from app.exceptions import ClubNotFoundError, ClubNotSyncableError, SheetSyncDisabledError
from app.models import Club, SheetSync
from app.repositories import BlockRepository, ClubRepository, MembershipRepository, SheetSyncRepository
from app.schemas import SheetIssue, SheetSyncDTO
from app.services.sheet_parser import parse_sheet
from app.utils import Clock


class SheetSyncService:
    def __init__(
        self,
        *,
        sheet_sync_repository: SheetSyncRepository,
        club_repository: ClubRepository,
        block_repository: BlockRepository,
        membership_repository: MembershipRepository,
        sheets_client: SheetsClient,
        clock: Clock,
    ) -> None:
        self._sheet_sync_repository = sheet_sync_repository
        self._club_repository = club_repository
        self._block_repository = block_repository
        self._membership_repository = membership_repository
        self._sheets_client = sheets_client
        self._clock = clock

    # Memberships mirror the ready columns exactly; chat access is reconciled against them, so no events are kept.
    async def sync_club(self, club_id: int) -> SheetSyncDTO:
        club = await self._get_club(club_id)
        spreadsheet_id, sheet_name = club.spreadsheet_id, club.sheet_name
        if not self._sheets_client.is_enabled:
            raise SheetSyncDisabledError
        if not club.is_active or spreadsheet_id is None or sheet_name is None:
            raise ClubNotSyncableError(club_id)
        started_at = self._clock.now()
        try:
            columns = await self._sheets_client.get_columns(spreadsheet_id, sheet_name)
        except SheetsClientError as error:
            logger.warning("Sheet sync of club {} failed: {}", club_id, error.message)
            return await self._record(club_id, started_at, status=SheetSyncStatus.FAILED, error=error.message)

        # Taken after the read: a slow Google response must not hold up the club's other syncs.
        await self._sheet_sync_repository.lock_club(club_id)
        blocks = await self._block_repository.list_for_club(club_id)
        parsed = parse_sheet(
            columns,
            block_titles={block.sheet_column_title for block in blocks},
            open_block_titles=[block.sheet_column_title for block in blocks if block.ends_at > started_at],
        )
        added = removed = 0
        for block in blocks:
            wanted = parsed.members.get(block.sheet_column_title)
            if wanted is None:
                continue
            current = await self._membership_repository.list_vk_ids(block.id)
            joined, left = wanted - current, current - wanted
            await self._membership_repository.add_many(block_id=block.id, vk_ids=joined)
            await self._membership_repository.delete_many(block_id=block.id, vk_ids=left)
            added += len(joined)
            removed += len(left)
        logger.info("Synced club {}: +{} -{}, {} issues", club_id, added, removed, len(parsed.issues))
        return await self._record(
            club_id,
            started_at,
            status=SheetSyncStatus.OK,
            added=added,
            removed=removed,
            issues=parsed.issues,
        )

    async def _get_club(self, club_id: int) -> Club:
        club = await self._club_repository.get_by_id(club_id)
        if club is None:
            raise ClubNotFoundError(club_id)
        return club

    async def _record(
        self,
        club_id: int,
        started_at: datetime,
        *,
        status: SheetSyncStatus,
        added: int = 0,
        removed: int = 0,
        issues: Sequence[SheetIssue] = (),
        error: str | None = None,
    ) -> SheetSyncDTO:
        sync = SheetSync(
            club_id=club_id,
            started_at=started_at,
            finished_at=self._clock.now(),
            status=status,
            added=added,
            removed=removed,
            issues=[issue.model_dump(mode="json") for issue in issues],
            error=error,
        )
        self._sheet_sync_repository.add(sync)
        await self._sheet_sync_repository.flush()
        return SheetSyncDTO.from_orm_obj(sync)
