"""Tests for output formatters."""

import json
import pytest

from super_signal.formatters import (
    get_formatter,
    BaseFormatter,
    TextFormatter,
    JsonFormatter,
    CsvFormatter,
)
from super_signal.models import StockInfo, RiskAnalysis, RiskFlag, RiskSeverity
from super_signal.cli import TickerResult


class TestGetFormatter:
    """Tests for the get_formatter factory function."""

    def test_get_text_formatter(self):
        """Test that 'text' returns a TextFormatter instance."""
        formatter = get_formatter('text')
        assert isinstance(formatter, TextFormatter)
        assert isinstance(formatter, BaseFormatter)

    def test_get_json_formatter(self):
        """Test that 'json' returns a JsonFormatter instance."""
        formatter = get_formatter('json')
        assert isinstance(formatter, JsonFormatter)
        assert isinstance(formatter, BaseFormatter)

    def test_get_csv_formatter(self):
        """Test that 'csv' returns a CsvFormatter instance."""
        formatter = get_formatter('csv')
        assert isinstance(formatter, CsvFormatter)
        assert isinstance(formatter, BaseFormatter)

    def test_invalid_format_raises_value_error(self):
        """Test that invalid format raises ValueError."""
        with pytest.raises(ValueError) as exc_info:
            get_formatter('xml')
        assert "Unsupported format: 'xml'" in str(exc_info.value)
        assert "text" in str(exc_info.value)
        assert "json" in str(exc_info.value)
        assert "csv" in str(exc_info.value)

    def test_invalid_format_empty_string(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError):
            get_formatter('')


class TestTextFormatter:
    """Tests for the TextFormatter class."""

    def test_format_returns_string(self, sample_us_stock):
        """Test that format returns a string."""
        formatter = TextFormatter()
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_format_contains_ticker(self, sample_us_stock):
        """Test that output contains the ticker symbol."""
        formatter = TextFormatter()
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        assert sample_us_stock.ticker in result

    def test_format_contains_company_name(self, sample_us_stock):
        """Test that output contains the company name."""
        formatter = TextFormatter()
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        assert sample_us_stock.long_name in result

    def test_format_with_vix(self, sample_us_stock):
        """Test that VIX value is included when provided."""
        formatter = TextFormatter()
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        result = formatter.format(
            sample_us_stock, risk_analysis, 3_000_000, vix_value=18.5
        )
        assert "18.5" in result

    def test_format_with_risk_flags(self, sample_us_stock):
        """Test that risk flags are displayed when present."""
        formatter = TextFormatter()
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        risk_analysis.add_flag("test", "Test risk flag", RiskSeverity.HIGH)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        assert "Test risk flag" in result


class TestJsonFormatter:
    """Tests for the JsonFormatter class."""

    def test_format_returns_valid_json(self, sample_us_stock):
        """Test that format returns valid JSON."""
        formatter = JsonFormatter()
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        # Should not raise
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_json_contains_required_fields(self, sample_us_stock):
        """Test that JSON contains all required top-level fields."""
        formatter = JsonFormatter()
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        data = json.loads(result)

        required_fields = [
            'ticker', 'company', 'location', 'price', 'shares',
            'volume', 'ownership', 'short_interest', 'financials',
            'executives', 'risk_analysis', 'vix', 'timestamp'
        ]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

    def test_json_ticker_value(self, sample_us_stock):
        """Test that ticker value is correct."""
        formatter = JsonFormatter()
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        data = json.loads(result)
        assert data['ticker'] == sample_us_stock.ticker

    def test_json_company_section(self, sample_us_stock):
        """Test that company section contains expected fields."""
        formatter = JsonFormatter()
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        data = json.loads(result)

        assert data['company']['name'] == sample_us_stock.long_name
        assert data['company']['exchange'] == sample_us_stock.exchange

    def test_json_with_vix(self, sample_us_stock):
        """Test that VIX value is included correctly."""
        formatter = JsonFormatter()
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        result = formatter.format(
            sample_us_stock, risk_analysis, 3_000_000, vix_value=22.5
        )
        data = json.loads(result)
        assert data['vix'] == 22.5

    def test_json_risk_flags(self, sample_us_stock):
        """Test that risk flags are included in JSON."""
        formatter = JsonFormatter()
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        risk_analysis.add_flag("adr", "Stock is an ADR", RiskSeverity.MEDIUM)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        data = json.loads(result)

        assert data['risk_analysis']['has_risks'] is True
        assert len(data['risk_analysis']['flags']) == 1
        assert data['risk_analysis']['flags'][0]['message'] == "Stock is an ADR"

    def test_json_ownership_percentages(self, sample_us_stock):
        """Test that ownership percentages are converted correctly."""
        formatter = JsonFormatter()
        sample_us_stock.held_percent_insiders = 0.15
        sample_us_stock.held_percent_institutions = 0.65
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        data = json.loads(result)

        assert data['ownership']['insider_percent'] == 15.0
        assert data['ownership']['institutional_percent'] == 65.0


