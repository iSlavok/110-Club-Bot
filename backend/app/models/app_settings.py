from sqlalchemy import CheckConstraint, Integer
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, declared_attr, mapped_column

from app.database import Base, str_enum
from app.enums import VkLinkMode

APP_SETTINGS_ID = 1


# The only row is created by a migration: bot settings that admins change without a redeploy.
class AppSettings(Base):
    __table_args__ = (CheckConstraint(f"id = {APP_SETTINGS_ID}", name="single_row"),)

    vk_link_mode: Mapped[VkLinkMode] = mapped_column(str_enum(VkLinkMode), server_default=VkLinkMode.OAUTH.value)
    # Minutes before the lesson start / homework deadline, prefilled in a new lesson.
    default_lesson_offsets: Mapped[list[int]] = mapped_column(ARRAY(Integer), server_default="{1440,60,0}")
    default_homework_offsets: Mapped[list[int]] = mapped_column(ARRAY(Integer), server_default="{2880,1440,180}")

    # Base pluralizes the class name, which would give "app_settingss".
    @declared_attr.directive
    @classmethod
    def __tablename__(cls) -> str:
        return "app_settings"
