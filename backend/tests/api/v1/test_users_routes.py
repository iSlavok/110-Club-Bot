from datetime import UTC, datetime

from app.enums import Permission
from tests.factories import make_admin_user, make_role, make_user


async def test_list_users_with_search(api_client, login_as, db_session) -> None:
    await login_as(await make_admin_user(db_session, await make_role(db_session, Permission.USERS_VIEW)))
    user = await make_user(
        db_session,
        full_name="Анна Белова",
        vk_id=42,
        vk_linked_at=datetime(2026, 9, 1, 9, 0, tzinfo=UTC),
    )
    await make_user(db_session, full_name="Борис")

    response = await api_client.get("/api/v1/users", params={"q": "анна"})

    assert response.status_code == 200
    body = response.json()
    assert body["total_items"] == 1
    assert body["items"][0]["id"] == user.id
    assert body["items"][0]["vk_id"] == 42
    assert body["items"][0]["vk_linked_at"] == "2026-09-01T09:00:00Z"


async def test_users_require_permission(api_client, login_as, db_session) -> None:
    await login_as(await make_admin_user(db_session, await make_role(db_session)))

    response = await api_client.get("/api/v1/users")

    assert response.status_code == 403
