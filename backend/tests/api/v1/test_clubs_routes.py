from datetime import UTC, datetime

import pytest

from app.enums import Permission
from tests.factories import make_admin_user, make_block, make_club, make_membership, make_role, make_user

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
    assert blocks.json()["items"][0]["members_count"] == 0
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


async def test_club_stats(api_client, login_as, db_session) -> None:
    await login_as(await make_admin_user(db_session, await make_role(db_session, P.CLUBS_VIEW)))
    club = await make_club(db_session)
    block = await make_block(db_session, club, title="Блок 5", starts_at=datetime(2026, 9, 1, tzinfo=UTC))
    membership = await make_membership(db_session, block)
    await make_membership(db_session, block)
    await make_user(db_session, vk_id=membership.vk_id)

    response = await api_client.get(f"/api/v1/clubs/{club.id}/stats")

    assert response.status_code == 200
    current_block = response.json()["current_block"]
    assert current_block["block"]["id"] == block.id
    assert current_block["block"]["title"] == "Блок 5"
    assert current_block["members"] == 2
    assert current_block["members_with_tg"] == 1


async def test_club_stats_between_blocks(api_client, login_as, manager, db_session) -> None:
    await login_as(manager)
    club = await make_club(db_session)

    response = await api_client.get(f"/api/v1/clubs/{club.id}/stats")

    assert response.status_code == 200
    assert response.json() == {"current_block": None}


async def test_club_stats_require_clubs_view(api_client, login_as, db_session) -> None:
    await login_as(await make_admin_user(db_session, await make_role(db_session)))
    club = await make_club(db_session)

    response = await api_client.get(f"/api/v1/clubs/{club.id}/stats")

    assert response.status_code == 403
    assert response.json()["code"] == "PERMISSION_DENIED"


async def test_stats_of_unknown_club_is_404(api_client, login_as, manager) -> None:
    await login_as(manager)

    response = await api_client.get("/api/v1/clubs/999999/stats")

    assert response.status_code == 404
    assert response.json()["code"] == "CLUB_NOT_FOUND"


async def test_block_members_need_users_view(api_client, login_as, db_session, manager) -> None:
    block = await make_block(db_session, await make_club(db_session))
    await make_membership(db_session, block, vk_id=501)
    await make_user(db_session, vk_id=501, full_name="Ученик Тестов", tg_username=None)

    await login_as(manager)
    denied = await api_client.get(f"/api/v1/blocks/{block.id}/members")
    await login_as(await make_admin_user(db_session, await make_role(db_session, P.USERS_VIEW)))
    allowed = await api_client.get(f"/api/v1/blocks/{block.id}/members")

    assert denied.status_code == 403
    assert allowed.status_code == 200
    item = allowed.json()["items"][0]
    assert item["vk_id"] == 501
    assert item["user"]["full_name"] == "Ученик Тестов"
    assert item["user"]["tg_username"] is None


async def test_members_of_unknown_block_is_404(api_client, login_as, db_session) -> None:
    await login_as(await make_admin_user(db_session, await make_role(db_session, P.USERS_VIEW)))

    response = await api_client.get("/api/v1/blocks/999999/members")

    assert response.status_code == 404
    assert response.json()["code"] == "BLOCK_NOT_FOUND"
