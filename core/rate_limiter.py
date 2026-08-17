import time
from collections import deque
from collections.abc import Callable
from threading import Lock

class RateLimiter:
    def __init__(self, limit: int, window_seconds: int, clock: Callable[[], float] = time.monotonic):
        if limit < 1 or window_seconds < 1:
            raise ValueError("Rate limit and window must be positive")
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests: dict[str, deque[float]] = {}
        self._clock = clock
        self._lock = Lock()
        self._checks = 0

    def _discard_expired(self, timestamps: deque[float], now: float) -> None:
        while timestamps and now - timestamps[0] >= self.window_seconds:
            timestamps.popleft()

    def _prune_stale_clients(self, now: float) -> None:
        stale_clients = [
            client_id
            for client_id, timestamps in self.requests.items()
            if not timestamps or now - timestamps[-1] >= self.window_seconds
        ]
        for client_id in stale_clients:
            self.requests.pop(client_id, None)

    def is_allowed(self, ip: str) -> bool:
        client_id = ip or "unknown"
        now = self._clock()
        with self._lock:
            self._checks += 1
            if self._checks % 100 == 0:
                self._prune_stale_clients(now)

            timestamps = self.requests.setdefault(client_id, deque())
            self._discard_expired(timestamps, now)
            if len(timestamps) >= self.limit:
                return False

            timestamps.append(now)
            return True

# 10 calls per IP per hour
analyze_rate_limiter = RateLimiter(limit=10, window_seconds=3600)
