from pydantic import BaseModel


class ExportFile(BaseModel):
    filename: str
    content: bytes
