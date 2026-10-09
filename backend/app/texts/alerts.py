from datetime import datetime
from html import escape

from app.enums import RemovalRequestStatus, SheetIssueKind
from app.schemas import RemovalCandidate, RemovalRequestAlert, SheetIssue
from app.utils import BUSINESS_TZ

# Keeps an alert far below Telegram's 4096-character message limit.
MAX_LISTED = 15

CONFIRM_REMOVAL_BUTTON = "Подтвердить"
REJECT_REMOVAL_BUTTON = "Отклонить"

_FEW_LAST_DIGITS = (2, 3, 4)
_TEENS = range(11, 15)


def removal_request(alert: RemovalRequestAlert) -> str:
    header = f"<b>{escape(alert.club_title)} · {escape(alert.block_title)}</b>"
    lines = [header, _removal_status(alert)]
    if alert.candidates:
        lines.append("")
        lines.extend(_candidate(candidate) for candidate in alert.candidates[:MAX_LISTED])
        lines.extend(_more(len(alert.candidates)))
    return "\n".join(lines)


def sync_failed(club_title: str, error: str) -> str:
    return (
        f"⚠️ <b>{escape(club_title)}</b>: синк таблицы не работает, состав блоков не обновляется.\n"
        f"Ошибка: {escape(error)}\n"
        "Напишу, когда снова заработает."
    )


def sync_recovered(club_title: str) -> str:
    return f"✅ <b>{escape(club_title)}</b>: синк таблицы снова работает."


def sheet_issues_appeared(club_title: str, issues: list[SheetIssue]) -> str:
    lines = [f"⚠️ <b>{escape(club_title)}</b>: новые проблемы в таблице."]
    lines.extend(f"• {_issue(issue)}" for issue in issues[:MAX_LISTED])
    lines.extend(_more(len(issues)))
    return "\n".join(lines)


def sheet_issues_resolved(club_title: str) -> str:
    return f"✅ <b>{escape(club_title)}</b>: проблем в таблице больше нет."


def removal_decided(status: RemovalRequestStatus) -> str:
    if status is RemovalRequestStatus.CONFIRMED:
        return "Удалены из блока."
    return "Остаются в блоке."


def _removal_status(alert: RemovalRequestAlert) -> str:
    count = _people(len(alert.candidates))
    detected = f"Пропали из таблицы {_moscow(alert.created_at)} МСК"
    decided = f"{escape(alert.decided_by or '')}, {_moscow(alert.decided_at)}" if alert.decided_at else ""
    match alert.status:
        case RemovalRequestStatus.PENDING:
            return f"{detected}: {count}. Удалить из блока? До решения они остаются в блоке."
        case RemovalRequestStatus.CONFIRMED:
            return f"{detected}: {count}.\n✅ Удалены из блока — {decided}."
        case RemovalRequestStatus.REJECTED:
            return (
                f"{detected}: {count}.\n❌ Остаются в блоке — {decided}. "
                "Снова спрошу, только если вернутся в таблицу и пропадут ещё раз."
            )
        case RemovalRequestStatus.CANCELLED:
            return f"{detected}, но все вернулись в таблицу. Запрос отменён."


def _issue(issue: SheetIssue) -> str:
    column = f"«{escape(issue.column)}»"
    cell = f"{column}, строка {issue.row}"
    value = escape(issue.value or "")
    match issue.kind:
        case SheetIssueKind.UNKNOWN_COLUMN:
            return f"{column}: столбец отмечен, но блока с таким заголовком нет"
        case SheetIssueKind.MISSING_COLUMN:
            return f"{column}: в таблице нет столбца этого блока"
        case SheetIssueKind.DUPLICATE_COLUMN:
            return f"{column}: второй отмеченный столбец с тем же заголовком, пропущен"
        case SheetIssueKind.INVALID_VALUE:
            return f"{cell}: «{value}» — не VK id, пропущено"
        case SheetIssueKind.DUPLICATE:
            return f"{cell}: VK id {value} повторяется"


def _more(total: int) -> list[str]:
    hidden = total - MAX_LISTED
    return [f"и ещё {hidden}"] if hidden > 0 else []


def _candidate(candidate: RemovalCandidate) -> str:
    link = f'<a href="https://vk.com/id{candidate.vk_id}">id{candidate.vk_id}</a>'
    if candidate.full_name is None:
        return f"• {link}"
    username = f" (@{escape(candidate.tg_username)})" if candidate.tg_username else ""
    return f"• {link} — {escape(candidate.full_name)}{username}"


# Russian plural: 2-4 take "человека" except 12-14; everything else takes "человек".
def _people(count: int) -> str:
    if count % 10 in _FEW_LAST_DIGITS and count % 100 not in _TEENS:
        return f"{count} человека"
    return f"{count} человек"


def _moscow(moment: datetime | None) -> str:
    return moment.astimezone(BUSINESS_TZ).strftime("%d.%m %H:%M") if moment else ""
