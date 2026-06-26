"""
Systems data analysis: real-time performance metrics collection.
Tracks p50/p95/p99 query latency, cache hit rates, and throughput.
"""
import statistics
from collections import deque
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional


@dataclass
class MetricsCollector:
    """
    Collects and aggregates system performance metrics for
    query pipeline observability and systems data analysis.
    
    Tracks:
        - Query latency percentiles (p50, p95, p99)
        - Cache hit/miss rates
        - Total throughput
        - Error rates
    """
    _latencies: deque = field(default_factory=lambda: deque(maxlen=1000))
    _cache_hits: int = 0
    _cache_misses: int = 0
    _total_queries: int = 0
    _errors: int = 0
    _lock: Lock = field(default_factory=Lock)

    def record_query(self, latency_ms: float, cache_hit: bool):
        """Record a completed query with latency and cache status."""
        with self._lock:
            self._latencies.append(latency_ms)
            self._total_queries += 1
            if cache_hit:
                self._cache_hits += 1
            else:
                self._cache_misses += 1

    def record_error(self):
        """Record a failed query."""
        with self._lock:
            self._errors += 1

    def get_summary(self) -> dict:
        """
        Get aggregated performance metrics.
        
        Returns:
            Dictionary with latency percentiles, cache stats, and throughput
        """
        with self._lock:
            lats = sorted(self._latencies)
            n = len(lats)

            if n == 0:
                return {
                    "total_queries": self._total_queries,
                    "errors": self._errors,
                    "status": "no_data",
                }

            def percentile(p: int) -> float:
                """Calculate percentile from sorted latencies."""
                idx = int(p * n / 100)
                # Handle edge cases
                if idx >= n:
                    idx = n - 1
                return round(lats[idx], 2)

            total_cache = self._cache_hits + self._cache_misses
            hit_rate = (
                round(100 * self._cache_hits / total_cache, 1)
                if total_cache > 0
                else 0.0
            )

            return {
                "total_queries": self._total_queries,
                "errors": self._errors,
                "error_rate_pct": round(100 * self._errors / max(self._total_queries, 1), 2),
                "latency_ms": {
                    "p50": percentile(50),
                    "p95": percentile(95),
                    "p99": percentile(99),
                    "mean": round(statistics.mean(lats), 2),
                    "min": round(lats[0], 2),
                    "max": round(lats[-1], 2),
                },
                "cache": {
                    "hit_rate_pct": hit_rate,
                    "hits": self._cache_hits,
                    "misses": self._cache_misses,
                    "total": total_cache,
                },
                "samples": n,
            }

    def reset(self):
        """Reset all metrics (useful for testing)."""
        with self._lock:
            self._latencies.clear()
            self._cache_hits = 0
            self._cache_misses = 0
            self._total_queries = 0
            self._errors = 0


# Global singleton instance
metrics = MetricsCollector()
