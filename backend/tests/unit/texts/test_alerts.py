from datetime import UTC, datetime

import pytest

from app.enums import LessonKind, ReminderKind, ReminderStatus, RemovalRequestStatus, SheetIssueKind
from app.schemas import LessonDTO, ReminderWithLessonDTO, RemovalCandidate, RemovalRequestAlert, SheetIssue
from app.texts import alerts

DETECTED_AT = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)
DECIDED_AT = datetime(2026, 10, 1, 10, 30, tzinfo=UTC)
NOW = datetime(2026, 10, 1, 9, 0, tzinfo=UTC)


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


@pytest.mark.parametrize(
    ("issue", "expected"),
    [
        (
            SheetIssue(kind=SheetIssueKind.UNKNOWN_COLUMN, column="Блок 9"),
            "«Блок 9»: столбец отмечен, но блока с таким заголовком нет",
        ),
        (
            SheetIssue(kind=SheetIssueKind.MISSING_COLUMN, column="Блок 6"),
            "«Блок 6»: в таблице нет столбца этого блока",
        ),
        (
            SheetIssue(kind=SheetIssueKind.DUPLICATE_COLUMN, column="Блок 5"),
            "«Блок 5»: второй отмеченный столбец с тем же заголовком, пропущен",
        ),
        (
            SheetIssue(kind=SheetIssueKind.INVALID_VALUE, column="Блок 5", row=4, value="<b>"),
            "«Блок 5», строка 4: «&lt;b&gt;» — не VK id, пропущено",
        ),
        (
            SheetIssue(kind=SheetIssueKind.DUPLICATE, column="Блок 5", row=7, value="501"),
            "«Блок 5», строка 7: VK id 501 повторяется",
        ),
    ],
)
def test_sheet_issues_are_described(issue: SheetIssue, expected: str) -> None:
    text = alerts.sheet_issues_appeared("Клуб 110", [issue])

    assert text == f"⚠️ <b>Клуб 110</b>: новые проблемы в таблице.\n• {expected}"


def test_many_sheet_issues_are_cut() -> None:
    issues = [SheetIssue(kind=SheetIssueKind.MISSING_COLUMN, column=f"Блок {n}") for n in range(20)]

    text = alerts.sheet_issues_appeared("Клуб 110", issues)

    assert text.endswith("и ещё 5")


def test_sync_failure_shows_the_escaped_error() -> None:
    text = alerts.sync_failed("Клуб <110>", "error <403>")

    assert text.startswith("⚠️ <b>Клуб &lt;110&gt;</b>: синк таблицы не работает")
    assert "Ошибка: error &lt;403&gt;" in text


def test_reminder_failed_alert() -> None:
    lesson = LessonDTO(
        id=1,
        club_id=1,
        kind=LessonKind.LESSON,
        title="Кислоты <1>",
        description=None,
        starts_at=NOW,
        call_url=None,
        is_cancelled=False,
        reminder_offsets=[],
        homework_deadline_at=NOW,
        homework_reminder_offsets=[],
        created_at=NOW,
        updated_at=NOW,
    )
    reminder = ReminderWithLessonDTO(
        id=1,
        club_id=1,
        lesson_id=1,
        kind=ReminderKind.HOMEWORK_DEADLINE,
        send_at=NOW,
        status=ReminderStatus.FAILED,
        attempts=3,
        sent_at=None,
        message_id=None,
        error="Bad Request: chat not found",
        created_at=NOW,
        updated_at=NOW,
        lesson=lesson,
    )

    assert alerts.reminder_failed("Химия & био", reminder) == (
        "⚠️ <b>Химия &amp; био</b>: напоминание не ушло в чат.\n"
        "«Кислоты &lt;1&gt;» — дедлайн ДЗ, должно было уйти 01.10 12:00 МСК.\n"
        "Ошибка: Bad Request: chat not found"
    )
