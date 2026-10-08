from typing import Self

from pydantic import BaseModel

from app.enums import CheckStatus, HealthStatus
from app.schemas import ReadinessReport


class HealthResponse(BaseModel):
    status: HealthStatus
    checks: dict[str, CheckStatus] | None = None

    @classmethod
    def from_report(cls, report: ReadinessReport) -> Self:
        return cls(status=report.status, checks=report.checks)
