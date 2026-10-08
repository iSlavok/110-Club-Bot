from datetime import datetime
from typing import Self

from pydantic import BaseModel, Field

from app.enums import SheetIssueKind, SheetSyncStatus
from app.schemas import SheetIssue, SheetSyncDTO


class SheetIssueResponse(BaseModel):
    kind: SheetIssueKind = Field(
        description=(
            "unknown_column: ready column matches no block; missing_column: a running or future block has no column; "
            "duplicate_column: second ready column with the same header, ignored; "
            "invalid_value: cell is not a VK id, skipped; duplicate: VK id repeated in the column"
        ),
    )
    column: str = Field(description="Column header (the block's expected header for missing_column)")
    row: int | None = Field(description="Sheet row number, from 1, for cell issues")
    value: str | None = Field(description="Cell content for cell issues")

    @classmethod
    def from_dto(cls, issue: SheetIssue) -> Self:
        return cls(kind=issue.kind, column=issue.column, row=issue.row, value=issue.value)


class SheetSyncResponse(BaseModel):
    id: int = Field(description="Sync id")
    club_id: int = Field(description="Synced club")
    started_at: datetime = Field(description="Sync start, UTC")
    finished_at: datetime = Field(description="Sync end, UTC")
    status: SheetSyncStatus = Field(description="failed: the sheet could not be read, memberships were not changed")
    added: int = Field(description="Memberships added")
    removed: int = Field(description="Memberships removed")
    issues: list[SheetIssueResponse] = Field(description="Problems found in the sheet")
    error: str | None = Field(description="Why the sync failed")

    @classmethod
    def from_dto(cls, sync: SheetSyncDTO) -> Self:
        return cls(
            id=sync.id,
            club_id=sync.club_id,
            started_at=sync.started_at,
            finished_at=sync.finished_at,
            status=sync.status,
            added=sync.added,
            removed=sync.removed,
            issues=[SheetIssueResponse.from_dto(issue) for issue in sync.issues],
            error=sync.error,
        )
