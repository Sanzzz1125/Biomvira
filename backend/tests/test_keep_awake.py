import asyncio
from datetime import datetime, timezone

from app import keep_awake


def test_daytime_window_in_india_time():
    # 6:30 AM IST is 01:00 UTC; 11 PM IST is 17:30 UTC.
    assert not keep_awake.is_daytime(datetime(2026, 11, 16, 0, 59, tzinfo=timezone.utc))
    assert keep_awake.is_daytime(datetime(2026, 11, 16, 1, 0, tzinfo=timezone.utc))
    assert keep_awake.is_daytime(datetime(2026, 11, 16, 17, 29, tzinfo=timezone.utc))
    assert not keep_awake.is_daytime(datetime(2026, 11, 16, 17, 30, tzinfo=timezone.utc))


def test_not_started_outside_render(monkeypatch):
    monkeypatch.delenv("RENDER_EXTERNAL_URL", raising=False)
    assert keep_awake.start() is None


def test_pings_own_health_endpoint_on_render(monkeypatch):
    calls = []

    class Client:
        def __init__(self, timeout): pass
        async def __aenter__(self): return self
        async def __aexit__(self, *exc): return False
        async def get(self, url): calls.append(url)

    monkeypatch.setattr(keep_awake.httpx, "AsyncClient", Client)
    monkeypatch.setattr(keep_awake, "is_daytime", lambda moment: True)

    async def run():
        task = asyncio.create_task(keep_awake.keep_awake("https://example.onrender.com/api/health", interval=0.01))
        await asyncio.sleep(0.05)
        task.cancel()

    asyncio.run(run())
    assert calls and set(calls) == {"https://example.onrender.com/api/health"}
