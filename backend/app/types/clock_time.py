from datetime import time
from typing import Annotated

from pydantic import AfterValidator


def _whole_minutes_without_zone(value: time) -> time:
    if value.tzinfo is not None:
        raise ValueError("time must not carry a timezone: it is Moscow time")
    if value.second or value.microsecond:
        raise ValueError("time must be whole minutes")
    return value


# Wall-clock time in Moscow (business time), e.g. the usual start of a lesson.
type ClockTime = Annotated[time, AfterValidator(_whole_minutes_without_zone)]
