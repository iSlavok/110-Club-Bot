from enum import StrEnum


class HealthStatus(StrEnum):
    OK = "ok"
    UNAVAILABLE = "unavailable"


class CheckStatus(StrEnum):
    OK = "ok"
    FAIL = "fail"
