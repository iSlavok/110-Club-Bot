from datetime import UTC, datetime

import pytest

from app.enums import RemovalRequestStatus
from app.schemas import RemovalCandidate, RemovalRequestAlert
from app.texts import alerts

DETECTED_AT = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
DECIDED_AT = datetime(2026, 10, 1, 10, 30, tzinfo=UTC)


def _alert(*vk_ids: int, **overrides: object) -> RemovalRequestAlert:
    candidates = [RemovalCandidate(vk_id=vk_id, full_name=None, tg_username=None) for vk_id in vk_ids]
    fields = {
        "club_title": "Клуб 110",
        "block_title": "Блок 5",
        "status": RemovalRequestStatus.PENDING,
        "created_at": DETECTED_AT,
        "candidates": candidates,
        **overrides,
    }
    return RemovalRequestAlert.model_validate(fields)


def test_pending_request_asks_and_lists_vk_links() -> None:
    text = alerts.removal_request(_alert(501, 502))

    assert text.splitlines()[0] == "<b>Клуб 110 · Блок 5</b>"
    assert "Пропали из таблицы 01.10 12:00 МСК: 2 человека. Удалить из блока?" in text
    assert '• <a href="https://vk.com/id501">id501</a>' in text


def test_linked_user_is_named_and_escaped() -> None:
    candidate = RemovalCandidate(vk_id=501, full_name="<Ученик>", tg_username="pupil")

    text = alerts.removal_request(_alert(candidates=[candidate]))

    assert "id501</a> — &lt;Ученик&gt; (@pupil)" in text


def test_long_list_is_cut_after_15() -> None:
    text = alerts.removal_request(_alert(*range(501, 521)))

    assert "id515<" in text
    assert "id516<" not in text
    assert text.endswith("и ещё 5")


@pytest.mark.parametrize(
    ("status", "expected"),
    [
        (RemovalRequestStatus.CONFIRMED, "✅ Удалены из блока — Владелец, 01.10 13:30."),
        (RemovalRequestStatus.REJECTED, "❌ Остаются в блоке — Владелец, 01.10 13:30."),
    ],
)
def test_decided_request_names_who_and_when(status: RemovalRequestStatus, expected: str) -> None:
    text = alerts.removal_request(_alert(501, status=status, decided_by="Владелец", decided_at=DECIDED_AT))

    assert expected in text


def test_cancelled_request() -> None:
    text = alerts.removal_request(_alert(status=RemovalRequestStatus.CANCELLED))

    assert "все вернулись в таблицу. Запрос отменён." in text


@pytest.mark.parametrize(
    ("count", "expected"),
    [(1, "1 человек"), (3, "3 человека"), (5, "5 человек"), (12, "12 человек"), (22, "22 человека")],
)
def test_people_count_is_declined(count: int, expected: str) -> None:
    text = alerts.removal_request(_alert(*range(1, count + 1)))

    assert f": {expected}." in text
