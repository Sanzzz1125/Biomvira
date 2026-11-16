"""Keep the free Render instance awake during the day.

Render's free plan stops an instance after 15 minutes without incoming requests, and the first request after that
waits up to a minute. While the instance is running on Render (RENDER_EXTERNAL_URL is set by Render itself), it calls
its own public health endpoint every 10 minutes between 6:30 AM and 11 PM India time. The request goes through
Render's public proxy, so it counts as traffic. At night no calls are made and the instance may sleep; the scheduled
GitHub job wakes it again in the morning.
"""
import asyncio
import os
from datetime import datetime, time, timedelta, timezone

import httpx

IST = timezone(timedelta(hours=5, minutes=30))
DAY_START, DAY_END = time(6, 30), time(23, 0)
INTERVAL_SECONDS = 600


def is_daytime(moment: datetime) -> bool:
    local = moment.astimezone(IST).time()
    return DAY_START <= local < DAY_END


async def keep_awake(url: str, interval: float = INTERVAL_SECONDS) -> None:
    async with httpx.AsyncClient(timeout=30) as client:
        while True:
            await asyncio.sleep(interval)
            if is_daytime(datetime.now(timezone.utc)):
                try:
                    await client.get(url)
                except httpx.HTTPError:
                    pass  # a missed ping only means the next one matters; never crash the server


def start() -> "asyncio.Task | None":
    base = os.environ.get("RENDER_EXTERNAL_URL", "").rstrip("/")
    if not base:
        return None  # local development and tests: nothing to keep awake
    return asyncio.create_task(keep_awake(f"{base}/api/health"))
