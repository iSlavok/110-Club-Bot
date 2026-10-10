from datetime import UTC, datetime

from app import texts
from app.enums import SheetIssueKind, SheetSyncStatus
from app.schemas import (
    BlockDTO,
    ClubDTO,
    ClubStatus,
    ClubSyncStatus,
    CurrentBlockStats,
    SheetIssue,
    SheetSyncDTO,
    StatusReport,
)

NOW = datetime(2026, 10, 1, tzinfo=UTC)
NO_SYNC = ClubSyncStatus(last_sync=None, pending_removal_requests=0)
NO_SYNC_LINES = "Синков ещё не было.\nЗапросов на удаление ждут решения: 0"


def _club(title: str) -> ClubDTO:
    return ClubDTO(
        id=1,
        title=title,
        chat_id=None,
        reminders_topic_id=None,
        spreadsheet_id=None,
        sheet_name=None,
        is_active=True,
        created_at=NOW,
        updated_at=NOW,
    )


def _block(title: str) -> BlockDTO:
    return BlockDTO(
        id=1,
        club_id=1,
        title=title,
        sheet_column_title=title,
        # 21:00 UTC is already the next day in Moscow.
        starts_at=datetime(2026, 8, 31, 21, 0, tzinfo=UTC),
        ends_at=datetime(2026, 10, 31, 21, 0, tzinfo=UTC),
        created_at=NOW,
        updated_at=NOW,
    )


def _sync(
    status: SheetSyncStatus,
    *,
    issues: list[SheetIssue] | None = None,
    error: str | None = None,
) -> SheetSyncDTO:
    return SheetSyncDTO(
        id=1,
        club_id=1,
        started_at=datetime(2026, 10, 1, 9, 29, 58, tzinfo=UTC),
        finished_at=datetime(2026, 10, 1, 9, 30, tzinfo=UTC),
        status=status,
        added=0,
        removal_requested=0,
        issues=issues or [],
        error=error,
        created_at=NOW,
        updated_at=NOW,
    )


def _report(sync: ClubSyncStatus) -> StatusReport:
    return StatusReport(clubs=[ClubStatus(club=_club("Химия"), current_block=None, sync=sync)])


def test_club_with_current_block() -> None:
    current_block = CurrentBlockStats(block=_block("Блок 5"), members=120, members_with_tg=80)
    report = StatusReport(clubs=[ClubStatus(club=_club("Химия"), current_block=current_block, sync=NO_SYNC)])

    assert texts.status.status_report(report) == (
        f"<b>Химия</b>\nБлок: Блок 5 (01.09–01.11)\nУчастников: 120, из них в боте: 80\n{NO_SYNC_LINES}"
    )


def test_club_without_current_block_and_escaping() -> None:
    report = StatusReport(clubs=[ClubStatus(club=_club("Био & <химия>"), current_block=None, sync=NO_SYNC)])

    assert texts.status.status_report(report) == (
        f"<b>Био &amp; &lt;химия&gt;</b>\nТекущего блока нет.\n{NO_SYNC_LINES}"
    )


def test_successful_sync_with_sheet_problems_and_pending_removals() -> None:
    issues = [
        SheetIssue(kind=SheetIssueKind.UNKNOWN_COLUMN, column="Блок 9"),
        SheetIssue(kind=SheetIssueKind.INVALID_VALUE, column="Блок 5", row=4, value="abc"),
    ]
    sync = ClubSyncStatus(last_sync=_sync(SheetSyncStatus.OK, issues=issues), pending_removal_requests=3)

    assert texts.status.status_report(_report(sync)) == (
        "<b>Химия</b>\nТекущего блока нет.\n"
        "Синк: 01.10 12:30 МСК, успешно\nПроблем в таблице: 2\nЗапросов на удаление ждут решения: 3"
    )


def test_failed_sync_shows_escaped_error_instead_of_problems() -> None:
    last_sync = _sync(SheetSyncStatus.FAILED, error="Sheet <Лист1> not found")
    sync = ClubSyncStatus(last_sync=last_sync, pending_removal_requests=0)

    assert texts.status.status_report(_report(sync)) == (
        "<b>Химия</b>\nТекущего блока нет.\n"
        "Синк: 01.10 12:30 МСК, ошибка: Sheet &lt;Лист1&gt; not found\nЗапросов на удаление ждут решения: 0"
    )


def test_clubs_are_separated_by_blank_line() -> None:
    report = StatusReport(
        clubs=[
            ClubStatus(club=_club("А"), current_block=None, sync=NO_SYNC),
            ClubStatus(club=_club("Б"), current_block=None, sync=NO_SYNC),
        ],
    )

    assert texts.status.status_report(report) == (
        f"<b>А</b>\nТекущего блока нет.\n{NO_SYNC_LINES}\n\n<b>Б</b>\nТекущего блока нет.\n{NO_SYNC_LINES}"
    )


def test_no_active_clubs() -> None:
    assert texts.status.status_report(StatusReport(clubs=[])) == texts.status.NO_ACTIVE_CLUBS


# Several clubs with long Google errors must not push the report past Telegram's 4096-character limit.
def test_long_sync_error_is_cut_before_escaping() -> None:
    last_sync = _sync(SheetSyncStatus.FAILED, error="x" * 199 + "<" + "y" * 300)
    sync = ClubSyncStatus(last_sync=last_sync, pending_removal_requests=0)

    text = texts.status.status_report(_report(sync))

    assert "ошибка: " + "x" * 199 + "&lt;…\n" in text
    assert "y" not in text
