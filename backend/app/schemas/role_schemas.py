from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, Field, StringConstraints

from app.enums import Permission, PermissionGroup, known_permissions
from app.models import Role
from app.models.role import ROLE_TITLE_MAX_LEN
from app.schemas.patch_schemas import Maybe, PatchSchema

type RoleTitle = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=ROLE_TITLE_MAX_LEN)]


class PermissionInfo(BaseModel):
    code: Permission
    title: str
    group: PermissionGroup


class RoleDTO(BaseModel):
    id: int
    title: str
    permissions: list[Permission]
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_obj(cls, role: Role) -> Self:
        return cls(
            id=role.id,
            title=role.title,
            permissions=sorted(known_permissions(role.permissions)),
            created_at=role.created_at,
            updated_at=role.updated_at,
        )


class RoleCreate(BaseModel):
    title: RoleTitle = Field(description="Unique role name")
    permissions: list[Permission] = Field(description="Permissions granted by the role")


class RoleUpdate(PatchSchema):
    title: Maybe[RoleTitle] = Field(description="Unique role name")
    permissions: Maybe[list[Permission]] = Field(description="Permissions granted by the role")
