from enum import StrEnum


class LessonKind(StrEnum):
    LESSON = "lesson"
    CURATOR_CALL = "curator_call"


class LessonView(StrEnum):
    UPCOMING = "upcoming"
    PAST = "past"
    ALL = "all"
