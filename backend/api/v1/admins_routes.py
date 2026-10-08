from typing import Annotated

from dishka.integrations.fastapi import FromDishka
from fastapi import APIRouter, Query, status

from api.core.auth import require
from api.core.routing import UnitOfWorkRoute
from api.schemas import Page
from api.schemas.admin_user_schemas import AdminUserResponse
from app.enums import Permission
from app.schemas import AdminPrincipal, AdminUserCreate, AdminUserUpdate, PageParams
from app.services import AdminUserService

router = APIRouter(prefix="/admins", tags=["admins"], route_class=UnitOfWorkRoute)


@router.get("", dependencies=[require(Permission.ADMINS_VIEW)])
async def list_admins(
    page: Annotated[PageParams, Query()],
    admin_user_service: FromDishka[AdminUserService],
) -> Page[AdminUserResponse]:
    admins = await admin_user_service.list_page(page)
    return Page.from_paginated(admins, page, AdminUserResponse.from_dto)


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_admin(
    actor: Annotated[AdminPrincipal, require(Permission.ADMINS_EDIT)],
    body: AdminUserCreate,
    admin_user_service: FromDishka[AdminUserService],
) -> AdminUserResponse:
    admin = await admin_user_service.create(actor, body)
    return AdminUserResponse.from_dto(admin)


@router.patch("/{admin_user_id}")
async def update_admin(
    actor: Annotated[AdminPrincipal, require(Permission.ADMINS_EDIT)],
    admin_user_id: int,
    patch: AdminUserUpdate,
    admin_user_service: FromDishka[AdminUserService],
) -> AdminUserResponse:
    admin = await admin_user_service.update(actor, admin_user_id, patch)
    return AdminUserResponse.from_dto(admin)
