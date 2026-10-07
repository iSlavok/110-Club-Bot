import pytest

from app.enums import Permission
from tests.factories import make_admin_user, make_role

P = Permission


@pytest.fixture
async def editor(db_session):
    return await make_admin_user(db_session, await make_role(db_session, P.ADMINS_VIEW, P.ADMINS_EDIT, P.ROLES_EDIT))


async def test_requires_permission(api_client, login_as, db_session) -> None:
    await login_as(await make_admin_user(db_session, await make_role(db_session, P.CLUBS_VIEW)))

    response = await api_client.get("/api/v1/admins")

    assert response.status_code == 403
    assert response.json()["code"] == "PERMISSION_DENIED"


async def test_admin_crud_flow(api_client, login_as, editor) -> None:
    await login_as(editor)

    role = await api_client.post("/api/v1/roles", json={"title": "Куратор", "permissions": ["admins.view"]})
    created = await api_client.post(
        "/api/v1/admins",
        json={"tg_id": 31337, "name": "Мария", "role_id": role.json()["id"]},
    )
    updated = await api_client.patch(f"/api/v1/admins/{created.json()['id']}", json={"is_active": False})
    listed = await api_client.get("/api/v1/admins", params={"per_page": 1})

    assert role.status_code == 201
    assert created.status_code == 201
    assert created.json()["role"] == {"id": role.json()["id"], "title": "Куратор"}
    assert updated.json()["is_active"] is False
    assert listed.json()["total_items"] == 2
    assert listed.json()["total_pages"] == 2
    assert len(listed.json()["items"]) == 1


async def test_role_lifecycle_and_conflicts(api_client, login_as, editor) -> None:
    await login_as(editor)

    created = await api_client.post("/api/v1/roles", json={"title": "Временная", "permissions": []})
    role_id = created.json()["id"]
    duplicate = await api_client.post("/api/v1/roles", json={"title": "Временная", "permissions": []})
    escalation = await api_client.patch(f"/api/v1/roles/{role_id}", json={"permissions": ["users.view"]})
    empty = await api_client.patch(f"/api/v1/roles/{role_id}", json={})
    deleted = await api_client.delete(f"/api/v1/roles/{role_id}")

    assert duplicate.status_code == 409
    assert duplicate.json()["code"] == "ROLE_TITLE_TAKEN"
    assert escalation.status_code == 403
    assert escalation.json()["code"] == "PERMISSION_ESCALATION"
    assert empty.status_code == 400
    assert empty.json()["code"] == "EMPTY_UPDATE"
    assert deleted.status_code == 204


async def test_permission_catalog_covers_every_permission(api_client, login_as, editor) -> None:
    await login_as(editor)

    response = await api_client.get("/api/v1/permissions")

    assert {item["code"] for item in response.json()} == {str(p) for p in Permission}
