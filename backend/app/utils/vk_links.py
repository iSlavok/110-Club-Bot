import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from app.types import INT64_MAX

_VK_HOSTS = frozenset({"vk.com", "vk.ru", "m.vk.com", "m.vk.ru", "www.vk.com", "www.vk.ru"})
_NUMERIC_ID = re.compile(r"(?:id)?(\d+)", re.IGNORECASE)
_SCREEN_NAME = re.compile(r"[a-z0-9_.]{1,64}", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class VkIdReference:
    user_id: int


@dataclass(frozen=True, slots=True)
class VkScreenNameReference:
    screen_name: str


type VkReference = VkIdReference | VkScreenNameReference


# Accepts what students paste: vk.com/id123, https://m.vk.com/kate.orlova?from=search, @kate.orlova, id123, 123.
def parse_vk_reference(text: str) -> VkReference | None:
    value = text.strip().removeprefix("@")
    if "/" in value or "vk.com" in value.lower() or "vk.ru" in value.lower():
        value = _profile_path(value)
        if value is None:
            return None
    if match := _NUMERIC_ID.fullmatch(value):
        user_id = int(match.group(1))
        return VkIdReference(user_id) if 0 < user_id <= INT64_MAX else None
    if _SCREEN_NAME.fullmatch(value):
        return VkScreenNameReference(value.lower())
    return None


def _profile_path(link: str) -> str | None:
    parts = urlsplit(link if "://" in link else f"https://{link}")
    if parts.scheme not in {"http", "https"} or (parts.hostname or "").lower() not in _VK_HOSTS:
        return None
    path = parts.path.strip("/")
    return path if path and "/" not in path else None
