import pytest

from app.clients import CellValue
from app.enums import SheetIssueKind
from app.schemas import SheetIssue
from app.services.sheet_parser import parse_sheet
from app.types import INT64_MAX


def parse(*columns: list[CellValue], blocks: tuple[str, ...] = ("Блок 5",), open_blocks: tuple[str, ...] = ()):
    return parse_sheet(list(columns), block_titles=blocks, open_block_titles=open_blocks)


def test_ready_column_gives_members_of_its_block() -> None:
    parsed = parse([True, "Блок 5", 101, "102", 103.0])

    assert parsed.members == {"Блок 5": {101, 102, 103}}
    assert parsed.issues == []


def test_column_without_checkbox_is_ignored() -> None:
    parsed = parse([False, "Блок 5", 101], ["", "Блок 6", "garbage"], blocks=("Блок 5", "Блок 6"))

    assert parsed.members == {}
    assert parsed.issues == []


@pytest.mark.parametrize("ready", ["TRUE", 1, ""])
def test_only_a_real_checkbox_marks_column_ready(ready: CellValue) -> None:
    parsed = parse([ready, "Блок 5", 101])

    assert parsed.members == {}


def test_header_is_trimmed() -> None:
    parsed = parse([True, "  Блок 5 ", 101])

    assert parsed.members == {"Блок 5": {101}}


def test_numeric_header_matches_block_title() -> None:
    parsed = parse([True, 5.0, 101], blocks=("5",))

    assert parsed.members == {"5": {101}}


def test_empty_cells_are_skipped() -> None:
    parsed = parse([True, "Блок 5", "", 101, "  ", 102])

    assert parsed.members == {"Блок 5": {101, 102}}
    assert parsed.issues == []


def test_ready_empty_column_means_no_members() -> None:
    parsed = parse([True, "Блок 5"])

    assert parsed.members == {"Блок 5": set()}


def test_unknown_ready_column_is_reported_and_not_parsed() -> None:
    parsed = parse([True, "Блок 9", "garbage"])

    assert parsed.members == {}
    assert parsed.issues == [SheetIssue(kind=SheetIssueKind.UNKNOWN_COLUMN, column="Блок 9")]


def test_ready_column_without_header_is_unknown() -> None:
    parsed = parse([True])

    assert parsed.issues == [SheetIssue(kind=SheetIssueKind.UNKNOWN_COLUMN, column="")]


@pytest.mark.parametrize(
    ("value", "shown"),
    [
        ("id101", "id101"),
        ("https://vk.com/id101", "https://vk.com/id101"),
        (101.5, "101.5"),
        (True, "True"),
        (0, "0"),
        (-5, "-5"),
        ("-5", "-5"),
        (INT64_MAX + 1, str(INT64_MAX + 1)),
    ],
)
def test_invalid_value_is_reported_with_its_row(value: CellValue, shown: str) -> None:
    parsed = parse([True, "Блок 5", 101, value])

    assert parsed.members == {"Блок 5": {101}}
    assert parsed.issues == [SheetIssue(kind=SheetIssueKind.INVALID_VALUE, column="Блок 5", row=4, value=shown)]


def test_duplicate_id_is_reported_and_kept_once() -> None:
    parsed = parse([True, "Блок 5", 101, " 101", 101.0])

    assert parsed.members == {"Блок 5": {101}}
    assert parsed.issues == [
        SheetIssue(kind=SheetIssueKind.DUPLICATE, column="Блок 5", row=4, value="101"),
        SheetIssue(kind=SheetIssueKind.DUPLICATE, column="Блок 5", row=5, value="101"),
    ]


def test_second_ready_column_with_same_header_is_ignored() -> None:
    parsed = parse([True, "Блок 5", 101], [True, "Блок 5", 102])

    assert parsed.members == {"Блок 5": {101}}
    assert parsed.issues == [SheetIssue(kind=SheetIssueKind.DUPLICATE_COLUMN, column="Блок 5")]


def test_open_block_without_column_is_reported() -> None:
    parsed = parse([False, "Блок 5"], blocks=("Блок 5", "Блок 6", "Блок 4"), open_blocks=("Блок 5", "Блок 6"))

    assert parsed.issues == [SheetIssue(kind=SheetIssueKind.MISSING_COLUMN, column="Блок 6")]
