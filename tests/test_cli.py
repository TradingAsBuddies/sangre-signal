"""Tests for CLI functions."""

import pytest

from super_signal.cli import normalize_tickers, TickerResult
from super_signal.models import StockInfo, RiskAnalysis


class TestNormalizeTickers:
    """Tests for the normalize_tickers function."""

    def test_single_ticker(self):
        """Test with a single ticker."""
        result = normalize_tickers(["AAPL"])
        assert result == ["AAPL"]

    def test_multiple_tickers_separate_args(self):
        """Test with multiple tickers as separate arguments."""
        result = normalize_tickers(["AAPL", "GOOG", "MSFT"])
        assert result == ["AAPL", "GOOG", "MSFT"]

    def test_comma_separated_tickers(self):
        """Test with comma-separated tickers in a single argument."""
        result = normalize_tickers(["AAPL,GOOG,MSFT"])
        assert result == ["AAPL", "GOOG", "MSFT"]

    def test_mixed_format(self):
        """Test with mixed format (comma-separated and separate args)."""
        result = normalize_tickers(["AAPL,GOOG", "MSFT"])
        assert result == ["AAPL", "GOOG", "MSFT"]

    def test_uppercase_conversion(self):
        """Test that lowercase tickers are converted to uppercase."""
        result = normalize_tickers(["aapl", "goog"])
        assert result == ["AAPL", "GOOG"]

    def test_deduplication(self):
        """Test that duplicate tickers are removed."""
        result = normalize_tickers(["AAPL", "GOOG", "AAPL"])
        assert result == ["AAPL", "GOOG"]

    def test_deduplication_comma_separated(self):
        """Test that duplicate tickers in comma-separated format are removed."""
        result = normalize_tickers(["AAPL,GOOG,AAPL"])
        assert result == ["AAPL", "GOOG"]

    def test_deduplication_across_args(self):
        """Test that duplicate tickers across arguments are removed."""
        result = normalize_tickers(["AAPL,GOOG", "GOOG,MSFT"])
        assert result == ["AAPL", "GOOG", "MSFT"]

    def test_preserves_order(self):
        """Test that first occurrence order is preserved."""
        result = normalize_tickers(["MSFT", "AAPL", "GOOG"])
        assert result == ["MSFT", "AAPL", "GOOG"]

    def test_whitespace_handling(self):
        """Test that whitespace is stripped."""
        result = normalize_tickers(["  AAPL  ", " GOOG , MSFT "])
        assert result == ["AAPL", "GOOG", "MSFT"]

    def test_empty_string_filtered(self):
        """Test that empty strings are filtered out."""
        result = normalize_tickers(["AAPL", "", "GOOG"])
        assert result == ["AAPL", "GOOG"]

    def test_empty_after_comma_filtered(self):
        """Test that empty parts after comma split are filtered."""
        result = normalize_tickers(["AAPL,,GOOG", "MSFT,"])
        assert result == ["AAPL", "GOOG", "MSFT"]

    def test_empty_list(self):
        """Test with empty input list."""
        result = normalize_tickers([])
        assert result == []


class TestTickerResult:
    """Tests for the TickerResult dataclass."""

    def test_success_property_true(self):
        """Test success property returns True when stock_info is present."""
        stock_info = StockInfo(ticker="AAPL")
        risk_analysis = RiskAnalysis(ticker="AAPL")
        result = TickerResult(
            ticker="AAPL",
            stock_info=stock_info,
            risk_analysis=risk_analysis
        )
        assert result.success is True

    def test_success_property_false(self):
        """Test success property returns False when stock_info is None."""
        result = TickerResult(ticker="INVALID", error="Unable to retrieve data")
        assert result.success is False

    def test_success_property_false_with_none(self):
        """Test success property returns False when all optional fields are None."""
        result = TickerResult(ticker="EMPTY")
        assert result.success is False

    def test_error_field(self):
        """Test error field stores error message."""
        error_msg = "Unable to retrieve data"
        result = TickerResult(ticker="INVALID", error=error_msg)
        assert result.error == error_msg
        assert result.success is False
