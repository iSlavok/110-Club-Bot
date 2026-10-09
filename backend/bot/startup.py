from dishka import AsyncContainer

from app.services import BotAdminService


# Startup observers get no request scope from dishka's middleware, so the hook opens its own.
async def sync_command_menus(container: AsyncContainer) -> None:
    async with container() as request_container:
        bot_admin_service = await request_container.get(BotAdminService)
        await bot_admin_service.sync_command_menus()
