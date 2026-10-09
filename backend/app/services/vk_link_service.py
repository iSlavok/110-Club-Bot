from datetime import timedelta
from urllib.parse import urlencode

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError
from loguru import logger

from app import texts
from app.clients import VkClient, VkClientError, VkUser
from app.clients.vk_client import VK_ID_AUTHORIZE_URL
from app.config import PublicSettings, VkSettings
from app.enums import VkLinkMode
from app.exceptions import (
    InvalidVkLinkError,
    UserNotRegisteredError,
    VkAccountTakenError,
    VkAlreadyLinkedError,
    VkLinkModeChangedError,
    VkLinkUnavailableError,
    VkProfileNotFoundError,
    VkUnavailableError,
)
from app.models import User, VkAuthRequest
from app.queries import AccessQueries
from app.repositories import UserRepository, VkAuthRequestRepository
from app.schemas import (
    ClubAccess,
    VkAlreadyLinked,
    VkCandidate,
    VkLinkByOAuth,
    VkLinkByProfile,
    VkLinkOffer,
    VkLinkResult,
    VkLinkUnavailable,
    VkOAuthCompletion,
)
from app.services.app_settings_service import AppSettingsService
from app.services.vk_link_availability import VkLinkAvailability
from app.utils import (
    Clock,
    VkIdReference,
    VkReference,
    VkScreenNameReference,
    generate_code_verifier,
    generate_oauth_state,
    hash_secret,
    parse_vk_reference,
    pkce_code_challenge,
)

# Matches the lifetime of a VK ID authorization code.
VK_AUTH_REQUEST_TTL = timedelta(minutes=10)
# Keep in sync with the route in api/v1/vk_routes.py; VK ID only redirects to URLs whitelisted in the VK app.
VK_CALLBACK_PATH = "/api/v1/vk/callback"
VK_ID_SCOPE = "vkid.personal_info"


