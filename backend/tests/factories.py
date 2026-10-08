from datetime import UTC, datetime, timedelta
from itertools import count
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.enums import Permission, SheetSyncStatus
from app.models import (
    AdminSession,
    AdminUser,
    AppSettings,
    Block,
    Club,
    LoginCode,
    Membership,
    Role,
    SheetSync,
    User,
    VkAuthRequest,
)
from app.models.app_settings import APP_SETTINGS_ID

_ids = count(1)


# The only settings row comes from the migration, so tests change it instead of creating one.
async def set_app_settings(session: AsyncSession, **values: Any) -> AppSettings:
    settings = await session.get(AppSettings, APP_SETTINGS_ID)
    assert settings is not None, "app_settings row is created by the migration"
    for name, value in values.items():
        setattr(settings, name, value)
    await session.flush()
    return settings


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


async def make_admin_session(session: AsyncSession, admin: AdminUser, **overrides: Any) -> AdminSession:
    n = next(_ids)
    admin_session = AdminSession(
        **{
            "token_hash": f"{n:064x}",
            "admin_user_id": admin.id,
            "expires_at": datetime(2026, 10, 2, tzinfo=UTC),
            **overrides,
        },
    )
    session.add(admin_session)
    await session.flush()
    return admin_session


async def make_login_code(session: AsyncSession, admin: AdminUser, **overrides: Any) -> LoginCode:
    n = next(_ids)
    login_code = LoginCode(
        **{
            "code_hash": f"{n:064x}",
            "admin_user_id": admin.id,
            "expires_at": datetime(2026, 10, 1, 9, 5, tzinfo=UTC),
            **overrides,
        },
    )
    session.add(login_code)
    await session.flush()
    return login_code


async def make_vk_auth_request(session: AsyncSession, user: User, **overrides: Any) -> VkAuthRequest:
    n = next(_ids)
    request = VkAuthRequest(
        **{
            "state_hash": f"{n:064x}",
            "user_id": user.id,
            "code_verifier": f"verifier-{n}",
            "expires_at": datetime(2026, 10, 1, 9, 10, tzinfo=UTC),
            **overrides,
        },
    )
    session.add(request)
    await session.flush()
    return request


async def make_sheet_sync(session: AsyncSession, club: Club, **overrides: Any) -> SheetSync:
    started_at = overrides.pop("started_at", datetime(2026, 10, 1, 8, 50, tzinfo=UTC))
    sync = SheetSync(
        **{
            "club_id": club.id,
            "started_at": started_at,
            "finished_at": started_at + timedelta(seconds=2),
            "status": SheetSyncStatus.OK,
            "added": 0,
            "removed": 0,
            "issues": [],
            **overrides,
        },
    )
    session.add(sync)
    await session.flush()
    return sync
