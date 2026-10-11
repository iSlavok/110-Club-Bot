from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter

from api.core.auth import require
from api.core.routing import UnitOfWorkRoute
from api.schemas.app_settings_schemas import AppSettingsResponse
from app.enums import Permission
from app.schemas import AppSettingsUpdate
from app.services import AppSettingsService

router = APIRouter(prefix="/settings", tags=["settings"], route_class=UnitOfWorkRoute)


@router.get("", dependencies=[require()])
async def get_settings(app_settings_service: FromDishka[AppSettingsService]) -> AppSettingsResponse:
    overview = await app_settings_service.get_overview()
    return AppSettingsResponse.from_overview(overview)


@router.patch("", dependencies=[require(Permission.SETTINGS_EDIT)])
async def update_settings(
    patch: AppSettingsUpdate,
    app_settings_service: FromDishka[AppSettingsService],
) -> AppSettingsResponse:
    overview = await app_settings_service.update(patch)
    return AppSettingsResponse.from_overview(overview)
