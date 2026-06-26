"""
HTTP client with connection pooling, retry logic, and latency tracking.
Demonstrates networking optimization: TCP session reuse, exponential backoff.
"""
import asyncio
import httpx
import logging
import time
from typing import Optional

logger = logging.getLogger(__name__)


class NetworkAwareCrawler:
    """HTTP client with connection pooling, retry, and latency tracking."""

    def __init__(self, pool_size: int = 10, timeout: float = 10.0):
        self._limits = httpx.Limits(
            max_connections=pool_size,
            max_keepalive_connections=pool_size,
        )
        self._client: Optional[httpx.AsyncClient] = None
        self.timeout = timeout
        self.stats = {"requests": 0, "retries": 0, "total_latency_ms": 0.0}

    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            limits=self._limits,
            timeout=self.timeout,
            headers={"User-Agent": "MiniSearchEngine/1.0 (research)"},
        )
        return self

    async def __aexit__(self, *_):
        await self._client.aclose()

    async def get(self, url: str, params: dict = None, max_retries: int = 3) -> bytes:
        """Fetch URL with exponential backoff retry."""
        backoff = 1.0
        for attempt in range(max_retries):
            try:
                start = time.perf_counter()
                response = await self._client.get(url, params=params)
                latency_ms = (time.perf_counter() - start) * 1000

                self.stats["requests"] += 1
                self.stats["total_latency_ms"] += latency_ms

                response.raise_for_status()
                return response.content

            except (httpx.HTTPStatusError, httpx.TimeoutException) as e:
                self.stats["retries"] += 1
                if attempt == max_retries - 1:
                    raise
                logger.warning(f"Retry {attempt+1}/{max_retries} for {url}: {e}")
                await asyncio.sleep(backoff)
                backoff *= 2  # exponential backoff

    def get_network_stats(self) -> dict:
        """Return aggregated network performance metrics."""
        avg = (
            self.stats["total_latency_ms"] / self.stats["requests"]
            if self.stats["requests"]
            else 0
        )
        return {**self.stats, "avg_latency_ms": round(avg, 2)}
