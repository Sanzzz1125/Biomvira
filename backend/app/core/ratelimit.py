"""Small in-memory rate limiter for login and sign-up endpoints (single server instance)."""
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request

from app.config import settings


def client_ip(request: Request) -> str:
    # Vercel sets X-Forwarded-For to the real client address before proxying to the API.
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()[:64]
    return (request.client.host if request.client else "unknown")[:64]


class RateLimiter:
    def __init__(self) -> None:
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def allow(self, key: str, limit: int, window_seconds: int = 60) -> bool:
        now = time.monotonic()
        with self._lock:
            hits = self._hits[key]
            while hits and now - hits[0] > window_seconds:
                hits.popleft()
            if len(hits) >= limit:
                return False
            hits.append(now)
            return True

    def reset(self) -> None:
        with self._lock:
            self._hits.clear()


limiter = RateLimiter()


def enforce_rate_limit(request: Request, bucket: str) -> None:
    if not limiter.allow(f"{bucket}:{client_ip(request)}", settings.auth_rate_limit_per_minute):
        raise HTTPException(429, "Too many attempts. Please wait a minute and try again.")
