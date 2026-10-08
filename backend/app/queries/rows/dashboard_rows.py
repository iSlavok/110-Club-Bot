from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DashboardCountsRow:
    active_clubs: int
    current_blocks: int
    users: int
    users_with_vk: int
