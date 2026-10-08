from datetime import timedelta

from sqlalchemy.ext.asyncio import AsyncSession

from app.config import AuthSettings
from app.exceptions import NotAuthenticatedError
from app.models import AdminSession
from app.repositories import AdminSessionRepository
from app.schemas import AdminPrincipal, SessionGrant
from app.services.admin_access_resolver import AdminAccessResolver
from app.utils import Clock, generate_session_token, hash_secret


class AdminSessionService:
    def __init__(
        self,
        session: AsyncSession,
        admin_session_repository: AdminSessionRepository,
        access_resolver: AdminAccessResolver,
        clock: Clock,
        settings: AuthSettings,
    ) -> None:
        self._session = session
        self._admin_session_repository = admin_session_repository
        self._access_resolver = access_resolver
        self._clock = clock
        self._settings = settings

    async def authenticate(self, token: str | None) -> AdminPrincipal:
        if not token:
            raise NotAuthenticatedError
        admin_session = await self._admin_session_repository.get_active(
            token_hash=hash_secret(token),
            now=self._clock.now(),
        )
        principal = self._access_resolver.resolve(admin_session.admin_user) if admin_session else None
        if principal is None:
            raise NotAuthenticatedError
        return principal

    async def start(self, principal: AdminPrincipal) -> SessionGrant:
        now = self._clock.now()
        await self._admin_session_repository.delete_expired_for_admin(admin_user_id=principal.id, now=now)
        token = generate_session_token()
        expires_at = now + timedelta(days=self._settings.session_ttl_days)
        self._admin_session_repository.add(
            AdminSession(token_hash=hash_secret(token), admin_user_id=principal.id, expires_at=expires_at),
        )
        await self._session.commit()
        return SessionGrant(token=token, expires_at=expires_at, admin=principal)

    async def end(self, token: str) -> None:
        await self._admin_session_repository.delete_by_token_hash(hash_secret(token))
        await self._session.commit()
