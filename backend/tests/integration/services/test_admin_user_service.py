import pytest
from sqlalchemy import select

from app.enums import Permission
from app.exceptions import (
    AdminAlreadyExistsError,
    OwnAccessChangeError,
    OwnerNotEditableError,
    PermissionEscalationError,
    RoleNotFoundError,
)
from app.models import AdminSession
from app.schemas import AdminPrincipal, AdminUserCreate, AdminUserUpdate, PageParams
from app.services import AdminAccessResolver, AdminSessionService, AdminUserService
from tests.factories import make_admin_user, make_role
from tests.providers import OWNER_TG_ID

P = Permission


def _actor(*permissions: Permission, actor_id: int = 0) -> AdminPrincipal:
    return AdminPrincipal(id=actor_id, tg_id=0, name="Actor", is_owner=False, permissions=frozenset(permissions))


EDITOR = _actor(P.ADMINS_EDIT, P.CLUBS_VIEW, P.USERS_VIEW)


@pytest.fixture
async def service(request_container) -> AdminUserService:
    return await request_container.get(AdminUserService)


async def test_create_admin_with_role(service, db_session) -> None:
    role = await make_role(db_session, P.CLUBS_VIEW, title="Куратор")

    admin = await service.create(EDITOR, AdminUserCreate(tg_id=55, name="Мария", role_id=role.id))

    assert admin.role is not None
    assert admin.role.title == "Куратор"
    assert not admin.is_owner


async def test_create_rejects_duplicate_owner_and_unknown_role(service, db_session) -> None:
    role = await make_role(db_session)
    existing = await make_admin_user(db_session, role)

    with pytest.raises(AdminAlreadyExistsError):
        await service.create(EDITOR, AdminUserCreate(tg_id=existing.tg_id, name="Дубль", role_id=role.id))
    with pytest.raises(OwnerNotEditableError):
        await service.create(EDITOR, AdminUserCreate(tg_id=OWNER_TG_ID, name="Владелец", role_id=1))
    with pytest.raises(RoleNotFoundError):
        await service.create(EDITOR, AdminUserCreate(tg_id=56, name="Без роли", role_id=999_999))


async def test_cannot_assign_stronger_role(service, db_session) -> None:
    strong = await make_role(db_session, P.ROLES_EDIT)

    with pytest.raises(PermissionEscalationError):
        await service.create(EDITOR, AdminUserCreate(tg_id=57, name="Кто-то", role_id=strong.id))


async def test_cannot_edit_admin_with_stronger_role(service, db_session) -> None:
    target = await make_admin_user(db_session, await make_role(db_session, P.ROLES_EDIT))

    with pytest.raises(PermissionEscalationError):
        await service.update(EDITOR, target.id, AdminUserUpdate.model_validate({"name": "Новое"}))


async def test_cannot_change_own_access(service, db_session) -> None:
    me = await make_admin_user(db_session, await make_role(db_session, P.ADMINS_EDIT))
    actor = _actor(P.ADMINS_EDIT, actor_id=me.id)

    renamed = await service.update(actor, me.id, AdminUserUpdate.model_validate({"name": "Я"}))
    with pytest.raises(OwnAccessChangeError):
        await service.update(actor, me.id, AdminUserUpdate.model_validate({"is_active": False}))

    assert renamed.name == "Я"


async def test_owner_is_not_editable(service, db_session) -> None:
    owner = await make_admin_user(db_session, tg_id=OWNER_TG_ID)

    with pytest.raises(OwnerNotEditableError):
        await service.update(EDITOR, owner.id, AdminUserUpdate.model_validate({"name": "X"}))


async def test_deactivation_ends_sessions(service, request_container, db_session) -> None:
    target = await make_admin_user(db_session, await make_role(db_session, P.CLUBS_VIEW))
    principal = (await request_container.get(AdminAccessResolver)).resolve(target)
    assert principal is not None
    await (await request_container.get(AdminSessionService)).start(principal)

    updated = await service.update(EDITOR, target.id, AdminUserUpdate.model_validate({"is_active": False}))

    assert not updated.is_active
    assert await db_session.scalar(select(AdminSession).where(AdminSession.admin_user_id == target.id)) is None


async def test_change_role(service, db_session) -> None:
    target = await make_admin_user(db_session, await make_role(db_session, P.CLUBS_VIEW))
    new_role = await make_role(db_session, P.USERS_VIEW, title="Аналитик")

    updated = await service.update(EDITOR, target.id, AdminUserUpdate.model_validate({"role_id": new_role.id}))

    assert updated.role is not None
    assert updated.role.title == "Аналитик"


async def test_list_marks_owners(service, db_session) -> None:
    await make_admin_user(db_session, tg_id=OWNER_TG_ID, name="Владелец")
    await make_admin_user(db_session, await make_role(db_session), name="Куратор")

    page = await service.list_page(PageParams())

    assert page.total == 2
    assert {admin.name: admin.is_owner for admin in page.items} == {"Владелец": True, "Куратор": False}
