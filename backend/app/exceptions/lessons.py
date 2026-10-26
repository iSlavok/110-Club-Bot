from app.exceptions.base import ConflictError, NotFoundError


class LessonNotFoundError(NotFoundError):
    def __init__(self, lesson_id: int) -> None:
        super().__init__(f"Lesson {lesson_id} not found")


class ReminderNotFoundError(NotFoundError):
    def __init__(self, reminder_id: int) -> None:
        super().__init__(f"Reminder {reminder_id} not found")


class ReminderNotPendingError(ConflictError):
    def __init__(self) -> None:
        super().__init__("Only a reminder that has not been sent yet can be cancelled")


class ReminderPreviewUnavailableError(ConflictError):
    def __init__(self) -> None:
        super().__init__("The lesson has no homework, so a homework reminder cannot be shown")


class LessonCancelledError(ConflictError):
    def __init__(self) -> None:
        super().__init__("Lesson is cancelled and can no longer be changed")


class LessonAlreadyStartedError(ConflictError):
    def __init__(self) -> None:
        super().__init__("The lesson has already started, a reminder about it is too late")


class LessonHasNoHomeworkError(ConflictError):
    def __init__(self) -> None:
        super().__init__("The lesson has no homework")


class HomeworkDeadlinePassedError(ConflictError):
    def __init__(self) -> None:
        super().__init__("The homework deadline has passed")
