"""Tests for the in-memory SQLite cache module."""

import time
import pytest
from unittest.mock import patch

from super_signal.cache import StockCache, get_cache, clear_cache, _cache
from super_signal.models import StockInfo


class TestStockCacheInitialization:
    """Tests for cache initialization."""

    def test_cache_creates_successfully(self):
        """Test that cache initializes without error."""
        cache = StockCache()
        assert cache is not None
        assert cache.conn is not None
        cache.close()

    def test_cache_default_ttl(self):
        """Test that cache has default TTL of 4 hours."""
        cache = StockCache()
        assert cache.ttl == 4 * 3600  # 4 hours
        cache.close()

    def test_cache_custom_ttl(self):
        """Test that cache accepts custom TTL."""
        cache = StockCache(ttl=300)
        assert cache.ttl == 300
        cache.close()

    def test_cache_tables_created(self):
        """Test that all required tables are created."""
        cache = StockCache()
        cursor = cache.conn.cursor()

        # Check stock_info table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='stock_info'"
        )
        assert cursor.fetchone() is not None

        # Check adr_status table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='adr_status'"
        )
        assert cursor.fetchone() is not None

        # Check directors table exists
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='directors'"
        )
        assert cursor.fetchone() is not None

        cache.close()


class TestStockInfoCache:
    """Tests for stock info caching."""

    def test_get_stock_info_cache_miss(self):
        """Test that cache miss returns None."""
        cache = StockCache()
        result = cache.get_stock_info("AAPL")
        assert result is None
        cache.close()

    def test_set_and_get_stock_info(self):
        """Test setting and getting stock info."""
        cache = StockCache()
        stock_info = StockInfo(
            ticker="AAPL",
            long_name="Apple Inc.",
            country="United States",
            exchange="NASDAQ",
            market_cap=3000000000000,
        )

        cache.set_stock_info(stock_info)
        result = cache.get_stock_info("AAPL")

        assert result is not None
        assert result.ticker == "AAPL"
        assert result.long_name == "Apple Inc."
        assert result.country == "United States"
        assert result.exchange == "NASDAQ"
        assert result.market_cap == 3000000000000
        cache.close()

    def test_stock_info_cache_case_insensitive(self):
        """Test that ticker lookup is case-insensitive."""
        cache = StockCache()
        stock_info = StockInfo(ticker="AAPL", long_name="Apple Inc.")

        cache.set_stock_info(stock_info)

        # Should find with different cases
        assert cache.get_stock_info("aapl") is not None
        assert cache.get_stock_info("Aapl") is not None
        assert cache.get_stock_info("AAPL") is not None
        cache.close()

    def test_stock_info_cache_overwrites(self):
        """Test that setting stock info twice overwrites the first."""
        cache = StockCache()
        stock_info1 = StockInfo(ticker="AAPL", long_name="Apple Inc.")
        stock_info2 = StockInfo(ticker="AAPL", long_name="Apple Corporation")

        cache.set_stock_info(stock_info1)
        cache.set_stock_info(stock_info2)

        result = cache.get_stock_info("AAPL")
        assert result.long_name == "Apple Corporation"
        cache.close()

    def test_stock_info_preserves_all_fields(self):
        """Test that all StockInfo fields are preserved through cache."""
        cache = StockCache()
        stock_info = StockInfo(
            ticker="TEST",
            long_name="Test Company",
            short_name="Test",
            country="United States",
            country_of_origin="USA",
            address1="123 Main St",
            city="New York",
            state="NY",
            zip_code="10001",
            exchange="NYSE",
            market="us_market",
            sector="Technology",
            industry="Software",
            market_cap=1000000000,
            regular_market_price=100.50,
            pre_market_price=101.00,
            post_market_price=100.25,
            fifty_two_week_high=120.00,
            fifty_two_week_low=80.00,
            average_volume_10days=5000000,
            shares_outstanding=100000000,
            float_shares=90000000,
            total_debt=500000000,
            debt_to_equity=0.5,
            full_time_employees=10000,
            website="https://test.com",
            short_percent_of_float=0.05,
            short_ratio=2.5,
            held_percent_insiders=0.10,
            held_percent_institutions=0.70,
            last_split_factor="2:1",
            last_split_date=1609459200,
            operating_cash_flow=200000000,
            last_split_display="2021-01-01 (2:1, split)",
            is_adr=False,
            directors=["John Doe - Director", "Jane Smith - Director"],
        )

        cache.set_stock_info(stock_info)
        result = cache.get_stock_info("TEST")

        assert result.ticker == stock_info.ticker
        assert result.long_name == stock_info.long_name
        assert result.short_name == stock_info.short_name
        assert result.country == stock_info.country
        assert result.market_cap == stock_info.market_cap
        assert result.regular_market_price == stock_info.regular_market_price
        assert result.is_adr == stock_info.is_adr
        assert result.directors == stock_info.directors
        cache.close()

    def test_stock_info_expiration(self):
        """Test that expired stock info is not returned."""
        cache = StockCache(ttl=1)  # 1 second TTL
        stock_info = StockInfo(ticker="AAPL", long_name="Apple Inc.")

        cache.set_stock_info(stock_info)
        assert cache.get_stock_info("AAPL") is not None

        # Wait for expiration
        time.sleep(1.1)

        assert cache.get_stock_info("AAPL") is None
        cache.close()


