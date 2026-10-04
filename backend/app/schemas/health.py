from pydantic import BaseModel

from app.enums import CheckStatus, HealthStatus


class ReadinessReport(BaseModel):
    status: HealthStatus
    checks: dict[str, CheckStatus]
