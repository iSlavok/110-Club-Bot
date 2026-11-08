from collections.abc import Sequence
from io import BytesIO

from xlsxwriter import Workbook

type XlsxCell = str | int | None

XLSX_MEDIA_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
_COLUMN_WIDTH = 24


# Synchronous: callers run it in a thread. A URL string becomes a clickable link (xlsxwriter's strings_to_urls).
def build_xlsx(headers: Sequence[str], rows: Sequence[Sequence[XlsxCell]]) -> bytes:
    buffer = BytesIO()
    with Workbook(buffer, {"in_memory": True}) as workbook:
        sheet = workbook.add_worksheet()
        bold = workbook.add_format({"bold": True})
        sheet.write_row(0, 0, headers, bold)
        for index, row in enumerate(rows, start=1):
            sheet.write_row(index, 0, row)
        sheet.set_column(0, len(headers) - 1, _COLUMN_WIDTH)
        sheet.freeze_panes(1, 0)
        sheet.autofilter(0, 0, len(rows), len(headers) - 1)
    return buffer.getvalue()