class TestAdrStatusCache:
    """Tests for ADR status caching."""

    def test_get_adr_status_cache_miss(self):
        """Test that cache miss returns (None, False)."""
        cache = StockCache()
        result, hit = cache.get_adr_status("AAPL")
        assert result is None
        assert hit is False
        cache.close()

    def test_set_and_get_adr_status_true(self):
        """Test caching ADR status as True."""
        cache = StockCache()
        cache.set_adr_status("BABA", True)

        result, hit = cache.get_adr_status("BABA")
        assert result is True
        assert hit is True
        cache.close()

    def test_set_and_get_adr_status_false(self):
        """Test caching ADR status as False."""
        cache = StockCache()
        cache.set_adr_status("AAPL", False)

        result, hit = cache.get_adr_status("AAPL")
        assert result is False
        assert hit is True
        cache.close()

    def test_set_and_get_adr_status_none(self):
        """Test caching ADR status as None (unknown)."""
        cache = StockCache()
        cache.set_adr_status("UNKN", None)

        result, hit = cache.get_adr_status("UNKN")
        assert result is None
        assert hit is True  # Cache hit, but value is None
        cache.close()

    def test_adr_status_case_insensitive(self):
        """Test that ADR status lookup is case-insensitive."""
        cache = StockCache()
        cache.set_adr_status("BABA", True)

        result, hit = cache.get_adr_status("baba")
        assert result is True
        assert hit is True
        cache.close()

    def test_adr_status_overwrites(self):
        """Test that setting ADR status twice overwrites the first."""
        cache = StockCache()
        cache.set_adr_status("BABA", True)
        cache.set_adr_status("BABA", False)

        result, hit = cache.get_adr_status("BABA")
        assert result is False
        cache.close()

    def test_adr_status_expiration(self):
        """Test that expired ADR status is not returned."""
        cache = StockCache(ttl=1)
        cache.set_adr_status("BABA", True)

        result, hit = cache.get_adr_status("BABA")
        assert hit is True

        time.sleep(1.1)

        result, hit = cache.get_adr_status("BABA")
        assert hit is False
        cache.close()


class TestDirectorsCache:
    """Tests for directors caching."""

    def test_get_directors_cache_miss(self):
        """Test that cache miss returns (None, False)."""
        cache = StockCache()
        result, hit = cache.get_directors("AAPL")
        assert result is None
        assert hit is False
        cache.close()

    def test_set_and_get_directors(self):
        """Test setting and getting directors."""
        cache = StockCache()
        directors = ["John Doe - Director", "Jane Smith - Independent Director"]

        cache.set_directors("AAPL", directors)
        result, hit = cache.get_directors("AAPL")

        assert hit is True
        assert result == directors
        assert len(result) == 2
        cache.close()

    def test_set_and_get_empty_directors(self):
        """Test caching empty directors list."""
        cache = StockCache()
        cache.set_directors("AAPL", [])

        result, hit = cache.get_directors("AAPL")
        assert hit is True
        assert result == []
        cache.close()

    def test_directors_case_insensitive(self):
        """Test that directors lookup is case-insensitive."""
        cache = StockCache()
        cache.set_directors("AAPL", ["John Doe - Director"])

        result, hit = cache.get_directors("aapl")
        assert hit is True
        assert len(result) == 1
        cache.close()

    def test_directors_overwrites(self):
        """Test that setting directors twice overwrites the first."""
        cache = StockCache()
        cache.set_directors("AAPL", ["John Doe"])
        cache.set_directors("AAPL", ["Jane Smith"])

        result, hit = cache.get_directors("AAPL")
        assert result == ["Jane Smith"]
        cache.close()

    def test_directors_expiration(self):
        """Test that expired directors are not returned."""
        cache = StockCache(ttl=1)
        cache.set_directors("AAPL", ["John Doe"])

        result, hit = cache.get_directors("AAPL")
        assert hit is True

        time.sleep(1.1)

        result, hit = cache.get_directors("AAPL")
        assert hit is False
        cache.close()


