from app.exceptions.base import ConflictError, NotFoundError


class LessonNotFoundError(NotFoundError):
    def __init__(self, lesson_id: int) -> None:
        super().__init__(f"Lesson {lesson_id} not found")


class LessonCancelledError(ConflictError):
    def __init__(self) -> None:
        super().__init__("Lesson is cancelled and can no longer be changed")
