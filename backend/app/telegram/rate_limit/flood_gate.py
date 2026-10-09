from app.telegram.rate_limit.timer import Timer


# Telegram's flood wait applies to the whole bot, so every request waits it out, not only the one that got the 429.
class FloodGate:
    def __init__(self, timer: Timer) -> None:
        self._timer = timer
        self._until = 0.0

    def pause(self, seconds: float) -> None:
        self._until = max(self._until, self._timer.monotonic() + seconds)

    async def wait(self) -> None:
        while (delay := self._until - self._timer.monotonic()) > 0:
            await self._timer.sleep(delay)
