from loguru import logger

from app.clients import VkClient, VkClientError, VkUser
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
from app.models import User
from app.queries import AccessQueries
from app.repositories import UserRepository
from app.schemas import (
    ClubAccess,
    VkAlreadyLinked,
    VkCandidate,
    VkLinkByProfile,
    VkLinkOffer,
    VkLinkResult,
    VkLinkUnavailable,
)
from app.services.app_settings_service import AppSettingsService
from app.services.vk_link_availability import VkLinkAvailability
from app.utils import Clock, VkIdReference, VkReference, VkScreenNameReference, parse_vk_reference


# A link is final: no relinking or unlinking, otherwise one student could invite others into the club chat.
class VkLinkService:
    def __init__(
        self,
        *,
        user_repository: UserRepository,
        access_queries: AccessQueries,
        app_settings_service: AppSettingsService,
        vk_link_availability: VkLinkAvailability,
        vk_client: VkClient,
        clock: Clock,
    ) -> None:
        self._user_repository = user_repository
        self._access_queries = access_queries
        self._app_settings_service = app_settings_service
        self._vk_link_availability = vk_link_availability
        self._vk_client = vk_client
        self._clock = clock

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
        return VkLinkUnavailable()

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
