from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from api.core.auth import require
from api.schemas.dashboard import DashboardStatsResponse
from app.services import DashboardService

router = APIRouter(prefix="/dashboard", tags=["dashboard"], route_class=DishkaRoute)


@router.get("/stats", dependencies=[require()])
async def get_dashboard_stats(dashboard_service: FromDishka[DashboardService]) -> DashboardStatsResponse:
    stats = await dashboard_service.get_stats()
    return DashboardStatsResponse.from_dto(stats)
