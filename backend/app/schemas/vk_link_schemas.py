from pydantic import BaseModel


class ClubAccess(BaseModel):
    club_title: str
    block_title: str
    # None when the club has no chat or Telegram refused to make the link.
    invite_link: str | None


class VkCandidate(BaseModel):
    vk_id: int
    full_name: str


class VkLinkResult(BaseModel):
    vk_id: int
    access: list[ClubAccess]


class VkAlreadyLinked(BaseModel):
    vk_id: int


class VkLinkByProfile(BaseModel):
    pass


class VkLinkByOAuth(BaseModel):
    authorize_url: str


class VkLinkUnavailable(BaseModel):
    pass


type VkLinkOffer = VkAlreadyLinked | VkLinkByProfile | VkLinkByOAuth | VkLinkUnavailable


class VkOAuthCompletion(BaseModel):
    # The state is unknown, used or expired: nothing happened and the user is not notified.
    is_expired: bool
    # None when Telegram is unreachable and the bot link cannot be built.
    bot_username: str | None
