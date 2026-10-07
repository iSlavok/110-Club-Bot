from fastapi import APIRouter

from api.core.errors import ERROR_RESPONSES
from api.v1 import auth


def create_v1_router() -> APIRouter:
    router = APIRouter(prefix="/api/v1", responses=ERROR_RESPONSES)
    router.include_router(auth.router)
    return router
