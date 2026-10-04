from dishka import Provider, Scope, provide_all

from app.queries import SystemQueries
from app.repositories import UserRepository
from app.services import HealthService, UserService


class RepositoriesProvider(Provider):
    scope = Scope.REQUEST

    repositories = provide_all(UserRepository)


class QueriesProvider(Provider):
    scope = Scope.REQUEST

    queries = provide_all(SystemQueries)


class ServicesProvider(Provider):
    scope = Scope.REQUEST

    services = provide_all(HealthService, UserService)
