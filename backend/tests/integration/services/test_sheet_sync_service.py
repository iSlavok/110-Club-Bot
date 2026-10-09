from datetime import UTC, datetime, timedelta

import pytest
from sqlalchemy import select

from app.clients import SheetsClientError
from app.enums import SheetIssueKind, SheetSyncStatus
from app.exceptions import ClubNotFoundError, ClubNotSyncableError, SheetSyncDisabledError
from app.models import Block, SheetSync
from app.repositories import MembershipRepository
from app.schemas import SheetIssue
from app.services import SheetSyncService
from app.services.sheet_sync_service import INTERNAL_ERROR_MESSAGE
from tests.factories import make_block, make_club, make_membership, make_sheet_sync
from tests.providers import DEFAULT_NOW

SPREADSHEET_ID = "spreadsheet-1"
SHEET_NAME = "Состав"


@pytest.fixture
async def service(request_container) -> SheetSyncService:
    return await request_container.get(SheetSyncService)


@pytest.fixture
async def club(db_session):
    return await make_club(db_session, spreadsheet_id=SPREADSHEET_ID, sheet_name=SHEET_NAME)


@pytest.fixture
def members(request_container):
    async def vk_ids(block: Block) -> set[int]:
        repository = await request_container.get(MembershipRepository)
        return await repository.list_vk_ids(block.id)

    return vk_ids


async def test_ready_column_becomes_block_members(service, db_session, club, sheets_client, members) -> None:
    block = await make_block(db_session, club, sheet_column_title="Блок 5")
    sheets_client.set_sheet(SPREADSHEET_ID, SHEET_NAME, [[True, "Блок 5", 501, 502]])

    sync = await service.sync_club(club.id)

    assert await members(block) == {501, 502}
    assert sync.status is SheetSyncStatus.OK
    assert (sync.added, sync.removal_requested) == (2, 0)
    assert sync.started_at == DEFAULT_NOW
    assert sync.issues == []


async def test_members_gone_from_sheet_wait_for_confirmation(service, db_session, club, sheets_client, members) -> None:
    block = await make_block(db_session, club, sheet_column_title="Блок 5")
    await make_membership(db_session, block, vk_id=501)
    await make_membership(db_session, block, vk_id=502)
    sheets_client.set_sheet(SPREADSHEET_ID, SHEET_NAME, [[True, "Блок 5", 502, 503]])

    sync = await service.sync_club(club.id)
    repeated = await service.sync_club(club.id)

    assert await members(block) == {501, 502, 503}
    assert (sync.added, sync.removal_requested) == (1, 1)
    assert (repeated.added, repeated.removal_requested) == (0, 0)


async def test_column_without_checkbox_keeps_members(service, db_session, club, sheets_client, members) -> None:
    block = await make_block(db_session, club, sheet_column_title="Блок 5")
    await make_membership(db_session, block, vk_id=501)
    sheets_client.set_sheet(SPREADSHEET_ID, SHEET_NAME, [[False, "Блок 5"]])

    sync = await service.sync_club(club.id)

    assert await members(block) == {501}
    assert (sync.added, sync.removal_requested) == (0, 0)


async def test_blocks_are_matched_within_the_club(service, db_session, club, sheets_client, members) -> None:
    other_block = await make_block(db_session, await make_club(db_session), sheet_column_title="Блок 5")
    block = await make_block(db_session, club, sheet_column_title="Блок 5")
    sheets_client.set_sheet(SPREADSHEET_ID, SHEET_NAME, [[True, "Блок 5", 501]])

    await service.sync_club(club.id)

    assert await members(block) == {501}
    assert await members(other_block) == set()


async def test_sheet_problems_are_recorded(service, db_session, club, sheets_client) -> None:
    await make_block(db_session, club, sheet_column_title="Блок 5")
    await make_block(db_session, club, sheet_column_title="Блок 6")
    ended = DEFAULT_NOW - timedelta(days=1)
    await make_block(db_session, club, sheet_column_title="Блок 1", starts_at=ended - timedelta(days=60), ends_at=ended)
    sheets_client.set_sheet(SPREADSHEET_ID, SHEET_NAME, [[True, "Блок 5", "abc"], [True, "Блок 9", 501]])

    sync = await service.sync_club(club.id)

    assert sync.status is SheetSyncStatus.OK
    assert sync.issues == [
        SheetIssue(kind=SheetIssueKind.INVALID_VALUE, column="Блок 5", row=3, value="abc"),
        SheetIssue(kind=SheetIssueKind.UNKNOWN_COLUMN, column="Блок 9"),
        SheetIssue(kind=SheetIssueKind.MISSING_COLUMN, column="Блок 6"),
    ]


