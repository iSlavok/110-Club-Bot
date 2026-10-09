from datetime import datetime
from html import escape

from app.enums import RemovalRequestStatus
from app.schemas import RemovalCandidate, RemovalRequestAlert
from app.utils import BUSINESS_TZ

# Keeps the alert far below Telegram's 4096-character message limit.
MAX_LISTED_CANDIDATES = 15

CONFIRM_REMOVAL_BUTTON = "Подтвердить"
REJECT_REMOVAL_BUTTON = "Отклонить"

_FEW_LAST_DIGITS = (2, 3, 4)
_TEENS = range(11, 15)


def removal_request(alert: RemovalRequestAlert) -> str:
    header = f"<b>{escape(alert.club_title)} · {escape(alert.block_title)}</b>"
    lines = [header, _removal_status(alert)]
    if alert.candidates:
        lines.append("")
        lines.extend(_candidate(candidate) for candidate in alert.candidates[:MAX_LISTED_CANDIDATES])
        hidden = len(alert.candidates) - MAX_LISTED_CANDIDATES
        if hidden > 0:
            lines.append(f"и ещё {hidden}")
    return "\n".join(lines)


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
