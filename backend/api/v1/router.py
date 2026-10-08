from fastapi import APIRouter

from api.core.errors import ERROR_RESPONSES
from api.v1 import (
    admins_routes,
    auth_routes,
    clubs_routes,
    roles_routes,
    settings_routes,
    sheet_syncs_routes,
    users_routes,
    vk_routes,
)


def create_v1_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", responses=ERROR_RESPONSES)
    router.include_router(auth_routes.router)
    router.include_router(admins_routes.router)
    router.include_router(roles_routes.router)
    router.include_router(clubs_routes.router)
    router.include_router(sheet_syncs_routes.router)
    router.include_router(users_routes.router)
    router.include_router(settings_routes.router)
    router.include_router(vk_routes.router)
    return router
