"""Keep the free Render instance awake from early morning until midnight (India time).

Render's free plan stops an instance after 15 minutes without incoming requests, and the first request after that
waits up to a minute. While the instance is running on Render (RENDER_EXTERNAL_URL is set by Render itself), it calls
its own public health endpoint every 10 minutes from 4:30 AM until midnight India time. The request goes through
Render's public proxy, so it counts as traffic. After midnight no calls are made and the instance sleeps; two daily
Vercel cron jobs (frontend/vercel.json, 4:30-5:29 AM and 5:30-6:29 AM IST) wake it again, so it is awake by 6 AM.
"""
import asyncio
import os
from datetime import datetime, time, timedelta, timezone

import httpx

IST = timezone(timedelta(hours=5, minutes=30))
DAY_START = time(4, 30)  # the first Vercel wake-up can arrive at 4:30 AM IST
INTERVAL_SECONDS = 600


def is_daytime(moment: datetime) -> bool:
    local = moment.astimezone(IST).time()
    return local >= DAY_START  # until midnight


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