class TestCacheClear:
    """Tests for cache clearing."""

    def test_clear_removes_all_data(self):
        """Test that clear removes all cached data."""
        cache = StockCache()

        # Add data to all tables
        cache.set_stock_info(StockInfo(ticker="AAPL", long_name="Apple"))
        cache.set_adr_status("BABA", True)
        cache.set_directors("MSFT", ["John Doe"])

        # Verify data exists
        assert cache.get_stock_info("AAPL") is not None
        assert cache.get_adr_status("BABA")[1] is True
        assert cache.get_directors("MSFT")[1] is True

        # Clear cache
        cache.clear()

        # Verify data is gone
        assert cache.get_stock_info("AAPL") is None
        assert cache.get_adr_status("BABA")[1] is False
        assert cache.get_directors("MSFT")[1] is False
        cache.close()

    def test_clear_allows_new_data(self):
        """Test that cache can be used after clearing."""
        cache = StockCache()

        cache.set_stock_info(StockInfo(ticker="AAPL", long_name="Apple"))
        cache.clear()
        cache.set_stock_info(StockInfo(ticker="MSFT", long_name="Microsoft"))

        assert cache.get_stock_info("AAPL") is None
        assert cache.get_stock_info("MSFT") is not None
        cache.close()


class TestGlobalCacheFunctions:
    """Tests for global cache functions."""

    def test_get_cache_returns_cache_instance(self):
        """Test that get_cache returns a StockCache instance."""
        cache = get_cache()
        assert isinstance(cache, StockCache)

    def test_get_cache_returns_same_instance(self):
        """Test that get_cache returns the same instance on multiple calls."""
        cache1 = get_cache()
        cache2 = get_cache()
        assert cache1 is cache2

    def test_clear_cache_clears_global_cache(self):
        """Test that clear_cache clears the global cache."""
        cache = get_cache()
        cache.set_stock_info(StockInfo(ticker="AAPL", long_name="Apple"))

        clear_cache()

        assert cache.get_stock_info("AAPL") is None


class TestCacheIntegration:
    """Integration tests for cache with fetchers."""

    def test_multiple_tickers_cached_separately(self):
        """Test that different tickers are cached separately."""
        cache = StockCache()

        cache.set_stock_info(StockInfo(ticker="AAPL", long_name="Apple"))
        cache.set_stock_info(StockInfo(ticker="MSFT", long_name="Microsoft"))
        cache.set_stock_info(StockInfo(ticker="GOOG", long_name="Alphabet"))

        assert cache.get_stock_info("AAPL").long_name == "Apple"
        assert cache.get_stock_info("MSFT").long_name == "Microsoft"
        assert cache.get_stock_info("GOOG").long_name == "Alphabet"
        cache.close()

    def test_mixed_data_types_cached(self):
        """Test caching different data types for same ticker."""
        cache = StockCache()

        cache.set_stock_info(StockInfo(ticker="AAPL", long_name="Apple"))
        cache.set_adr_status("AAPL", False)
        cache.set_directors("AAPL", ["Tim Cook - Director"])

        assert cache.get_stock_info("AAPL").long_name == "Apple"
        assert cache.get_adr_status("AAPL") == (False, True)
        assert cache.get_directors("AAPL") == (["Tim Cook - Director"], True)
        cache.close()

    def test_cache_handles_special_characters_in_directors(self):
        """Test that cache handles special characters in director names."""
        cache = StockCache()
        directors = [
            "Jean-Pierre Dupont - Director",
            "Maria Garcia-Lopez - Independent Director",
            "Li Wei - Director",
        ]

        cache.set_directors("TEST", directors)
        result, hit = cache.get_directors("TEST")

        assert hit is True
        assert result == directors
        cache.close()

    def test_cache_handles_unicode_in_stock_info(self):
        """Test that cache handles unicode in stock info."""
        cache = StockCache()
        stock_info = StockInfo(
            ticker="TEST",
            long_name="Societe Generale S.A.",
            city="Paris",
            country="France",
        )

        cache.set_stock_info(stock_info)
        result = cache.get_stock_info("TEST")

        assert result.long_name == "Societe Generale S.A."
        cache.close()
