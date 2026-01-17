"""Persistent SQLite cache for stock data with rate limiting.

This module provides a caching layer using SQLite file-based database
to minimize repeated API/HTTP requests for the same ticker across sessions.
Also includes rate limiting to avoid Yahoo Finance API throttling.
"""

import json
import logging
import sqlite3
import time
import os
from dataclasses import asdict
from pathlib import Path
from typing import Optional, List, Tuple

from .models import StockInfo

logger = logging.getLogger("sangre_signal.cache")

# Default cache TTL in seconds (4 hours - stock data doesn't change frequently)
DEFAULT_TTL = 4 * 3600

# Rate limiting settings
RATE_LIMIT_WINDOW = 3600  # 1 hour window
RATE_LIMIT_MAX_REQUESTS = 80  # Max requests per hour (conservative limit)

# Cache file location
def _get_cache_path() -> str:
    """Get the path for the cache database file."""
    # Use user's home directory for cache
    cache_dir = Path.home() / ".cache" / "sangre-signal"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return str(cache_dir / "stock_cache.db")


class StockCache:
    """Persistent SQLite cache for stock data with rate limiting.

    Caches stock info, ADR status, and directors to avoid repeated
    network requests for the same ticker. Persists data across sessions
    and includes rate limiting to prevent API throttling.
    """

    def __init__(self, ttl: int = DEFAULT_TTL, db_path: str = None):
        """Initialize the persistent cache.

        Args:
            ttl: Time-to-live for cache entries in seconds (default: 4 hours)
            db_path: Path to SQLite database file (default: ~/.cache/sangre-signal/)
        """
        self.ttl = ttl
        self.db_path = db_path or _get_cache_path()
        self.conn = sqlite3.connect(self.db_path, check_same_thread=False)
        self._create_tables()
        self._cleanup_old_entries()
        logger.info(f"Initialized persistent stock cache at {self.db_path}")

    def _create_tables(self) -> None:
        """Create the cache tables."""
        cursor = self.conn.cursor()

        # Stock info cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_info (
                ticker TEXT PRIMARY KEY,
                data TEXT NOT NULL,
                cached_at REAL NOT NULL
            )
        """)

        # ADR status cache (from FinViz)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS adr_status (
                ticker TEXT PRIMARY KEY,
                is_adr INTEGER,
                cached_at REAL NOT NULL
            )
        """)

        # Directors cache
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS directors (
                ticker TEXT PRIMARY KEY,
                directors TEXT NOT NULL,
                cached_at REAL NOT NULL
            )
        """)

        # Rate limiting table - tracks API requests
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS rate_limit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_time REAL NOT NULL,
                endpoint TEXT DEFAULT 'yahoo'
            )
        """)

        # Create index for faster rate limit queries
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_rate_limit_time
            ON rate_limit(request_time)
        """)

        self.conn.commit()
        logger.debug("Cache tables created")

    def _cleanup_old_entries(self) -> None:
        """Clean up expired cache entries and old rate limit records."""
        cursor = self.conn.cursor()
        now = time.time()
        cutoff = now - self.ttl

        # Clean up expired stock info
        cursor.execute("DELETE FROM stock_info WHERE cached_at < ?", (cutoff,))

        # Clean up expired ADR status
        cursor.execute("DELETE FROM adr_status WHERE cached_at < ?", (cutoff,))

        # Clean up expired directors
        cursor.execute("DELETE FROM directors WHERE cached_at < ?", (cutoff,))

        # Clean up old rate limit records (older than 1 hour)
        rate_cutoff = now - RATE_LIMIT_WINDOW
        cursor.execute("DELETE FROM rate_limit WHERE request_time < ?", (rate_cutoff,))

        self.conn.commit()
        logger.debug("Cleaned up expired cache entries")

    def _is_expired(self, cached_at: float) -> bool:
        """Check if a cache entry has expired.

        Args:
            cached_at: Unix timestamp when the entry was cached

        Returns:
            True if expired, False otherwise
        """
        return time.time() - cached_at > self.ttl

    def get_stock_info(self, ticker: str) -> Optional[StockInfo]:
        """Retrieve cached stock info for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            StockInfo if cached and not expired, None otherwise
        """
        ticker = ticker.upper()
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT data, cached_at FROM stock_info WHERE ticker = ?",
            (ticker,)
        )
        row = cursor.fetchone()

        if row is None:
            logger.debug(f"Cache miss for stock_info: {ticker}")
            return None

        data, cached_at = row
        if self._is_expired(cached_at):
            logger.debug(f"Cache expired for stock_info: {ticker}")
            self._delete_stock_info(ticker)
            return None

        logger.info(f"Cache hit for stock_info: {ticker}")
        return self._deserialize_stock_info(data)

    def set_stock_info(self, stock_info: StockInfo) -> None:
        """Cache stock info for a ticker.

        Args:
            stock_info: StockInfo object to cache
        """
        ticker = stock_info.ticker.upper()
        data = self._serialize_stock_info(stock_info)
        cached_at = time.time()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO stock_info (ticker, data, cached_at)
            VALUES (?, ?, ?)
            """,
            (ticker, data, cached_at)
        )
        self.conn.commit()
        logger.debug(f"Cached stock_info for {ticker}")

    def _delete_stock_info(self, ticker: str) -> None:
        """Delete cached stock info for a ticker."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM stock_info WHERE ticker = ?", (ticker,))
        self.conn.commit()

    def _serialize_stock_info(self, stock_info: StockInfo) -> str:
        """Serialize StockInfo to JSON string."""
        return json.dumps(asdict(stock_info))

    def _deserialize_stock_info(self, data: str) -> StockInfo:
        """Deserialize JSON string to StockInfo."""
        d = json.loads(data)
        return StockInfo(**d)

    def get_adr_status(self, ticker: str) -> Tuple[Optional[bool], bool]:
        """Retrieve cached ADR status for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Tuple of (is_adr, cache_hit). is_adr is None if not in cache
            or if FinViz returned None. cache_hit is True if found in cache.
        """
        ticker = ticker.upper()
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT is_adr, cached_at FROM adr_status WHERE ticker = ?",
            (ticker,)
        )
        row = cursor.fetchone()

        if row is None:
            logger.debug(f"Cache miss for adr_status: {ticker}")
            return None, False

        is_adr_int, cached_at = row
        if self._is_expired(cached_at):
            logger.debug(f"Cache expired for adr_status: {ticker}")
            self._delete_adr_status(ticker)
            return None, False

        # Convert from integer (0, 1, or NULL) back to Optional[bool]
        is_adr = None if is_adr_int is None else bool(is_adr_int)
        logger.info(f"Cache hit for adr_status: {ticker}")
        return is_adr, True

    def set_adr_status(self, ticker: str, is_adr: Optional[bool]) -> None:
        """Cache ADR status for a ticker.

        Args:
            ticker: Stock ticker symbol
            is_adr: ADR status (True, False, or None if unknown)
        """
        ticker = ticker.upper()
        # Convert Optional[bool] to integer for SQLite
        is_adr_int = None if is_adr is None else int(is_adr)
        cached_at = time.time()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO adr_status (ticker, is_adr, cached_at)
            VALUES (?, ?, ?)
            """,
            (ticker, is_adr_int, cached_at)
        )
        self.conn.commit()
        logger.debug(f"Cached adr_status for {ticker}: {is_adr}")

    def _delete_adr_status(self, ticker: str) -> None:
        """Delete cached ADR status for a ticker."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM adr_status WHERE ticker = ?", (ticker,))
        self.conn.commit()

    def get_directors(self, ticker: str) -> Tuple[Optional[List[str]], bool]:
        """Retrieve cached directors for a ticker.

        Args:
            ticker: Stock ticker symbol

        Returns:
            Tuple of (directors_list, cache_hit). directors_list is None
            if not in cache. cache_hit is True if found in cache.
        """
        ticker = ticker.upper()
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT directors, cached_at FROM directors WHERE ticker = ?",
            (ticker,)
        )
        row = cursor.fetchone()

        if row is None:
            logger.debug(f"Cache miss for directors: {ticker}")
            return None, False

        directors_json, cached_at = row
        if self._is_expired(cached_at):
            logger.debug(f"Cache expired for directors: {ticker}")
            self._delete_directors(ticker)
            return None, False

        logger.info(f"Cache hit for directors: {ticker}")
        return json.loads(directors_json), True

    def set_directors(self, ticker: str, directors: List[str]) -> None:
        """Cache directors for a ticker.

        Args:
            ticker: Stock ticker symbol
            directors: List of director names/titles
        """
        ticker = ticker.upper()
        directors_json = json.dumps(directors)
        cached_at = time.time()

        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT OR REPLACE INTO directors (ticker, directors, cached_at)
            VALUES (?, ?, ?)
            """,
            (ticker, directors_json, cached_at)
        )
        self.conn.commit()
        logger.debug(f"Cached {len(directors)} directors for {ticker}")

    def _delete_directors(self, ticker: str) -> None:
        """Delete cached directors for a ticker."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM directors WHERE ticker = ?", (ticker,))
        self.conn.commit()

    # --- Rate Limiting Methods ---

    def record_request(self, endpoint: str = "yahoo") -> None:
        """Record an API request for rate limiting.

        Args:
            endpoint: API endpoint identifier (default: 'yahoo')
        """
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO rate_limit (request_time, endpoint) VALUES (?, ?)",
            (time.time(), endpoint)
        )
        self.conn.commit()

    def get_request_count(self, endpoint: str = "yahoo") -> int:
        """Get the number of requests made in the current rate limit window.

        Args:
            endpoint: API endpoint identifier (default: 'yahoo')

        Returns:
            Number of requests made in the last hour
        """
        cursor = self.conn.cursor()
        cutoff = time.time() - RATE_LIMIT_WINDOW
        cursor.execute(
            "SELECT COUNT(*) FROM rate_limit WHERE request_time > ? AND endpoint = ?",
            (cutoff, endpoint)
        )
        return cursor.fetchone()[0]

    def is_rate_limited(self, endpoint: str = "yahoo") -> bool:
        """Check if we've exceeded the rate limit.

        Args:
            endpoint: API endpoint identifier (default: 'yahoo')

        Returns:
            True if rate limited, False otherwise
        """
        count = self.get_request_count(endpoint)
        is_limited = count >= RATE_LIMIT_MAX_REQUESTS
        if is_limited:
            logger.warning(
                f"Rate limit reached: {count}/{RATE_LIMIT_MAX_REQUESTS} requests "
                f"in the last hour for {endpoint}"
            )
        return is_limited

    def get_rate_limit_reset_time(self, endpoint: str = "yahoo") -> Optional[float]:
        """Get the time until rate limit resets (oldest request expires).

        Args:
            endpoint: API endpoint identifier (default: 'yahoo')

        Returns:
            Seconds until rate limit resets, or None if not rate limited
        """
        if not self.is_rate_limited(endpoint):
            return None

        cursor = self.conn.cursor()
        cutoff = time.time() - RATE_LIMIT_WINDOW
        cursor.execute(
            "SELECT MIN(request_time) FROM rate_limit WHERE request_time > ? AND endpoint = ?",
            (cutoff, endpoint)
        )
        oldest = cursor.fetchone()[0]
        if oldest:
            reset_time = oldest + RATE_LIMIT_WINDOW - time.time()
            return max(0, reset_time)
        return None

    def get_rate_limit_status(self, endpoint: str = "yahoo") -> dict:
        """Get current rate limit status.

        Args:
            endpoint: API endpoint identifier (default: 'yahoo')

        Returns:
            Dict with 'requests_made', 'requests_remaining', 'is_limited', 'reset_in_seconds'
        """
        count = self.get_request_count(endpoint)
        remaining = max(0, RATE_LIMIT_MAX_REQUESTS - count)
        is_limited = count >= RATE_LIMIT_MAX_REQUESTS
        reset_time = self.get_rate_limit_reset_time(endpoint) if is_limited else None

        return {
            "requests_made": count,
            "requests_remaining": remaining,
            "max_requests": RATE_LIMIT_MAX_REQUESTS,
            "is_limited": is_limited,
            "reset_in_seconds": reset_time,
            "window_seconds": RATE_LIMIT_WINDOW,
        }

    def clear(self) -> None:
        """Clear all cached data (but preserve rate limit records)."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM stock_info")
        cursor.execute("DELETE FROM adr_status")
        cursor.execute("DELETE FROM directors")
        self.conn.commit()
        logger.info("Cache cleared")

    def clear_all(self) -> None:
        """Clear all data including rate limit records."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM stock_info")
        cursor.execute("DELETE FROM adr_status")
        cursor.execute("DELETE FROM directors")
        cursor.execute("DELETE FROM rate_limit")
        self.conn.commit()
        logger.info("All cache and rate limit data cleared")

    def close(self) -> None:
        """Close the database connection."""
        self.conn.close()
        logger.debug("Cache connection closed")


# Global cache instance (initialized lazily)
_cache: Optional[StockCache] = None


def get_cache() -> StockCache:
    """Get the global cache instance, creating it if necessary.

    Returns:
        The global StockCache instance
    """
    global _cache
    if _cache is None:
        _cache = StockCache()
    return _cache


def clear_cache() -> None:
    """Clear the global cache."""
    global _cache
    if _cache is not None:
        _cache.clear()
