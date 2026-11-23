"""HTTP session with retries, timeouts and a polite rate limit shared across threads."""

from __future__ import annotations

import threading
import time

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

USER_AGENT = "Mozilla/5.0 (compatible; CatalogScraper/1.0; +https://github.com/)"


class RateLimiter:
    """Allow at most one request every ``interval`` seconds across all threads."""

    def __init__(self, interval: float):
        self.interval = interval
        self._lock = threading.Lock()
        self._next = 0.0

    def wait(self) -> None:
        with self._lock:
            now = time.monotonic()
            delay = self._next - now
            self._next = max(now, self._next) + self.interval
        if delay > 0:
            time.sleep(delay)


class Fetcher:
    def __init__(self, delay: float = 0.2, timeout: float = 20, retries: int = 4):
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": USER_AGENT, "Accept-Language": "en"})
        retry = Retry(
            total=retries,
            backoff_factor=0.8,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=("GET",),
            respect_retry_after_header=True,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=16, pool_maxsize=16)
        self.session.mount("https://", adapter)
        self.session.mount("http://", adapter)
        self.timeout = timeout
        self.limiter = RateLimiter(delay)
        self.requests_made = 0

    def get(self, url: str) -> str:
        self.limiter.wait()
        resp = self.session.get(url, timeout=self.timeout)
        resp.raise_for_status()
        self.requests_made += 1
        # The site declares UTF-8 in <meta>, not in the header: decode the bytes ourselves.
        return resp.content.decode("utf-8", errors="replace")
