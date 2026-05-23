import time
from typing import Dict, List

class RateLimiter:
    def __init__(self, limit: int, window_seconds: int):
        self.limit = limit
        self.window_seconds = window_seconds
        self.requests: Dict[str, List[float]] = {}

    def is_allowed(self, ip: str) -> bool:
        now = time.time()
        if ip not in self.requests:
            self.requests[ip] = []
        
        # Clean up old timestamps
        self.requests[ip] = [t for t in self.requests[ip] if now - t < self.window_seconds]
        
        if len(self.requests[ip]) >= self.limit:
            return False
        
        self.requests[ip].append(now)
        return True

# 10 calls per IP per hour
analyze_rate_limiter = RateLimiter(limit=10, window_seconds=3600)