# A link is final: no relinking or unlinking, otherwise one student could invite others into the club chat.
class VkLinkService:
    def __init__(
        self,
        *,
        user_repository: UserRepository,
        vk_auth_request_repository: VkAuthRequestRepository,
        access_queries: AccessQueries,
        app_settings_service: AppSettingsService,
        vk_link_availability: VkLinkAvailability,
        vk_client: VkClient,
        clock: Clock,
        public_settings: PublicSettings,
        vk_settings: VkSettings,
        bot: Bot,
    ) -> None:
        self._user_repository = user_repository
        self._vk_auth_request_repository = vk_auth_request_repository
        self._access_queries = access_queries
        self._app_settings_service = app_settings_service
        self._vk_link_availability = vk_link_availability
        self._vk_client = vk_client
        self._clock = clock
        self._public_settings = public_settings
        self._vk_settings = vk_settings
        self._bot = bot

    async def offer(self, tg_id: int) -> VkLinkOffer:
        user = await self._get_user(tg_id)
        if user.vk_id is not None:
            access = await self._access(user.vk_id)
            return VkAlreadyLinked(vk_id=user.vk_id, access=access)
        mode = await self._current_mode()
        if not self._vk_link_availability.is_configured(mode):
            logger.warning("VK link mode {} is selected but its credentials are missing", mode)
            return VkLinkUnavailable()
        if mode is VkLinkMode.LINK:
            return VkLinkByProfile()
        return await self._start_oauth(user)

    async def find_candidate(self, tg_id: int, text: str) -> VkCandidate:
        user = await self._get_unlinked_user(tg_id)
        await self._ensure_mode(VkLinkMode.LINK)
        reference = parse_vk_reference(text)
        if reference is None:
            raise InvalidVkLinkError
        vk_user = await self._resolve(reference)
        await self._ensure_vk_free(vk_user.id, user)
        full_name = f"{vk_user.first_name} {vk_user.last_name}".strip()
        return VkCandidate(vk_id=vk_user.id, full_name=full_name)

    async def confirm_candidate(self, tg_id: int, vk_id: int) -> VkLinkResult:
        user = await self._get_unlinked_user(tg_id)
        await self._ensure_mode(VkLinkMode.LINK)
        return await self._link(user, vk_id)

    # Called by the VK ID redirect. The result goes to the student in Telegram; the browser only returns to the bot.
    # The request is accepted even if the mode switched to "link" meanwhile: VK ID proves ownership anyway.
    async def complete_oauth(
        self,
        *,
        state: str,
        code: str | None,
        device_id: str | None,
        error: str | None,
    ) -> VkOAuthCompletion:
        now = self._clock.now()
        request = await self._vk_auth_request_repository.get_for_update(hash_secret(state))
        if request is None or request.used_at is not None or request.expires_at <= now:
            return VkOAuthCompletion(is_expired=True, bot_username=None)
        request.used_at = now
        await self._vk_auth_request_repository.flush()
        if error is not None or code is None or device_id is None:
            logger.info("VK ID returned no code for user {}: {}", request.user_id, error)
            await self._notify(request.user.tg_id, texts.vk_link.OAUTH_CANCELLED)
        else:
            await self._finish_oauth(request, state=state, code=code, device_id=device_id)
        bot_username = await self._bot_username()
        return VkOAuthCompletion(is_expired=False, bot_username=bot_username)

    async def _start_oauth(self, user: User) -> VkLinkByOAuth:
        now = self._clock.now()
        await self._vk_auth_request_repository.expire_active_for_user(user_id=user.id, now=now)
        state = generate_oauth_state()
        code_verifier = generate_code_verifier()
        expires_at = now + VK_AUTH_REQUEST_TTL
        self._vk_auth_request_repository.add(
            VkAuthRequest(
                state_hash=hash_secret(state),
                user_id=user.id,
                code_verifier=code_verifier,
                expires_at=expires_at,
            ),
        )
        await self._vk_auth_request_repository.flush()
        query = urlencode(
            {
                "response_type": "code",
                "client_id": self._vk_settings.client_id,
                "redirect_uri": self._redirect_uri(),
                "state": state,
                "code_challenge": pkce_code_challenge(code_verifier),
                "code_challenge_method": "S256",
                "scope": VK_ID_SCOPE,
            },
        )
        return VkLinkByOAuth(authorize_url=f"{VK_ID_AUTHORIZE_URL}?{query}", expires_at=expires_at)

    async def _finish_oauth(self, request: VkAuthRequest, *, state: str, code: str, device_id: str) -> None:
        user = request.user
        if user.vk_id is not None:
            await self._notify(user.tg_id, texts.vk_link.OAUTH_ALREADY_LINKED)
            return
        try:
            vk_id = await self._vk_client.exchange_code(
                code=code,
                code_verifier=request.code_verifier,
                device_id=device_id,
                state=state,
                redirect_uri=self._redirect_uri(),
            )
        except VkClientError as error:
            logger.warning("VK ID code exchange failed for user {}: {}", user.id, error)
            await self._notify(user.tg_id, texts.vk_link.OAUTH_FAILED)
            return
        try:
            result = await self._link(user, vk_id)
        except VkAccountTakenError:
            await self._notify(user.tg_id, texts.vk_link.OAUTH_VK_TAKEN)
            return
        await self._notify(user.tg_id, texts.vk_link.linked(result))

    # The link is already saved, so a failed message is only logged: /vk shows the status again.
    async def _notify(self, tg_id: int, text: str) -> None:
        try:
            await self._bot.send_message(tg_id, text)
        except TelegramForbiddenError:
            logger.info("User {} blocked the bot, VK ID result not delivered", tg_id)
        except TelegramAPIError:
            logger.exception("Failed to send the VK ID result to user {}", tg_id)

    def _redirect_uri(self) -> str:
        if self._public_settings.url is None:
            raise VkLinkUnavailableError
        return f"{self._public_settings.url}{VK_CALLBACK_PATH}"

    async def _bot_username(self) -> str | None:
        try:
            me = await self._bot.me()
        except TelegramAPIError as error:
            logger.warning("Cannot get the bot username for the VK ID redirect: {}", error)
            return None
        return me.username

    async def _link(self, user: User, vk_id: int) -> VkLinkResult:
        await self._ensure_vk_free(vk_id, user)
        user.vk_id = vk_id
        user.vk_linked_at = self._clock.now()
        await self._user_repository.flush()
        logger.info("User {} linked VK {}", user.id, vk_id)
        access = await self._access(vk_id)
        return VkLinkResult(vk_id=vk_id, access=access)

    async def _resolve(self, reference: VkReference) -> VkUser:
        try:
            vk_user = await self._vk_client.get_user(self._user_ref(reference))
        except VkClientError as error:
            logger.warning("VK lookup failed: {}", error)
            raise VkUnavailableError from error
        if vk_user is None or vk_user.is_deactivated:
            raise VkProfileNotFoundError
        return vk_user

    @staticmethod
    def _user_ref(reference: VkReference) -> int | str:
        match reference:
            case VkIdReference(user_id=user_id):
                return user_id
            case VkScreenNameReference(screen_name=screen_name):
                return screen_name

    async def _ensure_vk_free(self, vk_id: int, user: User) -> None:
        owner = await self._user_repository.get_by_vk_id(vk_id)
        if owner is not None and owner.id != user.id:
            logger.warning("User {} tried to link VK {} that belongs to user {}", user.id, vk_id, owner.id)
            raise VkAccountTakenError

    async def _ensure_mode(self, mode: VkLinkMode) -> None:
        if await self._current_mode() is not mode:
            raise VkLinkModeChangedError
        if not self._vk_link_availability.is_configured(mode):
            raise VkLinkUnavailableError

    async def _current_mode(self) -> VkLinkMode:
        settings = await self._app_settings_service.get()
        return settings.vk_link_mode

    async def _access(self, vk_id: int) -> list[ClubAccess]:
        rows = await self._access_queries.current_blocks_for_vk(vk_id=vk_id, now=self._clock.now())
        return [ClubAccess(club_title=row.club_title, block_title=row.block_title) for row in rows]

    async def _get_user(self, tg_id: int) -> User:
        user = await self._user_repository.get_by_tg_id(tg_id)
        if user is None:
            raise UserNotRegisteredError
        return user

    async def _get_unlinked_user(self, tg_id: int) -> User:
        user = await self._get_user(tg_id)
        if user.vk_id is not None:
            raise VkAlreadyLinkedError
        return user
