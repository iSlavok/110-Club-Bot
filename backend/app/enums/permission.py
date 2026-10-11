from enum import StrEnum


class Permission(StrEnum):
    CLUBS_VIEW = "clubs.view"
    CLUBS_EDIT = "clubs.edit"
    BLOCKS_EDIT = "blocks.edit"
    SYNC_RUN = "sync.run"
    USERS_VIEW = "users.view"
    ADMINS_VIEW = "admins.view"
    ADMINS_EDIT = "admins.edit"
    ROLES_EDIT = "roles.edit"
    LESSONS_VIEW = "lessons.view"
    LESSONS_EDIT = "lessons.edit"
    SETTINGS_EDIT = "settings.edit"


class PermissionGroup(StrEnum):
    CLUBS = "clubs"
    LESSONS = "lessons"
    USERS = "users"
    ADMINS = "admins"
    SETTINGS = "settings"


def known_permissions(values: list[str]) -> frozenset[Permission]:
    return frozenset(Permission(value) for value in values if value in Permission)
