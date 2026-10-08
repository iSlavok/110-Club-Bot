from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import known_permissions
from app.exceptions import (
    AdminAlreadyExistsError,
    AdminUserNotFoundError,
    EmptyUpdateError,
    OwnAccessChangeError,
    OwnerNotEditableError,
    RoleNotFoundError,
)
from app.models import AdminUser, Role
from app.repositories import AdminSessionRepository, AdminUserRepository, RoleRepository
from app.schemas import (
    AdminPrincipal,
    AdminUserCreate,
    AdminUserUpdate,
    AdminUserWithRoleDTO,
    PageParams,
    Paginated,
)
from app.services.admin_access_resolver import AdminAccessResolver
from app.services.permission_guard import ensure_within_own_permissions


class AdminUserService:
    def __init__(
        self,
        session: AsyncSession,
        admin_user_repository: AdminUserRepository,
        role_repository: RoleRepository,
        admin_session_repository: AdminSessionRepository,
        access_resolver: AdminAccessResolver,
    ) -> None:
        self._session = session
        self._admin_user_repository = admin_user_repository
        self._role_repository = role_repository
        self._admin_session_repository = admin_session_repository
        self._access_resolver = access_resolver

    async def list_page(self, page: PageParams) -> Paginated[AdminUserWithRoleDTO]:
        admins = await self._admin_user_repository.list_page(limit=page.per_page, offset=page.offset)
        return Paginated(items=[self._to_dto(admin) for admin in admins.items], total=admins.total)

    async def create(self, actor: AdminPrincipal, data: AdminUserCreate) -> AdminUserWithRoleDTO:
        if self._access_resolver.is_owner(data.tg_id):
            raise OwnerNotEditableError
        if await self._admin_user_repository.get_by_tg_id(data.tg_id) is not None:
            raise AdminAlreadyExistsError(data.tg_id)
        role = await self._get_assignable_role(actor, data.role_id)
        admin = AdminUser(tg_id=data.tg_id, name=data.name, role=role)
        self._admin_user_repository.add(admin)
        await self._session.commit()
        return self._to_dto(admin)

    async def update(self, actor: AdminPrincipal, admin_user_id: int, patch: AdminUserUpdate) -> AdminUserWithRoleDTO:
        if patch.is_empty():
            raise EmptyUpdateError
        admin = await self._admin_user_repository.get_with_role(admin_user_id)
        if admin is None:
            raise AdminUserNotFoundError(admin_user_id)
        if self._access_resolver.is_owner(admin.tg_id):
            raise OwnerNotEditableError
        if admin.id == actor.id and (patch.role_id.is_set or patch.is_active.is_set):
            raise OwnAccessChangeError
        if admin.role is not None:
            ensure_within_own_permissions(actor, known_permissions(admin.role.permissions))

        admin.name = patch.name.apply(admin.name)
        new_role_id = patch.role_id.apply(admin.role_id)
        if new_role_id is not None and new_role_id != admin.role_id:
            admin.role = await self._get_assignable_role(actor, new_role_id)
        admin.is_active = patch.is_active.apply(admin.is_active)
        if not admin.is_active:
            await self._admin_session_repository.delete_for_admin(admin.id)
        await self._session.commit()
        return self._to_dto(admin)

    async def _get_assignable_role(self, actor: AdminPrincipal, role_id: int) -> Role:
        role = await self._role_repository.get_by_id(role_id)
        if role is None:
            raise RoleNotFoundError(role_id)
        ensure_within_own_permissions(actor, known_permissions(role.permissions))
        return role

    def _to_dto(self, admin: AdminUser) -> AdminUserWithRoleDTO:
        is_owner = self._access_resolver.is_owner(admin.tg_id)
        return AdminUserWithRoleDTO.from_orm_obj_with_role(admin, is_owner=is_owner)
