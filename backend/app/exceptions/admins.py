from app.exceptions.base import AuthorizationError, ConflictError, NotFoundError


class RoleNotFoundError(NotFoundError):
    def __init__(self, role_id: int) -> None:
        super().__init__(f"Role {role_id} not found")


class RoleTitleTakenError(ConflictError):
    def __init__(self, title: str) -> None:
        super().__init__(f"Role '{title}' already exists")


class RoleInUseError(ConflictError):
    def __init__(self) -> None:
        super().__init__("Role is assigned to admins; reassign them first")


class AdminUserNotFoundError(NotFoundError):
    def __init__(self, admin_user_id: int) -> None:
        super().__init__(f"Admin {admin_user_id} not found")


class AdminAlreadyExistsError(ConflictError):
    def __init__(self, tg_id: int) -> None:
        super().__init__(f"Admin with Telegram id {tg_id} already exists")


class OwnerNotEditableError(AuthorizationError):
    def __init__(self) -> None:
        super().__init__("Owners are configured on the server and cannot be edited")


class OwnAccessChangeError(AuthorizationError):
    def __init__(self) -> None:
        super().__init__("You cannot change your own role or deactivate yourself")


class PermissionEscalationError(AuthorizationError):
    def __init__(self) -> None:
        super().__init__("You cannot grant or manage permissions you do not have")