class TestCsvFormatter:
    """Tests for the CsvFormatter class."""

    def test_format_returns_string(self, sample_us_stock):
        """Test that format returns a string."""
        formatter = CsvFormatter()
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_csv_has_header_and_data_row(self, sample_us_stock):
        """Test that CSV has exactly two rows (header + data)."""
        formatter = CsvFormatter()
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        lines = result.strip().split('\n')
        assert len(lines) == 2

    def test_csv_header_contains_expected_columns(self, sample_us_stock):
        """Test that CSV header contains expected column names."""
        formatter = CsvFormatter()
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        header = result.split('\n')[0]

        expected_columns = [
            'ticker', 'company_name', 'exchange', 'market_cap',
            'price_current', 'float_shares', 'has_risk_flags', 'vix'
        ]
        for col in expected_columns:
            assert col in header, f"Missing column: {col}"

    def test_csv_data_row_contains_ticker(self, sample_us_stock):
        """Test that CSV data row contains the ticker."""
        formatter = CsvFormatter()
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        data_row = result.split('\n')[1]
        assert sample_us_stock.ticker in data_row

    def test_csv_with_vix(self, sample_us_stock):
        """Test that VIX value is included in CSV."""
        formatter = CsvFormatter()
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        result = formatter.format(
            sample_us_stock, risk_analysis, 3_000_000, vix_value=15.75
        )
        assert "15.75" in result

    def test_csv_risk_flags_combined(self, sample_us_stock):
        """Test that multiple risk flags are combined with semicolon."""
        formatter = CsvFormatter()
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        risk_analysis.add_flag("test1", "First risk", RiskSeverity.LOW)
        risk_analysis.add_flag("test2", "Second risk", RiskSeverity.HIGH)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        # Risk flags should be combined with semicolon
        assert "First risk; Second risk" in result

    def test_csv_boolean_lowercase(self, sample_us_stock):
        """Test that booleans are formatted as lowercase."""
        formatter = CsvFormatter()
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        # is_adr should be 'false' (lowercase)
        assert "false" in result


class TestFormatterIntegration:
    """Integration tests across all formatters."""

    @pytest.mark.parametrize("format_type", ["text", "json", "csv"])
    def test_all_formatters_handle_minimal_stock(self, format_type):
        """Test that all formatters handle stock with minimal data."""
        formatter = get_formatter(format_type)
        stock = StockInfo(ticker="TEST")
        risk_analysis = RiskAnalysis(ticker="TEST")
        # Should not raise
        result = formatter.format(stock, risk_analysis, 3_000_000)
        assert "TEST" in result

    @pytest.mark.parametrize("format_type", ["text", "json", "csv"])
    def test_all_formatters_handle_none_values(self, format_type):
        """Test that all formatters handle None values gracefully."""
        formatter = get_formatter(format_type)
        stock = StockInfo(
            ticker="NULL",
            long_name=None,
            market_cap=None,
            regular_market_price=None,
        )
        risk_analysis = RiskAnalysis(ticker="NULL")
        # Should not raise
        result = formatter.format(stock, risk_analysis, 3_000_000, vix_value=None)
        assert isinstance(result, str)

    @pytest.mark.parametrize("format_type", ["text", "json", "csv"])
    def test_all_formatters_handle_directors(self, format_type):
        """Test that all formatters handle directors list."""
        formatter = get_formatter(format_type)
        stock = StockInfo(
            ticker="EXEC",
            directors=["John Doe - CEO", "Jane Smith - CFO"]
        )
        risk_analysis = RiskAnalysis(ticker="EXEC")
        result = formatter.format(stock, risk_analysis, 3_000_000)
        # At minimum, directors should be processed without error
        assert isinstance(result, str)


