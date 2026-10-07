from itertools import count
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import Permission
from app.models import AdminUser, Role, User

_ids = count(1)


async def make_user(session: AsyncSession, **overrides: Any) -> User:
    n = next(_ids)
    user = User(**{"tg_id": 100_000 + n, "tg_username": f"user{n}", "full_name": f"User {n}", **overrides})
    session.add(user)
    await session.flush()
    return user


async def make_role(session: AsyncSession, *permissions: Permission, **overrides: Any) -> Role:
    n = next(_ids)
    role = Role(**{"title": f"Role {n}", "permissions": [str(p) for p in permissions], **overrides})
    session.add(role)
    await session.flush()
    return role


async def make_admin_user(session: AsyncSession, role: Role | None = None, **overrides: Any) -> AdminUser:
    n = next(_ids)
    admin = AdminUser(**{"tg_id": 900_000 + n, "name": f"Admin {n}", "role_id": role.id if role else None, **overrides})
    session.add(admin)
    await session.flush()
    return admin
