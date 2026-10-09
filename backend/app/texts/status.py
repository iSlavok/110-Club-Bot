from datetime import datetime
from html import escape

from app.enums import SheetSyncStatus
from app.schemas import ClubStatus, ClubSyncStatus, CurrentBlockStats, SheetSyncDTO, StatusReport
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
        *_sync(status.sync),
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


def _sync(status: ClubSyncStatus) -> list[str]:
    return [
        *_last_sync(status.last_sync),
        f"Запросов на удаление ждут решения: {status.pending_removal_requests}",
    ]


# A failed sync never read the sheet, so it has no problem count to show.
def _last_sync(sync: SheetSyncDTO | None) -> list[str]:
    if sync is None:
        return ["Синков ещё не было."]
    finished = f"Синк: {_moment(sync.finished_at)} МСК"
    if sync.status is SheetSyncStatus.FAILED:
        return [f"{finished}, ошибка: {escape(sync.error or '')}"]
    return [f"{finished}, успешно", f"Проблем в таблице: {len(sync.issues)}"]


def _day(moment: datetime) -> str:
    return moment.astimezone(BUSINESS_TZ).strftime("%d.%m")


def _moment(moment: datetime) -> str:
    return moment.astimezone(BUSINESS_TZ).strftime("%d.%m %H:%M")
