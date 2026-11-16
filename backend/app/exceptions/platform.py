from app.exceptions.base import ConflictError, ExternalServiceError, NotFoundError


class ClubHasNoPlatformCourseError(ConflictError):
    def __init__(self, club_id: int) -> None:
        super().__init__(f"Club {club_id} has no platform course set")


class PlatformCourseNotFoundError(NotFoundError):
    def __init__(self, course_id: int) -> None:
        super().__init__(f"Platform course {course_id} not found")


class PlatformLessonNotFoundError(NotFoundError):
    def __init__(self, lesson_id: int) -> None:
        super().__init__(f"Platform lesson {lesson_id} not found")


class PlatformLinkingDisabledError(ExternalServiceError):
    def __init__(self) -> None:
        super().__init__("The platform token is not configured, lessons cannot be linked")


class PlatformTokenRejectedError(ExternalServiceError):
    def __init__(self) -> None:
        super().__init__("The platform refused the token")


class PlatformUnavailableError(ExternalServiceError):
    def __init__(self) -> None:
        super().__init__("The platform is unavailable")
