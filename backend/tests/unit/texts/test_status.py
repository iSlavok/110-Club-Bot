from datetime import UTC, datetime

from app import texts
from app.enums import LessonKind, ReminderKind, ReminderStatus, SheetIssueKind, SheetSyncStatus
from app.schemas import (
    BlockDTO,
    ClubDTO,
    ClubStatus,
    ClubSyncStatus,
    CurrentBlockStats,
    LessonDTO,
    ReminderStatusSection,
    ReminderWithLessonDTO,
    SheetIssue,
    SheetSyncDTO,
    StatusReport,
)

NOW = datetime(2026, 10, 1, tzinfo=UTC)
NO_SYNC = ClubSyncStatus(last_sync=None, pending_removal_requests=0)
NO_SYNC_LINES = "Синков ещё не было.\nЗапросов на удаление ждут решения: 0"
NO_REMINDERS = ReminderStatusSection(upcoming=[], failed_last_day=0)
NO_REMINDERS_LINES = "Ближайших напоминаний нет."


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


def _report(sync: ClubSyncStatus = NO_SYNC, reminders: ReminderStatusSection = NO_REMINDERS) -> StatusReport:
    return StatusReport(clubs=[ClubStatus(club=_club("Химия"), current_block=None, sync=sync, reminders=reminders)])


def test_club_with_current_block() -> None:
    current_block = CurrentBlockStats(block=_block("Блок 5"), members=120, members_with_tg=80)
    report = StatusReport(
        clubs=[ClubStatus(club=_club("Химия"), current_block=current_block, sync=NO_SYNC, reminders=NO_REMINDERS)]
    )

    assert texts.status.status_report(report) == (
        "<b>Химия</b>\nБлок: Блок 5 (01.09–01.11)\nУчастников: 120, из них в боте: 80\n"
        f"{NO_SYNC_LINES}\n{NO_REMINDERS_LINES}"
    )


def test_club_without_current_block_and_escaping() -> None:
    report = StatusReport(
        clubs=[ClubStatus(club=_club("Био & <химия>"), current_block=None, sync=NO_SYNC, reminders=NO_REMINDERS)]
    )

    assert texts.status.status_report(report) == (
        f"<b>Био &amp; &lt;химия&gt;</b>\nТекущего блока нет.\n{NO_SYNC_LINES}\n{NO_REMINDERS_LINES}"
    )


def test_successful_sync_with_sheet_problems_and_pending_removals() -> None:
    issues = [
        SheetIssue(kind=SheetIssueKind.UNKNOWN_COLUMN, column="Блок 9"),
        SheetIssue(kind=SheetIssueKind.INVALID_VALUE, column="Блок 5", row=4, value="abc"),
    ]
    sync = ClubSyncStatus(last_sync=_sync(SheetSyncStatus.OK, issues=issues), pending_removal_requests=3)

    assert texts.status.status_report(_report(sync)) == (
        "<b>Химия</b>\nТекущего блока нет.\n"
        "Синк: 01.10 12:30 МСК, успешно\nПроблем в таблице: 2\nЗапросов на удаление ждут решения: 3\n"
        f"{NO_REMINDERS_LINES}"
    )


def test_failed_sync_shows_escaped_error_instead_of_problems() -> None:
    last_sync = _sync(SheetSyncStatus.FAILED, error="Sheet <Лист1> not found")
    sync = ClubSyncStatus(last_sync=last_sync, pending_removal_requests=0)

    assert texts.status.status_report(_report(sync)) == (
        "<b>Химия</b>\nТекущего блока нет.\n"
        "Синк: 01.10 12:30 МСК, ошибка: Sheet &lt;Лист1&gt; not found\nЗапросов на удаление ждут решения: 0\n"
        f"{NO_REMINDERS_LINES}"
    )


def test_clubs_are_separated_by_blank_line() -> None:
    report = StatusReport(
        clubs=[
            ClubStatus(club=_club("А"), current_block=None, sync=NO_SYNC, reminders=NO_REMINDERS),
            ClubStatus(club=_club("Б"), current_block=None, sync=NO_SYNC, reminders=NO_REMINDERS),
        ],
    )

    club_text = f"Текущего блока нет.\n{NO_SYNC_LINES}\n{NO_REMINDERS_LINES}"
    assert texts.status.status_report(report) == f"<b>А</b>\n{club_text}\n\n<b>Б</b>\n{club_text}"


def test_no_active_clubs() -> None:
    assert texts.status.status_report(StatusReport(clubs=[])) == texts.status.NO_ACTIVE_CLUBS


# Several clubs with long Google errors must not push the report past Telegram's 4096-character limit.
def test_long_sync_error_is_cut_before_escaping() -> None:
    last_sync = _sync(SheetSyncStatus.FAILED, error="x" * 199 + "<" + "y" * 300)
    sync = ClubSyncStatus(last_sync=last_sync, pending_removal_requests=0)

    text = texts.status.status_report(_report(sync))

    assert "ошибка: " + "x" * 199 + "&lt;…\n" in text
    assert "y" not in text


def _reminder(kind: ReminderKind, send_at: datetime, title: str) -> ReminderWithLessonDTO:
    lesson = LessonDTO(
        id=1,
        club_id=1,
        kind=LessonKind.LESSON,
        title=title,
        description=None,
        starts_at=send_at,
        call_url=None,
        is_cancelled=False,
        reminder_offsets=[],
        homework_deadline_at=None,
        homework_reminder_offsets=[],
        created_at=NOW,
        updated_at=NOW,
    )
    return ReminderWithLessonDTO(
        id=1,
        club_id=1,
        lesson_id=1,
        kind=kind,
        send_at=send_at,
        status=ReminderStatus.PENDING,
        attempts=0,
        sent_at=None,
        message_id=None,
        error=None,
        created_at=NOW,
        updated_at=NOW,
        lesson=lesson,
    )


def test_upcoming_and_failed_reminders() -> None:
    reminders = ReminderStatusSection(
        upcoming=[
            _reminder(ReminderKind.LESSON_UPCOMING, datetime(2026, 10, 1, 15, 0, tzinfo=UTC), "Кислоты <1>"),
            _reminder(ReminderKind.HOMEWORK_DEADLINE, datetime(2026, 10, 2, 17, 30, tzinfo=UTC), "Оксиды"),
        ],
        failed_last_day=2,
    )

    assert texts.status.status_report(_report(reminders=reminders)) == (
        "<b>Химия</b>\n"
        "Текущего блока нет.\n"
        f"{NO_SYNC_LINES}\n"
        "Ближайшие напоминания:\n"
        "• 01.10 18:00 — напоминание об уроке, «Кислоты &lt;1&gt;»\n"
        "• 02.10 20:30 — дедлайн ДЗ, «Оксиды»\n"
        "Не ушло в чат за сутки: 2"
    )
