"""One shared HTTP helper that waits politely and retries when an API is busy."""

import time

import httpx

RETRY_STATUS = {429, 500, 502, 503, 504}


def get_with_retry(
    client: httpx.Client,
    url: str,
    *,
    params: dict | None = None,
    tries: int = 5,
    sleep=time.sleep,
) -> httpx.Response:
    """GET a URL. On "too many requests" or a server error, wait and try again.

    If the API says how long to wait (Retry-After or x-ratelimit-reset), we wait
    that long. Otherwise we back off 2, 4, 8, 16 seconds.
    """
    for attempt in range(tries):
        try:
            response = client.get(url, params=params)
        except httpx.TransportError:
            if attempt == tries - 1:
                raise
            sleep(2 ** (attempt + 1))
            continue
        if response.status_code not in RETRY_STATUS:
            response.raise_for_status()
            return response
        if attempt == tries - 1:
            response.raise_for_status()
        wait = response.headers.get("retry-after") or response.headers.get("x-ratelimit-reset")
        sleep(float(wait) + 1 if wait else 2 ** (attempt + 1))
    raise RuntimeError("unreachable")


class RateLimiter:
    """Keeps us under a fixed number of calls per minute (OpenAQ allows 60)."""

    def __init__(self, per_minute: int, clock=time.monotonic, sleep=time.sleep):
        self.gap = 60.0 / per_minute
        self.clock = clock
        self.sleep = sleep
        self.last = None

    def wait(self) -> None:
        now = self.clock()
        if self.last is not None and now - self.last < self.gap:
            self.sleep(self.gap - (now - self.last))
            now = self.clock()
        self.last = now
