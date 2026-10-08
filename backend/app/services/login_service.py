from datetime import UTC, datetime, timedelta

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from app.clients import ClientError, LoginThrottle
from app.config import AuthSettings, BotSettings
from app.exceptions import (
    AdminAccessDeniedError,
    InvalidLoginCodeError,
    InvalidWidgetDataError,
    LoginUnavailableError,
    TelegramUnavailableError,
    TooManyLoginAttemptsError,
    WidgetLoginDisabledError,
)
from app.models import AdminUser, LoginCode
from app.repositories import AdminUserRepository, LoginCodeRepository
from app.schemas import AuthConfig, IssuedLoginCode, SessionGrant, TelegramProfile, TelegramWidgetPayload
from app.services.admin_access_resolver import AdminAccessResolver
from app.services.admin_session_service import AdminSessionService
from app.utils import Clock, generate_login_code, hash_secret, is_valid_widget_signature

LOGIN_CODE_TTL = timedelta(minutes=5)
WIDGET_DATA_MAX_AGE = timedelta(minutes=10)


class LoginService:
    def __init__(
        self,
        *,
        admin_user_repository: AdminUserRepository,
        login_code_repository: LoginCodeRepository,
        access_resolver: AdminAccessResolver,
        admin_session_service: AdminSessionService,
        login_throttle: LoginThrottle,
        clock: Clock,
        settings: AuthSettings,
        bot_settings: BotSettings,
        bot: Bot,
    ) -> None:
        self._admin_user_repository = admin_user_repository
        self._login_code_repository = login_code_repository
        self._access_resolver = access_resolver
        self._admin_session_service = admin_session_service
        self._login_throttle = login_throttle
        self._clock = clock
        self._settings = settings
        self._bot_settings = bot_settings
        self._bot = bot

    async def get_config(self) -> AuthConfig:
        try:
            me = await self._bot.me()
        except TelegramAPIError as error:
            raise TelegramUnavailableError from error
        return AuthConfig(widget_enabled=self._settings.widget_enabled, bot_username=me.username or "")

    async def issue_code(self, profile: TelegramProfile) -> IssuedLoginCode:
        admin = await self._find_admin(profile)
        if admin is None or self._access_resolver.resolve(admin) is None:
            raise AdminAccessDeniedError
        now = self._clock.now()
        await self._login_code_repository.expire_active_for_admin(admin_user_id=admin.id, now=now)
        code = await self._generate_unique_code(now)
        expires_at = now + LOGIN_CODE_TTL
        self._login_code_repository.add(
            LoginCode(code_hash=hash_secret(code), admin_user_id=admin.id, expires_at=expires_at),
        )
        await self._login_code_repository.flush()
        return IssuedLoginCode(code=code, expires_at=expires_at)

    async def login_with_code(self, code: str, client_key: str) -> SessionGrant:
        if await self._is_throttled(client_key):
            raise TooManyLoginAttemptsError
        now = self._clock.now()
        login_code = await self._login_code_repository.get_active(code_hash=hash_secret(code), now=now)
        principal = self._access_resolver.resolve(login_code.admin_user) if login_code else None
        if login_code is None or principal is None:
            await self._register_failed_attempt(client_key)
            raise InvalidLoginCodeError
        login_code.used_at = now
        return await self._admin_session_service.start(principal)

    async def login_with_widget(self, payload: TelegramWidgetPayload) -> SessionGrant:
        if not self._settings.widget_enabled:
            raise WidgetLoginDisabledError
        if not self._is_widget_payload_valid(payload):
            raise InvalidWidgetDataError
        profile = TelegramProfile(tg_id=payload.id, tg_username=payload.username, full_name=payload.full_name)
        admin = await self._find_admin(profile)
        principal = self._access_resolver.resolve(admin) if admin else None
        if principal is None:
            raise AdminAccessDeniedError
        return await self._admin_session_service.start(principal)

    async def _is_throttled(self, client_key: str) -> bool:
        try:
            return await self._login_throttle.is_blocked(client_key)
        except ClientError as error:
            raise LoginUnavailableError from error

    async def _register_failed_attempt(self, client_key: str) -> None:
        try:
            await self._login_throttle.register_failure(client_key)
        except ClientError as error:
            raise LoginUnavailableError from error

    def _is_widget_payload_valid(self, payload: TelegramWidgetPayload) -> bool:
        signed_at = datetime.fromtimestamp(payload.auth_date, tz=UTC)
        if self._clock.now() - signed_at > WIDGET_DATA_MAX_AGE:
            return False
        bot_token = self._bot_settings.token.get_secret_value()
        return is_valid_widget_signature(payload.signed_fields(), payload.hash, bot_token)

    # Owners get an account on their first login; everyone else must be added in the admin panel.
    async def _find_admin(self, profile: TelegramProfile) -> AdminUser | None:
        admin = await self._admin_user_repository.get_by_tg_id(profile.tg_id)
        if admin is not None or not self._access_resolver.is_owner(profile.tg_id):
            return admin
        admin = AdminUser(tg_id=profile.tg_id, name=profile.full_name, role=None)
        self._admin_user_repository.add(admin)
        await self._admin_user_repository.flush()
        return admin

    async def _generate_unique_code(self, now: datetime) -> str:
        while True:
            code = generate_login_code()
            if not await self._login_code_repository.exists_active(code_hash=hash_secret(code), now=now):
                return code
