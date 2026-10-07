from dishka import Provider, Scope, provide_all

from app.queries import SystemQueries
from app.repositories import (
    AdminSessionRepository,
    AdminUserRepository,
    BlockRepository,
    ClubRepository,
    LoginCodeRepository,
    MembershipRepository,
    RoleRepository,
    UserRepository,
)
from app.services import (
    AdminAccessResolver,
    AdminSessionService,
    AdminUserService,
    BlockService,
    ClubService,
    HealthService,
    LoginService,
    RoleService,
    UserService,
)


class RepositoriesProvider(Provider):
    scope = Scope.REQUEST

    repositories = provide_all(
        AdminSessionRepository,
        AdminUserRepository,
        BlockRepository,
        ClubRepository,
        LoginCodeRepository,
        MembershipRepository,
        RoleRepository,
        UserRepository,
    )


class QueriesProvider(Provider):
    scope = Scope.REQUEST

    queries = provide_all(SystemQueries)


class ServicesProvider(Provider):
    scope = Scope.REQUEST

    services = provide_all(
        AdminAccessResolver,
        AdminSessionService,
        AdminUserService,
        BlockService,
        ClubService,
        HealthService,
        LoginService,
        RoleService,
        UserService,
    )
