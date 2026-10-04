import asyncio
import signal

from aiogram import Bot
from redis.asyncio import Redis

from api import create_app, create_server
from app.config import ApiSettings, Settings, setup_logging
from app.ioc import create_container
from bot import create_dispatcher
from worker import create_scheduler


async def run() -> None:
    settings = Settings()  # pyright: ignore[reportCallIssue] - required fields come from the environment
    setup_logging(settings.log)
    container = create_container(settings)
    try:
        bot = await container.get(Bot)
        dispatcher = create_dispatcher(container, await container.get(Redis))
        server = create_server(create_app(container), await container.get(ApiSettings))
        scheduler = create_scheduler(container)

        stop = asyncio.Event()
        loop = asyncio.get_running_loop()
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(sig, stop.set)

        async with asyncio.TaskGroup() as tasks:
            tasks.create_task(server.serve())
            tasks.create_task(dispatcher.start_polling(bot, handle_signals=False, close_bot_session=False))
            scheduler.start()
            await stop.wait()

            scheduler.shutdown(wait=False)
            server.should_exit = True
            await dispatcher.stop_polling()
    finally:
        await container.close()


if __name__ == "__main__":
    asyncio.run(run())
