from tests.factories import make_user


async def test_server_defaults_are_readable_after_flush(db_session) -> None:
    user = await make_user(db_session)
    created_at = user.created_at

    user.full_name = "Новое имя"
    await db_session.flush()

    assert user.updated_at >= created_at
