import pytest

from app.enums import Permission
from tests.factories import make_admin_user, make_role

TOO_BIG = 10**20


@pytest.fixture
async def manager(db_session):
    role = await make_role(db_session, Permission.CLUBS_VIEW, Permission.CLUBS_EDIT, Permission.USERS_VIEW)
    return await make_admin_user(db_session, role)


@pytest.mark.parametrize(
    "payload",
    [
        {"id": 1, "first_name": "A", "auth_date": TOO_BIG, "hash": "a" * 64},
        {"id": TOO_BIG, "first_name": "A", "auth_date": 1, "hash": "a" * 64},
        {"id": 1, "first_name": "A", "auth_date": 1, "hash": "я" * 64},
    ],
)
async def test_malformed_widget_payload_is_rejected_before_the_service(api_client, payload) -> None:
    response = await api_client.post("/api/v1/auth/widget", json=payload)

    assert response.status_code == 422
    assert response.json()["code"] == "VALIDATION_FAILED"


@pytest.mark.parametrize(
    "path",
    [
        f"/api/v1/clubs/{TOO_BIG}",
        f"/api/v1/clubs/{TOO_BIG}/blocks",
        f"/api/v1/clubs?page={TOO_BIG}",
    ],
)
async def test_out_of_range_ids_and_pages_are_rejected(api_client, login_as, manager, path) -> None:
    await login_as(manager)

    response = await api_client.get(path)

    assert response.status_code == 422


@pytest.mark.parametrize(
    "body",
    [
        {"title": "Клуб", "reminders_topic_id": 2**31},
        {"title": "Клуб", "chat_id": -(2**63) - 1},
    ],
)
async def test_values_beyond_column_types_are_rejected(api_client, login_as, manager, body) -> None:
    await login_as(manager)

    response = await api_client.post("/api/v1/clubs", json=body)

    assert response.status_code == 422


async def test_huge_numeric_search_finds_nothing(api_client, login_as, manager) -> None:
    await login_as(manager)

    response = await api_client.get("/api/v1/users", params={"q": str(TOO_BIG)})

    assert response.status_code == 200
    assert response.json()["total_items"] == 0
