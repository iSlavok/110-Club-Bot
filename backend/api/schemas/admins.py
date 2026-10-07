from typing import Self

from pydantic import BaseModel, Field

from app.schemas import AdminUserWithRoleDTO, RoleDTO


class RoleRefResponse(BaseModel):
    id: int = Field(description="Role id")
    title: str = Field(description="Role name")

    @classmethod
    def from_dto(cls, role: RoleDTO) -> Self:
        return cls(id=role.id, title=role.title)


class AdminUserResponse(BaseModel):
    id: int = Field(description="Admin account id")
    tg_id: int = Field(description="Telegram user id")
    name: str = Field(description="Display name")
    is_active: bool = Field(description="Inactive admins cannot log in")
    is_owner: bool = Field(description="Owner from server config: has every permission, cannot be edited")
    role: RoleRefResponse | None = Field(description="Assigned role; null for owners")

    @classmethod
    def from_dto(cls, admin: AdminUserWithRoleDTO) -> Self:
        return cls(
            id=admin.id,
            tg_id=admin.tg_id,
            name=admin.name,
            is_active=admin.is_active,
            is_owner=admin.is_owner,
            role=RoleRefResponse.from_dto(admin.role) if admin.role else None,
        )
