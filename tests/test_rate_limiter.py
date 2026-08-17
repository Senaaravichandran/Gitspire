import unittest
from concurrent.futures import ThreadPoolExecutor

from core.rate_limiter import RateLimiter


class MutableClock:
    def __init__(self):
        self.value = 0.0

    def __call__(self) -> float:
        return self.value


class RateLimiterTests(unittest.TestCase):
    def test_resets_after_window(self):
        clock = MutableClock()
        limiter = RateLimiter(limit=2, window_seconds=10, clock=clock)

        self.assertTrue(limiter.is_allowed("client"))
        self.assertTrue(limiter.is_allowed("client"))
        self.assertFalse(limiter.is_allowed("client"))

        clock.value = 10.0
        self.assertTrue(limiter.is_allowed("client"))

    def test_concurrent_requests_cannot_exceed_limit(self):
        limiter = RateLimiter(limit=10, window_seconds=60, clock=lambda: 1.0)
        with ThreadPoolExecutor(max_workers=20) as executor:
            results = list(executor.map(lambda _: limiter.is_allowed("client"), range(100)))

        self.assertEqual(sum(results), 10)

    def test_periodic_cleanup_removes_stale_clients(self):
        clock = MutableClock()
        limiter = RateLimiter(limit=1, window_seconds=10, clock=clock)
        self.assertTrue(limiter.is_allowed("stale-client"))

        clock.value = 20.0
        for index in range(99):
            limiter.is_allowed(f"active-{index}")

        self.assertNotIn("stale-client", limiter.requests)


if __name__ == "__main__":
    unittest.main()
