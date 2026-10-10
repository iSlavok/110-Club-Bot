from dishka import Provider, Scope, provide_all

from app.queries import (
    ChatAccessQueries,
    ClubStatsQueries,
    MembershipQueries,
    MembershipRemovalQueries,
    SystemQueries,
)
from app.repositories import (
    AdminSessionRepository,
    AdminUserRepository,
    AppSettingsRepository,
    BlockRepository,
    ChatAccessRepository,
    ClubRepository,
    LessonRepository,
    LoginCodeRepository,
    MembershipRemovalItemRepository,
    MembershipRemovalRequestRepository,
    MembershipRepository,
    ReminderRepository,
    RoleRepository,
    SheetSyncRepository,
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
    ChatAccessService,
    ClubService,
    ClubStatsService,
    HealthService,
    LessonService,
    LoginService,
    MembershipRemovalService,
    ReminderDispatchService,
    ReminderPlanner,
    ReminderService,
    RoleService,
    SheetSyncService,
    StatusService,
    StudentStatusService,
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
        ChatAccessRepository,
        ClubRepository,
        LessonRepository,
        LoginCodeRepository,
        MembershipRemovalItemRepository,
        MembershipRemovalRequestRepository,
        MembershipRepository,
        ReminderRepository,
        RoleRepository,
        SheetSyncRepository,
        UserRepository,
        VkAuthRequestRepository,
    )


class QueriesProvider(Provider):
    scope = Scope.REQUEST

    queries = provide_all(
        ChatAccessQueries, ClubStatsQueries, MembershipQueries, MembershipRemovalQueries, SystemQueries
    )


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
        ChatAccessService,
        ClubService,
        ClubStatsService,
        HealthService,
        LessonService,
        LoginService,
        MembershipRemovalService,
        ReminderDispatchService,
        ReminderPlanner,
        ReminderService,
        RoleService,
        StatusService,
        StudentStatusService,
        SheetSyncService,
        UserService,
        VkLinkAvailability,
        VkLinkService,
    )
