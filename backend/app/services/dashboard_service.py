from app.queries import DashboardQueries
from app.schemas import DashboardStats
from app.utils import Clock


class DashboardService:
    def __init__(self, dashboard_queries: DashboardQueries, clock: Clock) -> None:
        self._dashboard_queries = dashboard_queries
        self._clock = clock

    async def get_stats(self) -> DashboardStats:
        counts = await self._dashboard_queries.counts(self._clock.now())
        return DashboardStats(
            active_clubs=counts.active_clubs,
            current_blocks=counts.current_blocks,
            users=counts.users,
            users_with_vk=counts.users_with_vk,
        )
