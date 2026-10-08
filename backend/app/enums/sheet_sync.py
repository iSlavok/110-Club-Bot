from enum import StrEnum


class SheetSyncStatus(StrEnum):
    OK = "ok"
    FAILED = "failed"


class SheetIssueKind(StrEnum):
    UNKNOWN_COLUMN = "unknown_column"
    MISSING_COLUMN = "missing_column"
    DUPLICATE_COLUMN = "duplicate_column"
    INVALID_VALUE = "invalid_value"
    DUPLICATE = "duplicate"
