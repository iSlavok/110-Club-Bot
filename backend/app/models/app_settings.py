from sqlalchemy import CheckConstraint
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.database import Base, str_enum
from app.enums import VkLinkMode

APP_SETTINGS_ID = 1


# The only row is created by a migration: bot settings that admins change without a redeploy.
class AppSettings(Base):
    __table_args__ = (CheckConstraint(f"id = {APP_SETTINGS_ID}", name="single_row"),)

    vk_link_mode: Mapped[VkLinkMode] = mapped_column(str_enum(VkLinkMode), server_default=VkLinkMode.OAUTH.value)

    # Base pluralizes the class name, which would give "app_settingss".
    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        return "app_settings"
