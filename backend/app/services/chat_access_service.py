from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from loguru import logger

from app.enums import ChatAccessStatus
from app.models import Block, ChatAccess, Club, User
from app.repositories import BlockRepository, ChatAccessRepository, ClubRepository, MembershipRepository, UserRepository
from app.schemas import ClubAccess
from app.utils import Clock

REINVITED_STATUSES = (ChatAccessStatus.LEFT, ChatAccessStatus.KICKED)


# The bot lets in only the owner of a personal join link who has access, and never declines a request:
# admins approve everyone else by hand.
class ChatAccessService:
    def __init__(
        self,
        *,
        chat_access_repository: ChatAccessRepository,
        club_repository: ClubRepository,
        block_repository: BlockRepository,
        membership_repository: MembershipRepository,
        user_repository: UserRepository,
        bot: Bot,
        clock: Clock,
    ) -> None:
        self._chat_access_repository = chat_access_repository
        self._club_repository = club_repository
        self._block_repository = block_repository
        self._membership_repository = membership_repository
        self._user_repository = user_repository
        self._bot = bot
        self._clock = clock

    # Every access comes with the student's join link: showing the status is the moment they need it.
    async def access_for_user(self, user_id: int) -> list[ClubAccess]:
        user = await self._user_repository.get_by_id(user_id)
        if user is None or user.vk_id is None:
            return []
        access: list[ClubAccess] = []
        clubs = await self._club_repository.list_active()
        for club in clubs:
            block = await self._access_block(club, user.vk_id)
            if block is None:
                continue
            invite_link = await self._try_invite_link(club, user)
            access.append(
                ClubAccess(
                    club_title=club.title,
                    block_title=block.title,
                    block_starts_at=block.starts_at,
                    is_upcoming=block.starts_at > self._clock.now(),
                    invite_link=invite_link,
                ),
            )
        return access

    async def handle_join_request(self, *, chat_id: int, tg_id: int, invite_link: str | None) -> None:
        if invite_link is None:
            return
        access = await self._chat_access_repository.get_by_invite_link_with_user(invite_link)
        if access is None or access.chat_id != chat_id:
            return
        if access.user.tg_id != tg_id:
            logger.info("Join request of {} came through the link of user {}, left to admins", tg_id, access.user_id)
            return
        club = await self._club_repository.get_by_id(access.club_id)
        vk_id = access.user.vk_id
        if club is None or not club.is_active or club.chat_id != chat_id or vk_id is None:
            return
        if await self._access_block(club, vk_id) is None:
            logger.info("Join request of user {} to club {} without access, left to admins", access.user_id, club.id)
            return
        try:
            await self._bot.approve_chat_join_request(chat_id=chat_id, user_id=tg_id)
        except TelegramAPIError as error:
            logger.warning("Cannot approve the join request of user {} to club {}: {}", access.user_id, club.id, error)
            return
        access.status = ChatAccessStatus.JOINED
        access.joined_at = self._clock.now()
        await self._chat_access_repository.flush()
        logger.info("User {} joined the chat of club {}", access.user_id, club.id)

    async def _access_block(self, club: Club, vk_id: int) -> Block | None:
        block = await self._block_repository.get_access_block(club_id=club.id, now=self._clock.now())
        if block is None:
            return None
        is_member = await self._membership_repository.is_member(block_id=block.id, vk_id=vk_id)
        return block if is_member else None

    async def _try_invite_link(self, club: Club, user: User) -> str | None:
        if club.chat_id is None:
            return None
        try:
            return await self._invite_link(club.id, club.chat_id, user)
        except TelegramAPIError:
            logger.exception("Cannot make a join link to club {} for user {}", club.id, user.id)
            return None

    # One link per student and chat, reused: a kicked student returns through the same link.
    async def _invite_link(self, club_id: int, chat_id: int, user: User) -> str:
        access = await self._chat_access_repository.get_for_user(club_id=club_id, user_id=user.id)
        now = self._clock.now()
        if access is not None and access.chat_id == chat_id:
            if access.status is ChatAccessStatus.KICKED:
                await self._bot.unban_chat_member(chat_id=chat_id, user_id=user.tg_id, only_if_banned=True)
            if access.status in REINVITED_STATUSES:
                access.status = ChatAccessStatus.INVITED
                access.invited_at = now
                await self._chat_access_repository.flush()
            return access.invite_link

        link = await self._bot.create_chat_invite_link(
            chat_id=chat_id,
            name=f"user {user.id}",
            creates_join_request=True,
        )
        if access is None:
            access = ChatAccess(club_id=club_id, user_id=user.id)
            self._chat_access_repository.add(access)
        access.chat_id = chat_id
        access.invite_link = link.invite_link
        access.status = ChatAccessStatus.INVITED
        access.invited_at = now
        access.joined_at = None
        access.kicked_at = None
        await self._chat_access_repository.flush()
        return access.invite_link
