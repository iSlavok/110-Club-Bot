from datetime import datetime
from typing import Self

from pydantic import BaseModel

from app.enums import SheetIssueKind, SheetSyncStatus
from app.models import SheetSync


class SheetIssue(BaseModel):
    kind: SheetIssueKind
    # Column header as written in the sheet (or the block's expected header for missing_column).
    column: str
    row: int | None = None
    value: str | None = None


class SheetSyncDTO(BaseModel):
    id: int
    club_id: int
    started_at: datetime
    finished_at: datetime
    status: SheetSyncStatus
    added: int
    removed: int
    issues: list[SheetIssue]
    error: str | None
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_obj(cls, sync: SheetSync) -> Self:
        return cls(
            id=sync.id,
            club_id=sync.club_id,
            started_at=sync.started_at,
            finished_at=sync.finished_at,
            status=sync.status,
            added=sync.added,
            removed=sync.removed,
            issues=[SheetIssue.model_validate(issue) for issue in sync.issues],
            error=sync.error,
            created_at=sync.created_at,
            updated_at=sync.updated_at,
        )
