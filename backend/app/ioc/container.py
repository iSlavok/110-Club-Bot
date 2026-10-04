from dishka import AsyncContainer, make_async_container

from app.config import Settings
from app.ioc.database import DatabaseProvider
from app.ioc.infra import InfraProvider, SettingsProvider
from app.ioc.layers import QueriesProvider, RepositoriesProvider, ServicesProvider


def create_container(settings: Settings) -> AsyncContainer:
    return make_async_container(
        SettingsProvider(),
        InfraProvider(),
        DatabaseProvider(),
        RepositoriesProvider(),
        QueriesProvider(),
        ServicesProvider(),
        context={Settings: settings},
    )
