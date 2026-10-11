import pytest

from app.telegram.rate_limit import FloodGate
from tests.fakes import FakeTimer


async def test_passes_through_when_not_paused() -> None:
    timer = FakeTimer()

    await FloodGate(timer).wait()

    assert timer.sleeps == []


async def test_waits_until_the_pause_ends() -> None:
    timer = FakeTimer()
    gate = FloodGate(timer)
    gate.pause(3)

    await gate.wait()

    assert timer.now == pytest.approx(3.0)


async def test_shorter_pause_does_not_cut_a_longer_one() -> None:
    timer = FakeTimer()
    gate = FloodGate(timer)
    gate.pause(10)
    gate.pause(2)

    await gate.wait()

    assert timer.now == pytest.approx(10.0)
