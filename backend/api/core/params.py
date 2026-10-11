from typing import Annotated

from fastapi import Path

from app.types import INT64_MAX

IdPath = Annotated[int, Path(ge=1, le=INT64_MAX)]