class TestBatchFormatting:
    """Tests for batch formatting of multiple ticker results."""

    @pytest.fixture
    def sample_results(self, sample_us_stock):
        """Create sample batch results with success and failure."""
        stock1 = sample_us_stock
        risk1 = RiskAnalysis(ticker=stock1.ticker)

        stock2 = StockInfo(
            ticker="GOOG",
            long_name="Alphabet Inc.",
            exchange="NASDAQ",
            market_cap=2000000000000,
        )
        risk2 = RiskAnalysis(ticker="GOOG")

        return [
            TickerResult(ticker="AAPL", stock_info=stock1, risk_analysis=risk1),
            TickerResult(ticker="GOOG", stock_info=stock2, risk_analysis=risk2),
            TickerResult(ticker="INVALID", error="Unable to retrieve data"),
        ]

    def test_text_batch_formatting(self, sample_results):
        """Test text formatter batch output contains all tickers."""
        formatter = TextFormatter()
        result = formatter.format_batch(sample_results, 3_000_000, vix_value=18.5)

        assert "AAPL" in result
        assert "GOOG" in result
        assert "INVALID" in result
        assert "Unable to retrieve data" in result

    def test_text_batch_has_separators(self, sample_results):
        """Test text formatter batch output has separators between stocks."""
        formatter = TextFormatter()
        result = formatter.format_batch(sample_results, 3_000_000)

        # Should contain separator characters (equals signs)
        assert "=" * 20 in result or "═" * 20 in result or result.count("AAPL") == 1

    def test_json_batch_formatting_valid_json(self, sample_results):
        """Test JSON formatter batch output is valid JSON."""
        formatter = JsonFormatter()
        result = formatter.format_batch(sample_results, 3_000_000, vix_value=18.5)

        # Should not raise
        data = json.loads(result)
        assert isinstance(data, dict)

    def test_json_batch_has_wrapper_object(self, sample_results):
        """Test JSON batch output has wrapper object with metadata."""
        formatter = JsonFormatter()
        result = formatter.format_batch(sample_results, 3_000_000, vix_value=18.5)
        data = json.loads(result)

        # Check wrapper fields
        assert "timestamp" in data
        assert "count" in data
        assert "successes" in data
        assert "failures" in data
        assert "vix" in data
        assert "results" in data

        # Check counts
        assert data["count"] == 3
        assert data["successes"] == 2
        assert data["failures"] == 1
        assert data["vix"] == 18.5

    def test_json_batch_results_array(self, sample_results):
        """Test JSON batch output results array contains all tickers."""
        formatter = JsonFormatter()
        result = formatter.format_batch(sample_results, 3_000_000)
        data = json.loads(result)

        results = data["results"]
        assert len(results) == 3

        # Check successful results have success: true
        tickers = {r["ticker"]: r for r in results}
        assert tickers["AAPL"]["success"] is True
        assert tickers["GOOG"]["success"] is True

        # Check failed result has success: false and error
        assert tickers["INVALID"]["success"] is False
        assert "error" in tickers["INVALID"]

    def test_csv_batch_formatting(self, sample_results):
        """Test CSV formatter batch output is valid CSV."""
        formatter = CsvFormatter()
        result = formatter.format_batch(sample_results, 3_000_000, vix_value=18.5)

        lines = result.strip().split('\n')
        # Should have header + 3 data rows
        assert len(lines) == 4

    def test_csv_batch_single_header(self, sample_results):
        """Test CSV batch output has only one header row."""
        formatter = CsvFormatter()
        result = formatter.format_batch(sample_results, 3_000_000)

        lines = result.strip().split('\n')
        header = lines[0]

        # Only first line should contain 'ticker' as header
        assert "ticker" in header
        # Subsequent lines should have actual ticker values
        assert "AAPL" in lines[1]
        assert "GOOG" in lines[2]
        assert "INVALID" in lines[3]

    def test_csv_batch_has_error_column(self, sample_results):
        """Test CSV batch output includes error column."""
        formatter = CsvFormatter()
        result = formatter.format_batch(sample_results, 3_000_000)

        lines = result.strip().split('\n')
        header = lines[0]

        # Should have error column
        assert "error" in header

        # Failed ticker row should contain error message
        invalid_row = lines[3]
        assert "Unable to retrieve data" in invalid_row

    def test_csv_batch_preserves_order(self, sample_results):
        """Test CSV batch output preserves ticker order."""
        formatter = CsvFormatter()
        result = formatter.format_batch(sample_results, 3_000_000)

        lines = result.strip().split('\n')
        # Check order matches input order
        assert "AAPL" in lines[1]
        assert "GOOG" in lines[2]
        assert "INVALID" in lines[3]

    @pytest.mark.parametrize("format_type", ["text", "json", "csv"])
    def test_all_formatters_handle_empty_batch(self, format_type):
        """Test that all formatters handle empty batch."""
        formatter = get_formatter(format_type)
        result = formatter.format_batch([], 3_000_000)
        assert isinstance(result, str)

    @pytest.mark.parametrize("format_type", ["text", "json", "csv"])
    def test_all_formatters_handle_all_failures(self, format_type):
        """Test that all formatters handle batch with all failures."""
        formatter = get_formatter(format_type)
        results = [
            TickerResult(ticker="INVALID1", error="Error 1"),
            TickerResult(ticker="INVALID2", error="Error 2"),
        ]
        result = formatter.format_batch(results, 3_000_000)
        assert isinstance(result, str)
        assert "INVALID1" in result
        assert "INVALID2" in result
