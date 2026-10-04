from itertools import count
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models import User

_ids = count(1)


async def make_user(session: AsyncSession, **overrides: Any) -> User:
    n = next(_ids)
    user = User(**{"tg_id": 100_000 + n, "tg_username": f"user{n}", "full_name": f"User {n}", **overrides})
    session.add(user)
    await session.flush()
    return user
