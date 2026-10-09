from datetime import UTC, datetime

from app import texts
from app.schemas import BlockDTO, ClubDTO, ClubStatus, CurrentBlockStats, StatusReport

NOW = datetime(2026, 10, 1, tzinfo=UTC)


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


def test_club_with_current_block() -> None:
    current_block = CurrentBlockStats(block=_block("Блок 5"), members=120, members_with_tg=80)
    report = StatusReport(clubs=[ClubStatus(club=_club("Химия"), current_block=current_block)])

    assert texts.status.status_report(report) == (
        "<b>Химия</b>\nБлок: Блок 5 (01.09–01.11)\nУчастников: 120, из них в боте: 80"
    )


def test_club_without_current_block_and_escaping() -> None:
    report = StatusReport(clubs=[ClubStatus(club=_club("Био & <химия>"), current_block=None)])

    assert texts.status.status_report(report) == "<b>Био &amp; &lt;химия&gt;</b>\nТекущего блока нет."


def test_clubs_are_separated_by_blank_line() -> None:
    report = StatusReport(
        clubs=[ClubStatus(club=_club("А"), current_block=None), ClubStatus(club=_club("Б"), current_block=None)],
    )

    assert texts.status.status_report(report) == "<b>А</b>\nТекущего блока нет.\n\n<b>Б</b>\nТекущего блока нет."


def test_no_active_clubs() -> None:
    assert texts.status.status_report(StatusReport(clubs=[])) == texts.status.NO_ACTIVE_CLUBS