async def test_api_error_is_recorded_and_members_kept(service, db_session, club, sheets_client, members) -> None:
    block = await make_block(db_session, club, sheet_column_title="Блок 5")
    await make_membership(db_session, block, vk_id=501)
    sheets_client.fail(SPREADSHEET_ID, SHEET_NAME, SheetsClientError("Google Sheets API error 403 PERMISSION_DENIED"))

    sync = await service.sync_club(club.id)

    assert await members(block) == {501}
    assert sync.status is SheetSyncStatus.FAILED
    assert sync.error == "Google Sheets API error 403 PERMISSION_DENIED"
    assert (sync.added, sync.removal_requested) == (0, 0)


async def test_repeated_sync_changes_nothing(service, db_session, club, sheets_client, members) -> None:
    block = await make_block(db_session, club, sheet_column_title="Блок 5")
    sheets_client.set_sheet(SPREADSHEET_ID, SHEET_NAME, [[True, "Блок 5", 501, 502]])
    await service.sync_club(club.id)

    sync = await service.sync_club(club.id)

    assert await members(block) == {501, 502}
    assert (sync.added, sync.removal_requested) == (0, 0)


async def test_unknown_club(service) -> None:
    with pytest.raises(ClubNotFoundError):
        await service.sync_club(999_999)


@pytest.mark.parametrize(
    "overrides",
    [
        {"is_active": False, "spreadsheet_id": SPREADSHEET_ID, "sheet_name": SHEET_NAME},
        {"spreadsheet_id": None, "sheet_name": SHEET_NAME},
        {"spreadsheet_id": SPREADSHEET_ID, "sheet_name": None},
    ],
)
async def test_club_without_sheet_is_not_synced(service, db_session, overrides) -> None:
    club = await make_club(db_session, **overrides)

    with pytest.raises(ClubNotSyncableError):
        await service.sync_club(club.id)


async def test_disabled_client_refuses_to_sync(service, club, sheets_client) -> None:
    sheets_client.is_enabled = False

    with pytest.raises(SheetSyncDisabledError):
        await service.sync_club(club.id)


async def test_sync_time_comes_from_clock(service, club, sheets_client, clock) -> None:
    sheets_client.set_sheet(SPREADSHEET_ID, SHEET_NAME, [])
    clock.set(datetime(2026, 10, 5, 12, 0, tzinfo=UTC))

    sync = await service.sync_club(club.id)

    assert sync.started_at == sync.finished_at == datetime(2026, 10, 5, 12, 0, tzinfo=UTC)


async def test_syncable_clubs_are_active_with_a_sheet(service, db_session, club) -> None:
    await make_club(db_session, spreadsheet_id=SPREADSHEET_ID, sheet_name=SHEET_NAME, is_active=False)
    await make_club(db_session, spreadsheet_id=SPREADSHEET_ID)

    assert await service.list_syncable_club_ids() == [club.id]


async def test_nothing_is_syncable_while_disabled(service, club, sheets_client) -> None:
    sheets_client.is_enabled = False

    assert await service.list_syncable_club_ids() == []


async def test_record_internal_error(service, club) -> None:
    sync = await service.record_internal_error(club.id)

    assert sync.status is SheetSyncStatus.FAILED
    assert sync.error == INTERNAL_ERROR_MESSAGE
    assert sync.started_at == DEFAULT_NOW


async def test_purge_keeps_last_100_days(service, db_session, club) -> None:
    await make_sheet_sync(db_session, club, started_at=DEFAULT_NOW - timedelta(days=101))
    recent = await make_sheet_sync(db_session, club, started_at=DEFAULT_NOW - timedelta(days=99))

    await service.purge_old()

    assert list(await db_session.scalars(select(SheetSync.id))) == [recent.id]
