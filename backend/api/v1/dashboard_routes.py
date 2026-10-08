from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter

from api.core.auth import require
from api.core.routing import UnitOfWorkRoute
from api.schemas.dashboard_schemas import DashboardStatsResponse
from app.services import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"], route_class=UnitOfWorkRoute)


@router.get("/stats", dependencies=[require()])
async def get_dashboard_stats(dashboard_service: FromDishka[DashboardService]) -> DashboardStatsResponse:
    stats = await dashboard_service.get_stats()
    return DashboardStatsResponse.from_dto(stats)
