from fastapi import APIRouter

from api.core.errors import ERROR_RESPONSES


def create_v1_router() -> APIRouter:
    return APIRouter(prefix="/api/v1", responses=ERROR_RESPONSES)
