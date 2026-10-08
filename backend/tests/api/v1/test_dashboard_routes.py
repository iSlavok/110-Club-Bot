from tests.factories import make_admin_user, make_role, make_user


async def test_any_admin_sees_stats(api_client, login_as, db_session) -> None:
    await login_as(await make_admin_user(db_session, await make_role(db_session)))
    await make_user(db_session)

    response = await api_client.get("/api/v1/dashboard/stats")

    assert response.status_code == 200
    assert response.json() == {"active_clubs": 0, "current_blocks": 0, "users": 1, "users_with_vk": 0}


async def test_stats_require_login(api_client) -> None:
    response = await api_client.get("/api/v1/dashboard/stats")

    assert response.status_code == 401
