from typing import Any

from fastapi import Response

from app.schemas import ExportFile
from app.utils import XLSX_MEDIA_TYPE

XLSX_RESPONSES: dict[int | str, dict[str, Any]] = {
    200: {"content": {XLSX_MEDIA_TYPE: {"schema": {"type": "string", "format": "binary"}}}, "description": "XLSX file"},
}


def xlsx_response(file: ExportFile) -> Response:
    return Response(
        content=file.content,
        media_type=XLSX_MEDIA_TYPE,
        headers={"Content-Disposition": f'attachment; filename="{file.filename}"'},
    )
