from app.exceptions import AppError, NotFoundError


class LessonNotFoundError(NotFoundError):
    pass


def test_code_is_derived_from_class_name() -> None:
    assert LessonNotFoundError.code == "LESSON_NOT_FOUND"


def test_tag_has_own_code() -> None:
    assert NotFoundError.code == "NOT_FOUND"


def test_message_is_kept() -> None:
    error = LessonNotFoundError("lesson 7 not found")

    assert isinstance(error, AppError)
    assert error.message == "lesson 7 not found"
