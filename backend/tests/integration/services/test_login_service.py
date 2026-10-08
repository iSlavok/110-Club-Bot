import hashlib
import hmac
from datetime import timedelta
from typing import TYPE_CHECKING, cast

import pytest
from aiogram import Bot
from aiogram.exceptions import TelegramNetworkError
from aiogram.methods import GetMe
from sqlalchemy import select

from app.clients import LoginThrottle
from app.clients.login_throttle import MAX_FAILURES
from app.enums import Permission
from app.exceptions import (
    AdminAccessDeniedError,
    InvalidLoginCodeError,
    InvalidWidgetDataError,
    LoginUnavailableError,
    TelegramUnavailableError,
    TooManyLoginAttemptsError,
)
from app.models import AdminSession, AdminUser
from app.schemas import TelegramProfile, TelegramWidgetPayload
from app.services import LoginService
from app.services.login_service import LOGIN_CODE_TTL
from tests.factories import make_admin_user, make_role
from tests.fakes import FakeLoginThrottle
from tests.providers import BOT_TOKEN, BOT_USERNAME, DEFAULT_NOW, OWNER_TG_ID

if TYPE_CHECKING:
    from unittest.mock import AsyncMock

CLIENT = "10.0.0.1"


def _profile(tg_id: int, full_name: str = "Олег Сидоров") -> TelegramProfile:
    return TelegramProfile(tg_id=tg_id, tg_username=None, full_name=full_name)


def _widget_payload(tg_id: int, auth_date: int, token: str = BOT_TOKEN) -> TelegramWidgetPayload:
    fields = {"id": tg_id, "first_name": "Олег", "auth_date": auth_date}
    data_check_string = "\n".join(f"{key}={fields[key]}" for key in sorted(fields))
    secret_key = hashlib.sha256(token.encode()).digest()
    signature = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()
    return TelegramWidgetPayload(id=tg_id, first_name="Олег", auth_date=auth_date, hash=signature)


@pytest.fixture
async def service(request_container) -> LoginService:
    return await request_container.get(LoginService)


@pytest.fixture
async def throttle(container) -> FakeLoginThrottle:
    return cast("FakeLoginThrottle", await container.get(LoginThrottle))


async def test_config_exposes_widget_flag_and_bot_username(service) -> None:
    config = await service.get_config()

    assert config.widget_enabled
    assert config.bot_username == BOT_USERNAME


async def test_owner_gets_account_and_code_on_first_login(service, db_session) -> None:
    issued = await service.issue_code(_profile(OWNER_TG_ID, "Владелец"))

    owner = await db_session.scalar(select(AdminUser).where(AdminUser.tg_id == OWNER_TG_ID))
    assert owner is not None
    assert owner.name == "Владелец"
    assert owner.role_id is None
    assert issued.expires_at == DEFAULT_NOW + LOGIN_CODE_TTL


async def test_stranger_gets_no_code(service) -> None:
    with pytest.raises(AdminAccessDeniedError):
        await service.issue_code(_profile(1))


async def test_inactive_admin_gets_no_code(service, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session), is_active=False)

    with pytest.raises(AdminAccessDeniedError):
        await service.issue_code(_profile(admin.tg_id))


async def test_code_logs_in_once(service, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session, Permission.CLUBS_VIEW))
    issued = await service.issue_code(_profile(admin.tg_id))

    grant = await service.login_with_code(issued.code, CLIENT)

    assert grant.admin.id == admin.id
    assert grant.admin.permissions == {Permission.CLUBS_VIEW}
    assert await db_session.scalar(select(AdminSession).where(AdminSession.admin_user_id == admin.id))
    with pytest.raises(InvalidLoginCodeError):
        await service.login_with_code(issued.code, CLIENT)


async def test_new_code_replaces_previous(service, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))
    first = await service.issue_code(_profile(admin.tg_id))
    second = await service.issue_code(_profile(admin.tg_id))

    with pytest.raises(InvalidLoginCodeError):
        await service.login_with_code(first.code, CLIENT)
    assert (await service.login_with_code(second.code, CLIENT)).admin.id == admin.id


async def test_expired_code_is_rejected(service, db_session, clock) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))
    issued = await service.issue_code(_profile(admin.tg_id))
    clock.set(issued.expires_at)

    with pytest.raises(InvalidLoginCodeError):
        await service.login_with_code(issued.code, CLIENT)


async def test_code_of_deactivated_admin_is_rejected(service, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))
    issued = await service.issue_code(_profile(admin.tg_id))
    admin.is_active = False

    with pytest.raises(InvalidLoginCodeError):
        await service.login_with_code(issued.code, CLIENT)


async def test_wrong_codes_are_throttled_per_client(service, db_session, throttle) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))
    issued = await service.issue_code(_profile(admin.tg_id))
    throttle.failures[CLIENT] = MAX_FAILURES - 1

    with pytest.raises(InvalidLoginCodeError):
        await service.login_with_code("000000" if issued.code != "000000" else "111111", CLIENT)
    with pytest.raises(TooManyLoginAttemptsError):
        await service.login_with_code(issued.code, CLIENT)
    assert (await service.login_with_code(issued.code, "10.0.0.2")).admin.id == admin.id


async def test_widget_logs_in_admin(service, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))

    grant = await service.login_with_widget(_widget_payload(admin.tg_id, int(DEFAULT_NOW.timestamp())))

    assert grant.admin.id == admin.id


async def test_widget_rejects_forged_signature(service, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))
    payload = _widget_payload(admin.tg_id, int(DEFAULT_NOW.timestamp()), token="654321:other-bot")

    with pytest.raises(InvalidWidgetDataError):
        await service.login_with_widget(payload)


async def test_widget_rejects_stale_data(service, db_session) -> None:
    admin = await make_admin_user(db_session, await make_role(db_session))
    stale = int((DEFAULT_NOW - timedelta(hours=1)).timestamp())

    with pytest.raises(InvalidWidgetDataError):
        await service.login_with_widget(_widget_payload(admin.tg_id, stale))


async def test_widget_rejects_stranger(service) -> None:
    with pytest.raises(AdminAccessDeniedError):
        await service.login_with_widget(_widget_payload(1, int(DEFAULT_NOW.timestamp())))


async def test_redis_outage_makes_code_login_unavailable(service, throttle) -> None:
    throttle.available = False

    with pytest.raises(LoginUnavailableError):
        await service.login_with_code("123456", CLIENT)


async def test_telegram_outage_is_a_domain_error(service, container) -> None:
    bot = cast("AsyncMock", await container.get(Bot))
    bot.me.side_effect = TelegramNetworkError(method=GetMe(), message="timeout")

    with pytest.raises(TelegramUnavailableError):
        await service.get_config()
