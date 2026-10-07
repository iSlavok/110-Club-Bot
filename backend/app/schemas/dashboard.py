from pydantic import BaseModel


class DashboardStats(BaseModel):
    active_clubs: int
    current_blocks: int
    users: int
    users_with_vk: int
