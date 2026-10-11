import pytest

from app.enums import Permission
from app.exceptions import EmptyUpdateError, PermissionEscalationError, RoleInUseError, RoleTitleTakenError
from app.models import Role
from app.schemas import AdminPrincipal, RoleCreate, RoleUpdate
from app.services import RoleService
from tests.factories import make_admin_user, make_role

P = Permission


def _actor(*permissions: Permission, is_owner: bool = False) -> AdminPrincipal:
    return AdminPrincipal(id=0, tg_id=0, name="Actor", is_owner=is_owner, permissions=frozenset(permissions))


OWNER = _actor(*Permission, is_owner=True)


@pytest.fixture
async def service(request_container) -> RoleService:
    return await request_container.get(RoleService)


async def test_create_role(service, db_session) -> None:
    role = await service.create(OWNER, RoleCreate(title="  Куратор ", permissions=[P.USERS_VIEW, P.CLUBS_VIEW]))

    stored = await db_session.get(Role, role.id)
    assert stored is not None
    assert stored.title == "Куратор"
    assert role.permissions == [P.CLUBS_VIEW, P.USERS_VIEW]


async def test_role_titles_are_unique(service, db_session) -> None:
    await make_role(db_session, title="Куратор")

    with pytest.raises(RoleTitleTakenError):
        await service.create(OWNER, RoleCreate(title="Куратор", permissions=[]))


async def test_cannot_grant_missing_permission(service) -> None:
    actor = _actor(P.ROLES_EDIT)

    with pytest.raises(PermissionEscalationError):
        await service.create(actor, RoleCreate(title="Супер", permissions=[P.ADMINS_EDIT]))


async def test_update_replaces_permissions_and_keeps_title(service, db_session) -> None:
    role = await make_role(db_session, P.USERS_VIEW, title="Куратор")

    updated = await service.update(OWNER, role.id, RoleUpdate.model_validate({"permissions": [P.CLUBS_VIEW]}))

    assert updated.title == "Куратор"
    assert updated.permissions == [P.CLUBS_VIEW]


async def test_cannot_edit_role_stronger_than_actor(service, db_session) -> None:
    role = await make_role(db_session, P.USERS_VIEW, P.ADMINS_EDIT)
    actor = _actor(P.ROLES_EDIT, P.USERS_VIEW)

    with pytest.raises(PermissionEscalationError):
        await service.update(actor, role.id, RoleUpdate.model_validate({"title": "Новое имя"}))


async def test_empty_update_is_rejected(service, db_session) -> None:
    role = await make_role(db_session)

    with pytest.raises(EmptyUpdateError):
        await service.update(OWNER, role.id, RoleUpdate.model_validate({}))


async def test_assigned_role_cannot_be_deleted(service, db_session) -> None:
    role = await make_role(db_session)
    await make_admin_user(db_session, role)

    with pytest.raises(RoleInUseError):
        await service.delete(OWNER, role.id)


async def test_delete_unused_role(service, db_session) -> None:
    role = await make_role(db_session)

    await service.delete(OWNER, role.id)

    assert await db_session.get(Role, role.id) is None
