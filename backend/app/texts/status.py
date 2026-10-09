from datetime import datetime
from html import escape

from app.schemas import ClubStatus, CurrentBlockStats, StatusReport
from app.utils import BUSINESS_TZ

NO_ACTIVE_CLUBS = "Активных клубов нет."


def status_report(report: StatusReport) -> str:
    if not report.clubs:
        return NO_ACTIVE_CLUBS
    return "\n\n".join(_club_status(status) for status in report.clubs)


def _club_status(status: ClubStatus) -> str:
    lines = [
        f"<b>{escape(status.club.title)}</b>",
        *_current_block(status.current_block),
    ]
    return "\n".join(lines)


def _current_block(stats: CurrentBlockStats | None) -> list[str]:
    if stats is None:
        return ["Текущего блока нет."]
    block = stats.block
    return [
        f"Блок: {escape(block.title)} ({_day(block.starts_at)}–{_day(block.ends_at)})",
        f"Участников: {stats.members}, из них в боте: {stats.members_with_tg}",
    ]


def _day(moment: datetime) -> str:
    return moment.astimezone(BUSINESS_TZ).strftime("%d.%m")
