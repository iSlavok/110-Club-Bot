from app.config import PublicSettings, VkSettings
from app.enums import VkLinkMode


class VkLinkAvailability:
    def __init__(self, vk_settings: VkSettings, public_settings: PublicSettings) -> None:
        self._vk_settings = vk_settings
        self._public_settings = public_settings

    def is_configured(self, mode: VkLinkMode) -> bool:
        match mode:
            case VkLinkMode.LINK:
                return self._vk_settings.service_token is not None
            case VkLinkMode.OAUTH:
                # VK ID redirects back to the public API, so it needs both the app id and the public address.
                return self._vk_settings.client_id is not None and self._public_settings.url is not None

    def configured_modes(self) -> list[VkLinkMode]:
        return [mode for mode in VkLinkMode if self.is_configured(mode)]
