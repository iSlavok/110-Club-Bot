from io import BytesIO

from openpyxl import load_workbook


def read_xlsx(content: bytes) -> list[list[object]]:
    sheet = load_workbook(BytesIO(content)).active
    assert sheet is not None
    return [list(row) for row in sheet.iter_rows(values_only=True)]
