import pytest
from sqlalchemy import select

from app.enums import SheetSyncStatus
from app.models import Membership, SheetSync
from app.services import SheetSyncService
from app.services.sheet_sync_service import INTERNAL_ERROR_MESSAGE
from tests.factories import make_block, make_club
from worker.jobs import sync_sheets


@pytest.fixture
async def service(request_container) -> SheetSyncService:
    return await request_container.get(SheetSyncService)


async def block_members(db_session, block_id: int) -> set[int]:
    vk_ids = await db_session.scalars(select(Membership.vk_id).where(Membership.block_id == block_id))
    return set(vk_ids)


async def syncs_by_club(db_session) -> dict[int, SheetSync]:
    syncs = await db_session.scalars(select(SheetSync))
    return {sync.club_id: sync for sync in syncs}


async def test_syncs_every_active_club_with_a_sheet(container, service, db_session, sheets_client) -> None:
    club = await make_club(db_session, spreadsheet_id="s1", sheet_name="list")
    block = await make_block(db_session, club, sheet_column_title="Блок 5")
    inactive = await make_club(db_session, spreadsheet_id="s2", sheet_name="list", is_active=False)
    without_sheet = await make_club(db_session)
    sheets_client.set_sheet("s1", "list", [[True, "Блок 5", 501]])
    sheets_client.set_sheet("s2", "list", [])

    await sync_sheets(container, service)

    assert await block_members(db_session, block.id) == {501}
    syncs = await syncs_by_club(db_session)
    assert club.id in syncs
    assert inactive.id not in syncs
    assert without_sheet.id not in syncs


async def test_crashed_club_does_not_stop_the_others(container, service, db_session, sheets_client) -> None:
    broken = await make_club(db_session, spreadsheet_id="s1", sheet_name="list")
    healthy = await make_club(db_session, spreadsheet_id="s2", sheet_name="list")
    block = await make_block(db_session, healthy, sheet_column_title="Блок 5")
    sheets_client.fail("s1", "list", RuntimeError("bug"))
    sheets_client.set_sheet("s2", "list", [[True, "Блок 5", 501]])

    await sync_sheets(container, service)

    assert await block_members(db_session, block.id) == {501}
    syncs = await syncs_by_club(db_session)
    assert syncs[healthy.id].status is SheetSyncStatus.OK
    assert syncs[broken.id].status is SheetSyncStatus.FAILED
    assert syncs[broken.id].error == INTERNAL_ERROR_MESSAGE


async def test_disabled_client_syncs_nothing(container, service, db_session, sheets_client) -> None:
    club = await make_club(db_session, spreadsheet_id="s1", sheet_name="list")
    sheets_client.is_enabled = False

    await sync_sheets(container, service)

    assert club.id not in await syncs_by_club(db_session)
