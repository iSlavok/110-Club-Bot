from dishka import Provider, Scope, provide_all

from app.queries import AccessQueries, ClubStatsQueries, SystemQueries
from app.repositories import (
    AdminSessionRepository,
    AdminUserRepository,
    AppSettingsRepository,
    BlockRepository,
    ClubRepository,
    LoginCodeRepository,
    MembershipRepository,
    RoleRepository,
    UserRepository,
    VkAuthRequestRepository,
)
from app.services import (
    AdminAccessResolver,
    AdminSessionService,
    AdminUserService,
    AppSettingsService,
    AuthCleanupService,
    BlockService,
    BotAdminService,
    ClubService,
    ClubStatsService,
    HealthService,
    LoginService,
    RoleService,
    StatusService,
    UserService,
    VkLinkAvailability,
    VkLinkService,
)


class RepositoriesProvider(Provider):
    scope = Scope.REQUEST

    repositories = provide_all(
        AdminSessionRepository,
        AdminUserRepository,
        AppSettingsRepository,
        BlockRepository,
        ClubRepository,
        LoginCodeRepository,
        MembershipRepository,
        RoleRepository,
        UserRepository,
        VkAuthRequestRepository,
    )


class QueriesProvider(Provider):
    scope = Scope.REQUEST

    queries = provide_all(AccessQueries, ClubStatsQueries, SystemQueries)


class ServicesProvider(Provider):
    scope = Scope.REQUEST

    services = provide_all(
        AdminAccessResolver,
        AdminSessionService,
        AdminUserService,
        AppSettingsService,
        AuthCleanupService,
        BlockService,
        BotAdminService,
        ClubService,
        ClubStatsService,
        HealthService,
        LoginService,
        RoleService,
        StatusService,
        UserService,
        VkLinkAvailability,
        VkLinkService,
    )
