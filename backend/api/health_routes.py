from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Response, status

from api.schemas import HealthResponse
from app.enums import HealthStatus
from app.services import HealthService

router = APIRouter(route_class=DishkaRoute, include_in_schema=False)


@router.get("/livez", response_model_exclude_none=True)
async def livez() -> HealthResponse:
    return HealthResponse(status=HealthStatus.OK)


@router.get("/readyz")
async def readyz(response: Response, health_service: FromDishka[HealthService]) -> HealthResponse:
    report = await health_service.check_readiness()
    if report.status is not HealthStatus.OK:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return HealthResponse.from_report(report)
