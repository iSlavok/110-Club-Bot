from app.enums import Permission, PermissionGroup, known_permissions
from app.exceptions import EmptyUpdateError, RoleInUseError, RoleNotFoundError, RoleTitleTakenError
from app.models import Role
from app.repositories import AdminUserRepository, RoleRepository
from app.schemas import AdminPrincipal, PermissionInfo, RoleCreate, RoleDTO, RoleUpdate
from app.services.permission_guard import ensure_within_own_permissions

PERMISSION_CATALOG = (
    PermissionInfo(code=Permission.CLUBS_VIEW, title="Просмотр клубов и блоков", group=PermissionGroup.CLUBS),
    PermissionInfo(code=Permission.CLUBS_EDIT, title="Создание и изменение клубов", group=PermissionGroup.CLUBS),
    PermissionInfo(code=Permission.BLOCKS_EDIT, title="Управление блоками", group=PermissionGroup.CLUBS),
    PermissionInfo(code=Permission.SYNC_RUN, title="Запуск синка с таблицей", group=PermissionGroup.CLUBS),
    PermissionInfo(code=Permission.USERS_VIEW, title="Просмотр пользователей бота", group=PermissionGroup.USERS),
    PermissionInfo(code=Permission.ADMINS_VIEW, title="Просмотр админов и ролей", group=PermissionGroup.ADMINS),
    PermissionInfo(code=Permission.ADMINS_EDIT, title="Добавление и изменение админов", group=PermissionGroup.ADMINS),
    PermissionInfo(code=Permission.ROLES_EDIT, title="Управление ролями", group=PermissionGroup.ADMINS),
    PermissionInfo(code=Permission.SETTINGS_EDIT, title="Изменение настроек бота", group=PermissionGroup.SETTINGS),
)


class RoleService:
    def __init__(
        self,
        role_repository: RoleRepository,
        admin_user_repository: AdminUserRepository,
    ) -> None:
        self._role_repository = role_repository
        self._admin_user_repository = admin_user_repository

    @staticmethod
    def list_permissions() -> list[PermissionInfo]:
        return list(PERMISSION_CATALOG)

    async def list_roles(self) -> list[RoleDTO]:
        roles = await self._role_repository.list_all()
        return [RoleDTO.from_orm_obj(role) for role in roles]

    async def create(self, actor: AdminPrincipal, data: RoleCreate) -> RoleDTO:
        ensure_within_own_permissions(actor, data.permissions)
        await self._ensure_title_free(data.title)
        role = Role(title=data.title, permissions=sorted(set(data.permissions)))
        self._role_repository.add(role)
        await self._role_repository.flush()
        return RoleDTO.from_orm_obj(role)

    async def update(self, actor: AdminPrincipal, role_id: int, patch: RoleUpdate) -> RoleDTO:
        if patch.is_empty():
            raise EmptyUpdateError
        role = await self._get(role_id)
        new_permissions = set(patch.permissions.apply(list(known_permissions(role.permissions))))
        ensure_within_own_permissions(actor, known_permissions(role.permissions) | new_permissions)
        if patch.title.is_set and patch.title.value != role.title:
            await self._ensure_title_free(patch.title.apply(role.title))
        role.title = patch.title.apply(role.title)
        role.permissions = sorted(new_permissions)
        await self._role_repository.flush()
        return RoleDTO.from_orm_obj(role)

    async def delete(self, actor: AdminPrincipal, role_id: int) -> None:
        role = await self._get(role_id)
        ensure_within_own_permissions(actor, known_permissions(role.permissions))
        if await self._admin_user_repository.exists_with_role(role.id):
            raise RoleInUseError
        await self._role_repository.delete(role)
        await self._role_repository.flush()

    async def _get(self, role_id: int) -> Role:
        role = await self._role_repository.get_by_id(role_id)
        if role is None:
            raise RoleNotFoundError(role_id)
        return role

    async def _ensure_title_free(self, title: str) -> None:
        if await self._role_repository.get_by_title(title) is not None:
            raise RoleTitleTakenError(title)
