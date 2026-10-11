from datetime import datetime
from html import escape

from app.enums import RemovalRequestStatus, SheetIssueKind
from app.schemas import KickedMember, ReminderWithLessonDTO, RemovalCandidate, RemovalRequestAlert, SheetIssue
from app.texts.reminders import KIND_LABELS
from app.utils import BUSINESS_TZ

# Keeps an alert far below Telegram's 4096-character message limit.
MAX_LISTED = 15

CONFIRM_REMOVAL_BUTTON = "Подтвердить"
REJECT_REMOVAL_BUTTON = "Отклонить"

_FEW_LAST_DIGITS = (2, 3, 4)
_TEENS = range(11, 15)


def removal_request(alert: RemovalRequestAlert) -> str:
    header = f"<b>Клуб {escape(alert.club_title)}, блок {escape(alert.block_title)}</b>"
    lines = [header, _removal_status(alert)]
    if alert.candidates:
        lines.append("")
        lines.extend(_candidate(candidate) for candidate in alert.candidates[:MAX_LISTED])
        lines.extend(_more(len(alert.candidates)))
    return "\n".join(lines)


def sync_failed(club_title: str, error: str) -> str:
    return (
        f"⚠️ <b>Клуб {escape(club_title)}</b>: синк таблицы не работает, состав блоков не обновляется.\n"
        f"Ошибка: {escape(error)}\n"
        "Напишу, когда снова заработает."
    )


def sync_recovered(club_title: str) -> str:
    return f"✅ <b>Клуб {escape(club_title)}</b>: синк таблицы снова работает."


def sheet_issues_appeared(club_title: str, issues: list[SheetIssue]) -> str:
    lines = [f"⚠️ <b>Клуб {escape(club_title)}</b>: новые проблемы в таблице."]
    lines.extend(f"• {_issue(issue)}" for issue in issues[:MAX_LISTED])
    lines.extend(_more(len(issues)))
    return "\n".join(lines)


def sheet_issues_resolved(club_title: str) -> str:
    return f"✅ <b>Клуб {escape(club_title)}</b>: проблем в таблице больше нет."


def removal_decided(status: RemovalRequestStatus) -> str:
    if status is RemovalRequestStatus.CONFIRMED:
        return "Удалены из блока."
    return "Остаются в блоке."


def reminder_failed(club_title: str, reminder: ReminderWithLessonDTO) -> str:
    return (
        f"⚠️ <b>Клуб {escape(club_title)}</b>: напоминание не ушло в чат.\n"
        f"«{escape(reminder.lesson.title)}» — {KIND_LABELS[reminder.kind]}, "
        f"должно было уйти {_moscow(reminder.send_at)}.\n"
        f"Ошибка: {escape(reminder.error or '—')}"
    )


def chat_kicked(club_title: str, kicked: list[KickedMember]) -> str:
    lines = [f"<b>Клуб {escape(club_title)}</b>: бот убрал из чата {_people(len(kicked))} — их нет в текущем блоке."]
    lines.extend(_candidate(member) for member in kicked[:MAX_LISTED])
    lines.extend(_more(len(kicked)))
    return "\n".join(lines)


def chat_kicks_on_hold(club_title: str, block_title: str | None, waiting: int) -> str:
    reason = (
        f"в блоке {escape(block_title)} нет участников — таблицу ещё не заполнили"
        if block_title is not None
        else "у клуба нет текущего и следующего блока"
    )
    return (
        f"⚠️ <b>Клуб {escape(club_title)}</b>: кик из чата ждёт таблицу: {reason}.\n"
        f"Впущенные ботом остаются в чате ({_people(waiting)}). Напишу, когда кик снова заработает."
    )


def chat_kicks_resumed(club_title: str) -> str:
    return f"✅ <b>Клуб {escape(club_title)}</b>: кик из чата снова работает."


def chat_failed(club_title: str, error: str) -> str:
    return (
        f"⚠️ <b>Клуб {escape(club_title)}</b>: бот не может управлять чатом клуба.\n"
        f"Ошибка: {escape(error)}\n"
        "Проверь, что бот — админ чата с правами приглашать по ссылке и блокировать. Напишу, когда заработает."
    )


def chat_recovered(club_title: str) -> str:
    return f"✅ <b>Клуб {escape(club_title)}</b>: бот снова управляет чатом клуба."


def _removal_status(alert: RemovalRequestAlert) -> str:
    count = _people(len(alert.candidates))
    detected = f"Пропали из таблицы {_moscow(alert.created_at)}"
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
            return f"{cell}: «{value}» — не VK ID, пропущено"
        case SheetIssueKind.DUPLICATE:
            return f"{cell}: VK ID {value} повторяется"


def _more(total: int) -> list[str]:
    hidden = total - MAX_LISTED
    return [f"и ещё {hidden}"] if hidden > 0 else []


def _candidate(candidate: RemovalCandidate | KickedMember) -> str:
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
