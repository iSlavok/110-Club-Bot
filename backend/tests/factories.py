from datetime import UTC, datetime, timedelta
from itertools import count
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import Permission
from app.models import AdminUser, Block, Club, Membership, Role, User

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
    admin = AdminUser(**{"tg_id": 900_000 + n, "name": f"Admin {n}", "role": role, **overrides})
    session.add(admin)
    await session.flush()
    return admin


async def make_club(session: AsyncSession, **overrides: Any) -> Club:
    n = next(_ids)
    club = Club(**{"title": f"Club {n}", **overrides})
    session.add(club)
    await session.flush()
    return club


async def make_block(session: AsyncSession, club: Club, **overrides: Any) -> Block:
    n = next(_ids)
    starts_at = overrides.pop("starts_at", datetime(2026, 9, 1, tzinfo=UTC))
    block = Block(
        **{
            "club_id": club.id,
            "title": f"Block {n}",
            "sheet_column_title": f"Блок {n}",
            "starts_at": starts_at,
            "ends_at": starts_at + timedelta(days=60),
            **overrides,
        },
    )
    session.add(block)
    await session.flush()
    return block


async def make_membership(session: AsyncSession, block: Block, **overrides: Any) -> Membership:
    n = next(_ids)
    membership = Membership(**{"block_id": block.id, "vk_id": 500_000 + n, **overrides})
    session.add(membership)
    await session.flush()
    return membership
