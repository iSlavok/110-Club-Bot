from typing import Self

from pydantic import BaseModel, Field

from app.enums import Permission, PermissionGroup
from app.schemas import PermissionInfo, RoleDTO


class PermissionResponse(BaseModel):
    code: Permission = Field(description="Permission code checked by the API")
    title: str = Field(description="Human-readable name")
    group: PermissionGroup = Field(description="Section of the admin panel the permission belongs to")

    @classmethod
    def from_dto(cls, info: PermissionInfo) -> Self:
        return cls(code=info.code, title=info.title, group=info.group)


class RoleResponse(BaseModel):
    id: int = Field(description="Role id")
    title: str = Field(description="Unique role name")
    permissions: list[Permission] = Field(description="Permissions granted by the role")

    @classmethod
    def from_dto(cls, role: RoleDTO) -> Self:
        return cls(id=role.id, title=role.title, permissions=role.permissions)
