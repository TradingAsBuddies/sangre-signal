"""In-memory SQLite cache for stock data.

This module provides a caching layer using SQLite in-memory database
to minimize repeated API/HTTP requests for the same ticker.
"""

import json
import logging
import sqlite3
import time
from dataclasses import asdict
from typing import Optional, List, Tuple

from .models import StockInfo

logger = logging.getLogger("super_signal.cache")

# Default cache TTL in seconds (1 hour)
DEFAULT_TTL = 3600


class StockCache:
    """In-memory SQLite cache for stock data.

    Caches stock info, ADR status, and directors to avoid repeated
    network requests for the same ticker within a session.
    """

    def __init__(self, ttl: int = DEFAULT_TTL):
        """Initialize the in-memory cache.

        Args:
            ttl: Time-to-live for cache entries in seconds (default: 1 hour)
        """
        self.ttl = ttl
        self.conn = sqlite3.connect(":memory:", check_same_thread=False)
        self._create_tables()
        logger.info("Initialized in-memory stock cache")

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

        self.conn.commit()
        logger.debug("Cache tables created")

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

    def clear(self) -> None:
        """Clear all cached data."""
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM stock_info")
        cursor.execute("DELETE FROM adr_status")
        cursor.execute("DELETE FROM directors")
        self.conn.commit()
        logger.info("Cache cleared")

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
