from enum import StrEnum


class Permission(StrEnum):
    CLUBS_VIEW = "clubs.view"
    CLUBS_EDIT = "clubs.edit"
    BLOCKS_EDIT = "blocks.edit"
    USERS_VIEW = "users.view"
    ADMINS_VIEW = "admins.view"
    ADMINS_EDIT = "admins.edit"
    ROLES_EDIT = "roles.edit"


class PermissionGroup(StrEnum):
    CLUBS = "clubs"
    USERS = "users"
    ADMINS = "admins"
