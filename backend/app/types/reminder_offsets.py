from typing import Annotated

from pydantic import AfterValidator, Field

MAX_REMINDER_OFFSET_MINUTES = 30 * 24 * 60
MAX_REMINDER_OFFSETS = 10


def _unique_latest_first(offsets: list[int]) -> list[int]:
    if len(set(offsets)) != len(offsets):
        raise ValueError("reminder offsets must be unique")
    return sorted(offsets, reverse=True)


# Minutes before the lesson start or the homework deadline; 0 is the moment itself.
type ReminderOffset = Annotated[int, Field(ge=0, le=MAX_REMINDER_OFFSET_MINUTES)]
type ReminderOffsets = Annotated[
    list[ReminderOffset],
    Field(max_length=MAX_REMINDER_OFFSETS),
    AfterValidator(_unique_latest_first),
]
