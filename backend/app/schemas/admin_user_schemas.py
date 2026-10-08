from datetime import datetime
from typing import Annotated, Self

from pydantic import BaseModel, Field, PositiveInt, StringConstraints

from app.models import AdminUser
from app.models.user import TG_FULL_NAME_MAX_LEN
from app.schemas.patch_schemas import Maybe, PatchSchema
from app.schemas.role_schemas import RoleDTO

type AdminName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=TG_FULL_NAME_MAX_LEN)]


class AdminUserDTO(BaseModel):
    id: int
    tg_id: int
    name: str
    role_id: int | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    @classmethod
    def from_orm_obj(cls, admin: AdminUser) -> Self:
        return cls(
            id=admin.id,
            tg_id=admin.tg_id,
            name=admin.name,
            role_id=admin.role_id,
            is_active=admin.is_active,
            created_at=admin.created_at,
            updated_at=admin.updated_at,
        )


class AdminUserWithRoleDTO(AdminUserDTO):
    role: RoleDTO | None
    # Not a column: owners come from AUTH_OWNER_IDS, the admin list always shows it next to the role.
    is_owner: bool

    # Separate name, not an override of from_orm_obj: the role must be loaded and is_owner comes from settings.
    @classmethod
    def from_orm_obj_with_role(cls, admin: AdminUser, *, is_owner: bool) -> Self:
        return cls(
            id=admin.id,
            tg_id=admin.tg_id,
            name=admin.name,
            role_id=admin.role_id,
            is_active=admin.is_active,
            created_at=admin.created_at,
            updated_at=admin.updated_at,
            role=RoleDTO.from_orm_obj(admin.role) if admin.role else None,
            is_owner=is_owner,
        )


class AdminUserCreate(BaseModel):
    tg_id: PositiveInt = Field(description="Telegram user id of the new admin")
    name: AdminName = Field(description="Display name")
    role_id: int = Field(description="Role to assign")


class AdminUserUpdate(PatchSchema):
    name: Maybe[AdminName] = Field(description="Display name")
    role_id: Maybe[int] = Field(description="Role to assign")
    is_active: Maybe[bool] = Field(description="Inactive admins cannot log in")
