from fastapi import APIRouter

from api.core.errors import ERROR_RESPONSES
from api.v1 import admins, auth, clubs, roles


def create_v1_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", responses=ERROR_RESPONSES)
    router.include_router(auth.router)
    router.include_router(admins.router)
    router.include_router(roles.router)
    router.include_router(clubs.router)
    return router
