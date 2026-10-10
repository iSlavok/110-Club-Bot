from datetime import UTC, datetime, timedelta

import pytest

from app.enums import ReminderStatus, RemovalRequestStatus, SheetIssueKind, SheetSyncStatus
from app.services import StatusService
from tests.factories import (
    make_block,
    make_club,
    make_lesson,
    make_membership,
    make_reminder,
    make_removal_request,
    make_sheet_sync,
    make_user,
)
from tests.providers import DEFAULT_NOW


@pytest.fixture
async def service(request_container) -> StatusService:
    return await request_container.get(StatusService)


async def test_reports_active_clubs_by_title(service, db_session) -> None:
    await make_club(db_session, title="Химия")
    await make_club(db_session, title="Биология")
    await make_club(db_session, title="Архив", is_active=False)

    report = await service.build()

    assert [status.club.title for status in report.clubs] == ["Биология", "Химия"]


async def test_reports_current_block_members(service, db_session) -> None:
    club = await make_club(db_session)
    block = await make_block(db_session, club, starts_at=datetime(2026, 9, 1, tzinfo=UTC))
    membership = await make_membership(db_session, block)
    await make_membership(db_session, block)
    await make_user(db_session, vk_id=membership.vk_id)

    report = await service.build()

    [status] = report.clubs
    assert status.current_block is not None
    assert status.current_block.block.id == block.id
    assert (status.current_block.members, status.current_block.members_with_tg) == (2, 1)


async def test_club_without_current_block(service, db_session) -> None:
    await make_club(db_session)

    report = await service.build()

    [status] = report.clubs
    assert status.current_block is None


async def test_reports_latest_sync_and_pending_removal_requests(service, db_session) -> None:
    club = await make_club(db_session)
    block = await make_block(db_session, club)
    await make_sheet_sync(db_session, club, started_at=datetime(2026, 10, 1, 8, 0, tzinfo=UTC))
    latest = await make_sheet_sync(
        db_session,
        club,
        started_at=datetime(2026, 10, 1, 8, 50, tzinfo=UTC),
        issues=[{"kind": SheetIssueKind.UNKNOWN_COLUMN, "column": "Блок 9"}],
    )
    await make_removal_request(db_session, block, 101)
    await make_removal_request(db_session, block, 102, status=RemovalRequestStatus.CONFIRMED)

    report = await service.build()

    [status] = report.clubs
    assert status.sync.last_sync is not None
    assert status.sync.last_sync.id == latest.id
    assert len(status.sync.last_sync.issues) == 1
    assert status.sync.pending_removal_requests == 1


async def test_reports_failed_sync(service, db_session) -> None:
    club = await make_club(db_session)
    await make_sheet_sync(db_session, club, status=SheetSyncStatus.FAILED, error="Sheet not found")

    report = await service.build()

    [status] = report.clubs
    assert status.sync.last_sync is not None
    assert (status.sync.last_sync.status, status.sync.last_sync.error) == (SheetSyncStatus.FAILED, "Sheet not found")


async def test_club_without_syncs(service, db_session) -> None:
    await make_club(db_session)

    report = await service.build()

    [status] = report.clubs
    assert status.sync.last_sync is None
    assert status.sync.pending_removal_requests == 0


async def test_no_active_clubs(service) -> None:
    report = await service.build()

    assert report.clubs == []


async def test_reports_next_three_pending_reminders_and_failed_last_day(service, db_session) -> None:
    club = await make_club(db_session)
    other_club = await make_club(db_session)
    lesson = await make_lesson(db_session, club)
    for hours in (4, 1, 3, 2):
        await make_reminder(db_session, lesson, send_at=DEFAULT_NOW + timedelta(hours=hours))
    await make_reminder(db_session, lesson, send_at=DEFAULT_NOW, status=ReminderStatus.SENT)
    await make_reminder(db_session, await make_lesson(db_session, other_club), send_at=DEFAULT_NOW)
    for hours_ago in (1, 23, 25):
        await make_reminder(
            db_session,
            lesson,
            send_at=DEFAULT_NOW - timedelta(hours=hours_ago),
            status=ReminderStatus.FAILED,
        )

    report = await service.build()

    status = next(status for status in report.clubs if status.club.id == club.id)
    assert [reminder.send_at for reminder in status.reminders.upcoming] == [
        DEFAULT_NOW + timedelta(hours=1),
        DEFAULT_NOW + timedelta(hours=2),
        DEFAULT_NOW + timedelta(hours=3),
    ]
    assert status.reminders.failed_last_day == 2
