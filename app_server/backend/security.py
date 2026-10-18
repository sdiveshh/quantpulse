import os
import secrets
import time
from collections import defaultdict, deque
from typing import Optional

from fastapi import Header, HTTPException, Request


def require_api_key(x_api_key: Optional[str] = Header(default=None)):
    expected = os.getenv("API_KEY")
    if not expected:
        return
    if not x_api_key or not secrets.compare_digest(x_api_key.encode(), expected.encode()):
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


class RateLimiter:
    """Sliding window limiter kept in memory (one process). Use Redis if you scale out."""

    def __init__(self, limit: int, window: float):
        self.limit = limit
        self.window = window
        self.hits = defaultdict(deque)

    def check(self, key: str) -> int:
        """Return 0 when allowed, otherwise the seconds to wait."""
        now = time.monotonic()
        q = self.hits[key]
        while q and now - q[0] >= self.window:
            q.popleft()
        if len(q) >= self.limit:
            return max(1, int(self.window - (now - q[0])) + 1)
        q.append(now)
        return 0


general_limiter = RateLimiter(limit=120, window=60)
chat_limiter = RateLimiter(limit=4, window=60)


def client_id(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for") if os.getenv("TRUST_PROXY") == "1" else None
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def _limit(limiter: RateLimiter):
    def dependency(request: Request):
        wait = limiter.check(client_id(request))
        if wait:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please slow down.",
                headers={"Retry-After": str(wait)},
            )

    return dependency


general_limit = _limit(general_limiter)
chat_limit = _limit(chat_limiter)