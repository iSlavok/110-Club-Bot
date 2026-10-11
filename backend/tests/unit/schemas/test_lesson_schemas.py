import pytest
from pydantic import ValidationError

from app.schemas import LessonCreate, LessonUpdate

BASE = {"kind": "lesson", "title": "Кислоты", "starts_at": "2026-10-03T19:00:00+03:00"}


def test_start_is_stored_in_utc_and_offsets_latest_first() -> None:
    lesson = LessonCreate.model_validate({**BASE, "reminder_offsets": [0, 1440, 60]})

    assert lesson.starts_at.isoformat() == "2026-10-03T16:00:00+00:00"
    assert lesson.reminder_offsets == [1440, 60, 0]


def test_offsets_are_optional_on_create() -> None:
    lesson = LessonCreate.model_validate(BASE)

    assert lesson.reminder_offsets is None
    assert lesson.homework_reminder_offsets is None


@pytest.mark.parametrize(
    "overrides",
    [
        {"reminder_offsets": [60, 60]},
        {"reminder_offsets": [-1]},
        {"homework_reminder_offsets": [43_201]},
        {"reminder_offsets": list(range(11))},
        {"call_url": "javascript:alert(1)"},
        {"call_url": 'https://meet.example.com/"x'},
        {"starts_at": "2026-10-03T19:00:00"},
        {"title": "  "},
    ],
)
def test_invalid_lessons_are_rejected(overrides) -> None:
    with pytest.raises(ValidationError):
        LessonCreate.model_validate({**BASE, **overrides})


def test_patch_tells_removed_homework_from_untouched() -> None:
    removed = LessonUpdate.model_validate({"homework_deadline_at": None})
    untouched = LessonUpdate.model_validate({"title": "Основания"})

    assert removed.homework_deadline_at.is_set
    assert removed.homework_deadline_at.value is None
    assert not untouched.homework_deadline_at.is_set
