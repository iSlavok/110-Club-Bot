import re
from collections.abc import Collection, Sequence
from dataclasses import dataclass, field

from app.clients import CellValue
from app.enums import SheetIssueKind
from app.schemas import SheetIssue
from app.types import INT64_MAX

# Layout agreed with the curators: row 1 is the "ready" checkbox, row 2 the block header, VK ids from row 3 down.
READY_ROW = 1
HEADER_ROW = 2
FIRST_MEMBER_ROW = 3

_DIGITS = re.compile(r"[0-9]+")


@dataclass(frozen=True, slots=True)
class ParsedSheet:
    # VK ids of every ready column that matches a block, keyed by the column header.
    members: dict[str, set[int]] = field(default_factory=dict)
    issues: list[SheetIssue] = field(default_factory=list)


# A column without the ready checkbox is skipped entirely: the curator has not finished it yet.
def parse_sheet(
    columns: Sequence[Sequence[CellValue]],
    *,
    block_titles: Collection[str],
    open_block_titles: Collection[str],
) -> ParsedSheet:
    parsed = ParsedSheet()
    headers: set[str] = set()
    for column in columns:
        title = _header(column)
        headers.add(title)
        if not _is_ready(column):
            continue
        if title not in block_titles:
            parsed.issues.append(SheetIssue(kind=SheetIssueKind.UNKNOWN_COLUMN, column=title))
        elif title in parsed.members:
            parsed.issues.append(SheetIssue(kind=SheetIssueKind.DUPLICATE_COLUMN, column=title))
        else:
            parsed.members[title] = _member_ids(title, column, parsed.issues)
    parsed.issues.extend(
        SheetIssue(kind=SheetIssueKind.MISSING_COLUMN, column=title)
        for title in open_block_titles
        if title not in headers
    )
    return parsed


def _is_ready(column: Sequence[CellValue]) -> bool:
    return len(column) >= READY_ROW and column[READY_ROW - 1] is True


def _header(column: Sequence[CellValue]) -> str:
    return _cell_text(column[HEADER_ROW - 1]) if len(column) >= HEADER_ROW else ""


def _member_ids(title: str, column: Sequence[CellValue], issues: list[SheetIssue]) -> set[int]:
    vk_ids: set[int] = set()
    for row, value in enumerate(column[FIRST_MEMBER_ROW - 1 :], start=FIRST_MEMBER_ROW):
        if _cell_text(value) == "":
            continue
        vk_id = _vk_id(value)
        if vk_id is None:
            issues.append(SheetIssue(kind=SheetIssueKind.INVALID_VALUE, column=title, row=row, value=_cell_text(value)))
        elif vk_id in vk_ids:
            issues.append(SheetIssue(kind=SheetIssueKind.DUPLICATE, column=title, row=row, value=str(vk_id)))
        else:
            vk_ids.add(vk_id)
    return vk_ids


def _vk_id(value: CellValue) -> int | None:
    # bool is an int subclass: a stray checkbox must not become VK id 1.
    if isinstance(value, bool):
        return None
    if isinstance(value, float):
        if not value.is_integer():
            return None
        value = int(value)
    if isinstance(value, str):
        if not _DIGITS.fullmatch(value.strip()):
            return None
        value = int(value.strip())
    return value if 0 < value <= INT64_MAX else None


def _cell_text(value: CellValue) -> str:
    if isinstance(value, float) and value.is_integer():
        return str(int(value))
    return str(value).strip()
