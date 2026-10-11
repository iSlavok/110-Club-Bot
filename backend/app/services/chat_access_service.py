from aiogram import Bot
from aiogram.enums import ChatMemberStatus
from aiogram.exceptions import TelegramAPIError, TelegramForbiddenError
from aiogram.types import ChatMemberRestricted, InlineKeyboardMarkup, ResultChatMemberUnion
from loguru import logger

from app import texts
from app.enums import ChatAccessStatus
from app.models import Block, ChatAccess, Club, User
from app.queries import ChatAccessQueries
from app.repositories import BlockRepository, ChatAccessRepository, ClubRepository, MembershipRepository, UserRepository
from app.schemas import ClubAccess, KickedMember, StudentClubStatus
from app.telegram import AdminAlerts, chat_invite_keyboard
from app.utils import Clock

REINVITED_STATUSES = (ChatAccessStatus.LEFT, ChatAccessStatus.KICKED)
OUT_OF_CHAT_STATUSES = (ChatMemberStatus.LEFT, ChatMemberStatus.KICKED)
CHAT_ADMIN_STATUSES = (ChatMemberStatus.CREATOR, ChatMemberStatus.ADMINISTRATOR)
ERROR_MAX_LEN = 1000
JOIN_LINK_NAME = "club bot"


# The bot lets in only students with access, and never declines a request: admins approve everyone else by hand.
class ChatAccessService:
    def __init__(
        self,
        *,
        chat_access_repository: ChatAccessRepository,
        chat_access_queries: ChatAccessQueries,
        club_repository: ClubRepository,
        block_repository: BlockRepository,
        membership_repository: MembershipRepository,
        user_repository: UserRepository,
        bot: Bot,
        admin_alerts: AdminAlerts,
        clock: Clock,
    ) -> None:
        self._chat_access_repository = chat_access_repository
        self._chat_access_queries = chat_access_queries
        self._club_repository = club_repository
        self._block_repository = block_repository
        self._membership_repository = membership_repository
        self._user_repository = user_repository
        self._bot = bot
        self._admin_alerts = admin_alerts
        self._clock = clock

    async def list_chat_club_ids(self) -> list[int]:
        clubs = await self._club_repository.list_with_chat()
        return [club.id for club in clubs]

    # Runs in the caller's transaction (sheet sync, confirmed removal, chat job), so it sees members changed just
    # before. Telegram errors are collected per student and alerted, never raised: they must not undo the caller.
    async def reconcile_club(self, club_id: int) -> None:
        club = await self._club_repository.get_by_id(club_id)
        if club is None or not club.is_active or club.chat_id is None:
            return
        chat_id = club.chat_id
        block = await self._block_repository.get_access_block(club_id=club.id, now=self._clock.now())
        # An access block without members means the sheet is not filled yet: kicking then would empty the chat.
        filled: Block | None = None
        if block is not None and await self._membership_repository.exists_for_block(block.id):
            filled = block
        kick_ids = await self._chat_access_queries.list_joined_without_access(
            club_id=club.id,
            chat_id=chat_id,
            block_id=filled.id if filled is not None else None,
        )
        on_hold = filled is None and bool(kick_ids)
        await self._set_kicks_on_hold(club, on_hold=on_hold, block=block, waiting=len(kick_ids))
        if filled is None:
            return
        invite_ids = await self._chat_access_queries.list_users_to_invite(
            club_id=club.id,
            chat_id=chat_id,
            block_id=filled.id,
        )

        errors = await self._invite_all(club, chat_id, filled, invite_ids)
        kicked: list[KickedMember] = []
        for access_id in kick_ids:
            try:
                member = await self._kick(club, access_id)
            except TelegramAPIError as error:
                logger.warning("Cannot kick chat access {} of club {}: {}", access_id, club.id, error)
                errors.append(str(error))
                continue
            if member is not None:
                kicked.append(member)
        await self._report(
            club,
            kicked=kicked,
            attempted=bool(invite_ids or kick_ids),
            error=errors[0] if errors else None,
        )

    async def access_blocks(self, vk_id: int) -> list[tuple[Club, Block]]:
        club_blocks: list[tuple[Club, Block]] = []
        clubs = await self._club_repository.list_active()
        for club in clubs:
            block = await self._access_block(club, vk_id)
            if block is not None:
                club_blocks.append((club, block))
        return club_blocks

    # Every access comes with the student's join link: showing the status is the moment they need it.
    async def access_for_user(self, user_id: int) -> list[ClubAccess]:
        user = await self._user_repository.get_by_id(user_id)
        if user is None or user.vk_id is None:
            return []
        access: list[ClubAccess] = []
        club_blocks = await self.access_blocks(user.vk_id)
        for club, block in club_blocks:
            invite_link = await self._try_invite_link(club, user)
            access.append(self._club_access(club, block, invite_link))
        return access

    # Telegram is asked directly: a student an admin let in by hand is in the chat too.
    async def student_clubs(self, user_id: int) -> list[StudentClubStatus]:
        user = await self._user_repository.get_by_id(user_id)
        if user is None or user.vk_id is None:
            return []
        statuses: list[StudentClubStatus] = []
        club_blocks = await self.access_blocks(user.vk_id)
        for club, block in club_blocks:
            in_chat = await self._is_in_chat(club, user)
            invite_link = await self._try_invite_link(club, user) if in_chat is False else None
            next_block_title = await self._next_block_title(club, block, user.vk_id)
            statuses.append(
                StudentClubStatus(
                    access=self._club_access(club, block, invite_link),
                    in_chat=in_chat,
                    next_block_title=next_block_title,
                ),
            )
        return statuses

    # The link does not matter, the student who asked does: a forwarded link lets nobody else in.
    async def handle_join_request(self, *, chat_id: int, tg_id: int) -> None:
        club = await self._club_repository.get_active_by_chat_id(chat_id)
        if club is None:
            return
        user = await self._user_repository.get_by_tg_id(tg_id)
        if user is None or user.vk_id is None:
            logger.info("Join request of {} to club {} without a linked VK, left to admins", tg_id, club.id)
            return
        if await self._access_block(club, user.vk_id) is None:
            logger.info("Join request of user {} to club {} without access, left to admins", user.id, club.id)
            return
        try:
            await self._bot.approve_chat_join_request(chat_id=chat_id, user_id=tg_id)
        except TelegramAPIError as error:
            logger.warning("Cannot approve the join request of user {} to club {}: {}", user.id, club.id, error)
            return
        now = self._clock.now()
        access = await self._chat_access_repository.get_for_user(club_id=club.id, user_id=user.id)
        if access is None:
            access = ChatAccess(club_id=club.id, user_id=user.id, invited_at=now)
            self._chat_access_repository.add(access)
        access.chat_id = chat_id
        access.status = ChatAccessStatus.JOINED
        access.joined_at = now
        await self._chat_access_repository.flush()
        logger.info("User {} joined the chat of club {}", user.id, club.id)

    # Join and leave notices clutter the chat; Telegram has no setting to turn them off.
    async def hide_service_message(self, *, chat_id: int, message_id: int) -> None:
        club = await self._club_repository.get_active_by_chat_id(chat_id)
        if club is None or not club.hide_service_messages:
            return
        try:
            await self._bot.delete_message(chat_id=chat_id, message_id=message_id)
        except TelegramAPIError as error:
            logger.warning("Cannot delete service message {} in club {}: {}", message_id, club.id, error)

    def _club_access(self, club: Club, block: Block, invite_link: str | None) -> ClubAccess:
        return ClubAccess(
            club_title=club.title,
            block_title=block.title,
            invite_link=invite_link,
        )

    async def _invite_all(self, club: Club, chat_id: int, block: Block, user_ids: list[int]) -> list[str]:
        if not user_ids:
            return []
        try:
            invite_link = await self._chat_link(club, chat_id)
        except TelegramAPIError as error:
            logger.warning("Cannot make the join link of club {}: {}", club.id, error)
            return [str(error)]
        errors: list[str] = []
        for user_id in user_ids:
            try:
                await self._invite(club, chat_id, block, user_id, invite_link)
            except TelegramAPIError as error:
                logger.warning("Cannot invite user {} to the chat of club {}: {}", user_id, club.id, error)
                errors.append(str(error))
        return errors

    async def _invite(self, club: Club, chat_id: int, block: Block, user_id: int, invite_link: str) -> None:
        user = await self._user_repository.get_by_id(user_id)
        if user is None:
            return
        await self._mark_invited(club.id, chat_id, user)
        item = self._club_access(club, block, invite_link)
        await self._message(user.tg_id, texts.chat_access.invite(item), chat_invite_keyboard([item]))
        logger.info("User {} invited to the chat of club {}", user.id, club.id)

    async def _kick(self, club: Club, access_id: int) -> KickedMember | None:
        access = await self._chat_access_repository.get_with_user(access_id)
        if access is None or access.user.vk_id is None:
            return None
        user, vk_id = access.user, access.user.vk_id
        member = await self._bot.get_chat_member(chat_id=access.chat_id, user_id=user.tg_id)
        if not _in_chat(member) or member.status in CHAT_ADMIN_STATUSES:
            # A student made a chat admin is managed by hand from then on.
            access.status = ChatAccessStatus.LEFT
            await self._chat_access_repository.flush()
            return None
        await self._bot.ban_chat_member(chat_id=access.chat_id, user_id=user.tg_id)
        access.status = ChatAccessStatus.KICKED
        access.kicked_at = self._clock.now()
        await self._chat_access_repository.flush()
        logger.info("User {} kicked from the chat of club {}", user.id, club.id)
        try:
            await self._bot.unban_chat_member(chat_id=access.chat_id, user_id=user.tg_id, only_if_banned=True)
        except TelegramAPIError:
            # Not fatal: the ban is lifted again when the student is invited back.
            logger.exception("Cannot lift the ban of user {} in club {}", user.id, club.id)
        await self._message(user.tg_id, texts.chat_access.kicked(club.title))
        return KickedMember(vk_id=vk_id, full_name=user.full_name, tg_username=user.tg_username)

    # attempted: without any Telegram call in the run the chat state is unknown, so a past error is kept.
    async def _report(self, club: Club, *, kicked: list[KickedMember], attempted: bool, error: str | None) -> None:
        if kicked:
            await self._admin_alerts.send(texts.alerts.chat_kicked(club.title, kicked))
        if error is not None and club.chat_error is None:
            club.chat_error = error[:ERROR_MAX_LEN]
            await self._admin_alerts.send(texts.alerts.chat_failed(club.title, error))
        elif error is None and attempted and club.chat_error is not None:
            club.chat_error = None
            await self._admin_alerts.send(texts.alerts.chat_recovered(club.title))
        await self._club_repository.flush()

    async def _set_kicks_on_hold(self, club: Club, *, on_hold: bool, block: Block | None, waiting: int) -> None:
        if club.chat_kicks_on_hold == on_hold:
            return
        club.chat_kicks_on_hold = on_hold
        await self._club_repository.flush()
        if on_hold:
            block_title = block.title if block is not None else None
            await self._admin_alerts.send(texts.alerts.chat_kicks_on_hold(club.title, block_title, waiting))
        else:
            await self._admin_alerts.send(texts.alerts.chat_kicks_resumed(club.title))

    # The state is already saved, so a message that did not reach the student is only logged.
    async def _message(self, tg_id: int, text: str, reply_markup: InlineKeyboardMarkup | None = None) -> None:
        try:
            await self._bot.send_message(tg_id, text, reply_markup=reply_markup)
        except TelegramForbiddenError:
            logger.info("User {} blocked the bot, chat message not delivered", tg_id)
        except TelegramAPIError:
            logger.exception("Failed to send a chat access message to user {}", tg_id)

    async def _access_block(self, club: Club, vk_id: int) -> Block | None:
        block = await self._block_repository.get_access_block(club_id=club.id, now=self._clock.now())
        if block is None:
            return None
        is_member = await self._membership_repository.is_member(block_id=block.id, vk_id=vk_id)
        return block if is_member else None

    # An unknown state reads as "not in the chat": the student then gets a join link and loses nothing.
    async def _is_in_chat(self, club: Club, user: User) -> bool | None:
        if club.chat_id is None:
            return None
        try:
            member = await self._bot.get_chat_member(chat_id=club.chat_id, user_id=user.tg_id)
        except TelegramAPIError as error:
            logger.warning("Cannot check user {} in the chat of club {}: {}", user.id, club.id, error)
            return False
        return _in_chat(member)

    async def _next_block_title(self, club: Club, block: Block, vk_id: int) -> str | None:
        now = self._clock.now()
        if block.starts_at > now:
            return None
        upcoming = await self._block_repository.get_upcoming(club_id=club.id, now=now)
        if upcoming is None:
            return None
        is_member = await self._membership_repository.is_member(block_id=upcoming.id, vk_id=vk_id)
        return upcoming.title if is_member else None

    async def _try_invite_link(self, club: Club, user: User) -> str | None:
        if club.chat_id is None:
            return None
        try:
            invite_link = await self._chat_link(club, club.chat_id)
            await self._mark_invited(club.id, club.chat_id, user)
        except TelegramAPIError:
            logger.exception("Cannot give the join link of club {} to user {}", club.id, user.id)
            return None
        return invite_link

    async def _chat_link(self, club: Club, chat_id: int) -> str:
        if club.chat_invite_link is not None:
            return club.chat_invite_link
        link = await self._bot.create_chat_invite_link(chat_id=chat_id, name=JOIN_LINK_NAME, creates_join_request=True)
        club.chat_invite_link = link.invite_link
        await self._club_repository.flush()
        return link.invite_link

    async def _mark_invited(self, club_id: int, chat_id: int, user: User) -> None:
        access = await self._chat_access_repository.get_for_user(club_id=club_id, user_id=user.id)
        now = self._clock.now()
        if access is not None and access.chat_id == chat_id:
            if access.status is ChatAccessStatus.KICKED:
                await self._bot.unban_chat_member(chat_id=chat_id, user_id=user.tg_id, only_if_banned=True)
            if access.status in REINVITED_STATUSES:
                access.status = ChatAccessStatus.INVITED
                access.invited_at = now
                await self._chat_access_repository.flush()
            return
        if access is None:
            access = ChatAccess(club_id=club_id, user_id=user.id)
            self._chat_access_repository.add(access)
        access.chat_id = chat_id
        access.status = ChatAccessStatus.INVITED
        access.invited_at = now
        access.joined_at = None
        access.kicked_at = None
        await self._chat_access_repository.flush()


def _in_chat(member: ResultChatMemberUnion) -> bool:
    if isinstance(member, ChatMemberRestricted):
        return member.is_member
    return member.status not in OUT_OF_CHAT_STATUSES
