from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, status

from api.core.auth import require
from api.schemas.role_schemas import PermissionResponse, RoleResponse
from app.enums import Permission
from app.schemas import AdminPrincipal, RoleCreate, RoleUpdate
from app.services import RoleService

router = APIRouter(tags=["roles"], route_class=DishkaRoute)


@router.get("/permissions", dependencies=[require(Permission.ADMINS_VIEW)])
async def list_permissions(role_service: FromDishka[RoleService]) -> list[PermissionResponse]:
    return [PermissionResponse.from_dto(info) for info in role_service.list_permissions()]


@router.get("/roles", dependencies=[require(Permission.ADMINS_VIEW)])
async def list_roles(role_service: FromDishka[RoleService]) -> list[RoleResponse]:
    roles = await role_service.list_roles()
    return [RoleResponse.from_dto(role) for role in roles]


@router.post("/roles", status_code=status.HTTP_201_CREATED)
async def create_role(
    actor: Annotated[AdminPrincipal, require(Permission.ROLES_EDIT)],
    body: RoleCreate,
    role_service: FromDishka[RoleService],
) -> RoleResponse:
    role = await role_service.create(actor, body)
    return RoleResponse.from_dto(role)


@router.patch("/roles/{role_id}")
async def update_role(
    actor: Annotated[AdminPrincipal, require(Permission.ROLES_EDIT)],
    role_id: int,
    patch: RoleUpdate,
    role_service: FromDishka[RoleService],
) -> RoleResponse:
    role = await role_service.update(actor, role_id, patch)
    return RoleResponse.from_dto(role)


@router.delete("/roles/{role_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_role(
    actor: Annotated[AdminPrincipal, require(Permission.ROLES_EDIT)],
    role_id: int,
    role_service: FromDishka[RoleService],
) -> None:
    await role_service.delete(actor, role_id)
