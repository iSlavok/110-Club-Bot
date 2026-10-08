import pytest

from app.enums import Permission
from tests.factories import make_admin_user, make_role

P = Permission


@pytest.fixture
async def manager(db_session):
    role = await make_role(db_session, P.CLUBS_VIEW, P.CLUBS_EDIT, P.BLOCKS_EDIT)
    return await make_admin_user(db_session, role)


async def test_viewer_cannot_edit(api_client, login_as, db_session) -> None:
    await login_as(await make_admin_user(db_session, await make_role(db_session, P.CLUBS_VIEW)))

    listed = await api_client.get("/api/v1/clubs")
    created = await api_client.post("/api/v1/clubs", json={"title": "Клуб"})

    assert listed.status_code == 200
    assert created.status_code == 403


async def test_club_and_block_flow(api_client, login_as, manager) -> None:
    await login_as(manager)

    club = (await api_client.post("/api/v1/clubs", json={"title": "Клуб 110", "chat_id": -100500})).json()
    patched = await api_client.patch(f"/api/v1/clubs/{club['id']}", json={"reminders_topic_id": 7})
    block = await api_client.post(
        f"/api/v1/clubs/{club['id']}/blocks",
        json={
            "title": "Блок 5",
            "sheet_column_title": "Блок 5",
            "starts_at": "2026-09-01T00:00:00+03:00",
            "ends_at": "2026-11-01T00:00:00+03:00",
        },
    )
    blocks = await api_client.get(f"/api/v1/clubs/{club['id']}/blocks")
    deleted = await api_client.delete(f"/api/v1/blocks/{block.json()['id']}")

    assert patched.json()["reminders_topic_id"] == 7
    assert block.status_code == 201
    assert block.json()["starts_at"] == "2026-08-31T21:00:00Z"
    assert blocks.json()["total_items"] == 1
    assert deleted.status_code == 204


async def test_block_period_validation(api_client, login_as, manager) -> None:
    await login_as(manager)
    club = (await api_client.post("/api/v1/clubs", json={"title": "Клуб"})).json()

    response = await api_client.post(
        f"/api/v1/clubs/{club['id']}/blocks",
        json={
            "title": "Блок",
            "sheet_column_title": "Блок",
            "starts_at": "2026-11-01T00:00:00Z",
            "ends_at": "2026-09-01T00:00:00Z",
        },
    )

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_FAILED"


async def test_unknown_club_is_404(api_client, login_as, manager) -> None:
    await login_as(manager)

    response = await api_client.get("/api/v1/clubs/999999")

    assert response.status_code == 404
    assert response.json()["code"] == "CLUB_NOT_FOUND"
