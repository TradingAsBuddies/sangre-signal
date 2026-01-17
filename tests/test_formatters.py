"""Tests for output formatters."""

import json
import pytest
from unittest.mock import patch, MagicMock

from super_signal.formatters import (
    get_formatter,
    BaseFormatter,
    TextFormatter,
    JsonFormatter,
    CsvFormatter,
    ClaudeFormatter,
)
from super_signal.formatters.claude_formatter import (
    _strip_emojis,
    _safe_encode_for_console,
    _format_number,
    _format_percent,
    SYSTEM_PROMPTS,
    ANALYSIS_PROMPTS,
    BATCH_PROMPTS,
)
from super_signal.config import ClaudeConfig
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

    def test_get_claude_formatter(self):
        """Test that 'claude' returns a ClaudeFormatter instance."""
        formatter = get_formatter('claude')
        assert isinstance(formatter, ClaudeFormatter)
        assert isinstance(formatter, BaseFormatter)

    def test_get_claude_formatter_with_english(self):
        """Test that 'claude' with language='en' returns English formatter."""
        formatter = get_formatter('claude', language='en')
        assert isinstance(formatter, ClaudeFormatter)
        assert formatter.language == 'en'

    def test_get_claude_formatter_with_spanish(self):
        """Test that 'claude' with language='es' returns Spanish formatter."""
        formatter = get_formatter('claude', language='es')
        assert isinstance(formatter, ClaudeFormatter)
        assert formatter.language == 'es'


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


# ============================================================================
# Claude Formatter Tests
# ============================================================================

class TestStripEmojis:
    """Tests for the _strip_emojis helper function."""

    def test_removes_emoticons(self):
        """Test that emoticons are removed."""
        text = "Hello 😀 World 😃"
        result = _strip_emojis(text)
        assert result == "Hello  World "

    def test_removes_symbols(self):
        """Test that symbol emojis are removed."""
        text = "Check ✅ this ❌ out"
        result = _strip_emojis(text)
        assert "✅" not in result
        assert "❌" not in result

    def test_preserves_regular_text(self):
        """Test that regular text is preserved."""
        text = "This is normal text with numbers 123 and symbols !@#"
        result = _strip_emojis(text)
        assert result == text

    def test_preserves_spanish_characters(self):
        """Test that Spanish accented characters are preserved."""
        text = "Análisis de riesgo en español con ñ"
        result = _strip_emojis(text)
        assert result == text

    def test_empty_string(self):
        """Test with empty string."""
        assert _strip_emojis("") == ""


class TestSafeEncodeForConsole:
    """Tests for the _safe_encode_for_console helper function."""

    def test_transliterates_spanish_accents(self):
        """Test that Spanish accents are transliterated on Windows."""
        text = "Análisis de inversión"
        with patch('super_signal.formatters.claude_formatter.sys') as mock_sys:
            mock_sys.platform = 'win32'
            mock_sys.stdout.encoding = 'cp1252'
            result = _safe_encode_for_console(text)
            assert 'a' in result.lower()  # á -> a
            assert 'o' in result.lower()  # ó -> o

    def test_transliterates_n_tilde(self):
        """Test that ñ is transliterated to n on Windows."""
        text = "España"
        with patch('super_signal.formatters.claude_formatter.sys') as mock_sys:
            mock_sys.platform = 'win32'
            mock_sys.stdout.encoding = 'cp1252'
            result = _safe_encode_for_console(text)
            assert "Espana" == result

    def test_transliterates_inverted_punctuation(self):
        """Test that inverted punctuation is transliterated."""
        text = "¿Cómo estás? ¡Hola!"
        with patch('super_signal.formatters.claude_formatter.sys') as mock_sys:
            mock_sys.platform = 'win32'
            mock_sys.stdout.encoding = 'cp1252'
            result = _safe_encode_for_console(text)
            assert "?" in result
            assert "!" in result
            assert "¿" not in result
            assert "¡" not in result

    def test_transliterates_bullet_points(self):
        """Test that bullet points are transliterated to dashes."""
        text = "• Item one • Item two"
        with patch('super_signal.formatters.claude_formatter.sys') as mock_sys:
            mock_sys.platform = 'win32'
            mock_sys.stdout.encoding = 'cp1252'
            result = _safe_encode_for_console(text)
            assert "- Item one - Item two" == result

    def test_preserves_text_on_utf8(self):
        """Test that text is preserved on UTF-8 systems."""
        text = "Análisis de inversión con ñ"
        with patch('super_signal.formatters.claude_formatter.sys') as mock_sys:
            mock_sys.platform = 'linux'
            mock_sys.stdout.encoding = 'utf-8'
            result = _safe_encode_for_console(text)
            assert result == text

    def test_preserves_text_on_non_windows(self):
        """Test that text is preserved on non-Windows systems."""
        text = "Análisis español"
        with patch('super_signal.formatters.claude_formatter.sys') as mock_sys:
            mock_sys.platform = 'darwin'
            mock_sys.stdout.encoding = 'utf-8'
            result = _safe_encode_for_console(text)
            assert result == text


class TestFormatNumber:
    """Tests for the _format_number helper function."""

    def test_format_trillions(self):
        """Test formatting of trillion values."""
        assert _format_number(1_500_000_000_000) == "$1.50T"
        assert _format_number(3_780_000_000_000) == "$3.78T"

    def test_format_billions(self):
        """Test formatting of billion values."""
        assert _format_number(1_500_000_000) == "$1.50B"
        assert _format_number(112_380_000_000) == "$112.38B"

    def test_format_millions(self):
        """Test formatting of million values."""
        assert _format_number(1_500_000) == "$1.50M"
        assert _format_number(47_910_000) == "$47.91M"

    def test_format_thousands(self):
        """Test formatting of thousand values."""
        assert _format_number(1_500) == "$1.50K"
        assert _format_number(15_000) == "$15.00K"

    def test_format_small_values(self):
        """Test formatting of small values."""
        assert _format_number(100) == "$100.00"
        assert _format_number(25.50) == "$25.50"

    def test_format_none(self):
        """Test formatting of None value."""
        assert _format_number(None) == "N/A"

    def test_format_with_custom_prefix(self):
        """Test formatting with custom prefix."""
        assert _format_number(1_000_000, prefix="") == "1.00M"
        assert _format_number(1_000_000, prefix="EUR ") == "EUR 1.00M"

    def test_format_negative_values(self):
        """Test formatting of negative values."""
        assert _format_number(-1_500_000_000) == "$-1.50B"


class TestFormatPercent:
    """Tests for the _format_percent helper function."""

    def test_format_percentage(self):
        """Test basic percentage formatting."""
        assert _format_percent(15.5) == "15.50%"
        assert _format_percent(0.01) == "0.01%"

    def test_format_none(self):
        """Test formatting of None value."""
        assert _format_percent(None) == "N/A"

    def test_format_zero(self):
        """Test formatting of zero."""
        assert _format_percent(0) == "0.00%"

    def test_format_negative(self):
        """Test formatting of negative percentage."""
        assert _format_percent(-11.46) == "-11.46%"


class TestClaudeFormatterInit:
    """Tests for ClaudeFormatter initialization."""

    def test_default_initialization(self):
        """Test default initialization uses global config."""
        formatter = ClaudeFormatter()
        assert formatter.language == "en"  # Default language
        assert formatter._client is None

    def test_custom_language(self):
        """Test initialization with custom language."""
        formatter = ClaudeFormatter(language="es")
        assert formatter.language == "es"

    def test_custom_config(self):
        """Test initialization with custom config."""
        config = ClaudeConfig(api_key="test-key", model="test-model")
        formatter = ClaudeFormatter(config=config)
        assert formatter.config.api_key == "test-key"
        assert formatter.config.model == "test-model"


class TestClaudeFormatterPrompts:
    """Tests for Claude formatter prompts."""

    def test_system_prompts_exist(self):
        """Test that system prompts exist for both languages."""
        assert "en" in SYSTEM_PROMPTS
        assert "es" in SYSTEM_PROMPTS

    def test_analysis_prompts_exist(self):
        """Test that analysis prompts exist for both languages."""
        assert "en" in ANALYSIS_PROMPTS
        assert "es" in ANALYSIS_PROMPTS

    def test_batch_prompts_exist(self):
        """Test that batch prompts exist for both languages."""
        assert "en" in BATCH_PROMPTS
        assert "es" in BATCH_PROMPTS

    def test_english_prompt_contains_placeholders(self):
        """Test that English prompt has required placeholders."""
        prompt = ANALYSIS_PROMPTS["en"]
        assert "{ticker}" in prompt
        assert "{company_name}" in prompt
        assert "{risk_flags}" in prompt

    def test_spanish_prompt_contains_placeholders(self):
        """Test that Spanish prompt has required placeholders."""
        prompt = ANALYSIS_PROMPTS["es"]
        assert "{ticker}" in prompt
        assert "{company_name}" in prompt
        assert "{risk_flags}" in prompt

    def test_spanish_prompt_mentions_oaxaca(self):
        """Test that Spanish prompt mentions Mexican Spanish from Oaxaca."""
        prompt = ANALYSIS_PROMPTS["es"]
        assert "Oaxaca" in prompt or "mexicano" in prompt.lower()


class TestClaudeFormatterRiskFlags:
    """Tests for Claude formatter risk flags text generation."""

    def test_build_risk_flags_text_no_risks_english(self):
        """Test risk flags text with no risks in English."""
        formatter = ClaudeFormatter(language="en")
        risk_analysis = RiskAnalysis(ticker="TEST")
        result = formatter._build_risk_flags_text(risk_analysis)
        assert "No significant risk flags" in result

    def test_build_risk_flags_text_no_risks_spanish(self):
        """Test risk flags text with no risks in Spanish."""
        formatter = ClaudeFormatter(language="es")
        risk_analysis = RiskAnalysis(ticker="TEST")
        result = formatter._build_risk_flags_text(risk_analysis)
        assert "No se detectaron" in result

    def test_build_risk_flags_text_with_flags(self):
        """Test risk flags text with actual flags."""
        formatter = ClaudeFormatter(language="en")
        risk_analysis = RiskAnalysis(ticker="TEST")
        risk_analysis.add_flag("adr", "Stock is an ADR", RiskSeverity.MEDIUM)
        risk_analysis.add_flag("country", "Non-US country", RiskSeverity.HIGH)
        result = formatter._build_risk_flags_text(risk_analysis)
        assert "Stock is an ADR" in result
        assert "Non-US country" in result
        assert "[MEDIUM]" in result
        assert "[HIGH]" in result


class TestClaudeFormatterFallback:
    """Tests for Claude formatter fallback when API unavailable."""

    def test_fallback_when_no_api_key(self, sample_us_stock):
        """Test fallback formatting when API key not configured."""
        config = ClaudeConfig(api_key="")  # Empty API key
        formatter = ClaudeFormatter(config=config)
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        assert "AI analysis unavailable" in result or "ANTHROPIC_API_KEY not set" in result
        assert sample_us_stock.ticker in result

    def test_fallback_english(self, sample_us_stock):
        """Test fallback formatting in English."""
        config = ClaudeConfig(api_key="")
        formatter = ClaudeFormatter(language="en", config=config)
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        assert "ANALYSIS" in result
        assert "Company:" in result

    def test_fallback_spanish(self, sample_us_stock):
        """Test fallback formatting in Spanish."""
        config = ClaudeConfig(api_key="")
        formatter = ClaudeFormatter(language="es", config=config)
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        assert "ANALISIS" in result
        assert "Empresa:" in result


class TestClaudeFormatterError:
    """Tests for Claude formatter error handling."""

    def test_format_error_english(self):
        """Test error formatting in English."""
        formatter = ClaudeFormatter(language="en")
        result = formatter.format_error("INVALID", "Connection timeout")
        assert "Error for INVALID" in result
        assert "Connection timeout" in result

    def test_format_error_spanish(self):
        """Test error formatting in Spanish."""
        formatter = ClaudeFormatter(language="es")
        result = formatter.format_error("INVALID", "Connection timeout")
        assert "Error para INVALID" in result
        assert "Connection timeout" in result

    def test_format_error_none_message_english(self):
        """Test error formatting with None message in English."""
        formatter = ClaudeFormatter(language="en")
        result = formatter.format_error("INVALID", None)
        assert "Unknown error" in result

    def test_format_error_none_message_spanish(self):
        """Test error formatting with None message in Spanish."""
        formatter = ClaudeFormatter(language="es")
        result = formatter.format_error("INVALID", None)
        assert "Error desconocido" in result


class TestClaudeFormatterWithMock:
    """Tests for Claude formatter with mocked API calls."""

    @pytest.fixture
    def mock_claude_response(self):
        """Create a mock Claude API response."""
        mock_message = MagicMock()
        mock_message.content = [MagicMock(text="This is a test analysis response.")]
        return mock_message

    def test_format_calls_api_when_configured(self, sample_us_stock, mock_claude_response):
        """Test that format calls Claude API when configured."""
        config = ClaudeConfig(api_key="test-key")
        formatter = ClaudeFormatter(config=config)
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)

        with patch.object(formatter, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_claude_response
            mock_get_client.return_value = mock_client

            result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)

            mock_client.messages.create.assert_called_once()
            assert "test analysis response" in result

    def test_format_includes_header_english(self, sample_us_stock, mock_claude_response):
        """Test that English format includes proper header."""
        config = ClaudeConfig(api_key="test-key")
        formatter = ClaudeFormatter(language="en", config=config)
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)

        with patch.object(formatter, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_claude_response
            mock_get_client.return_value = mock_client

            result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)

            assert "AAPL ANALYSIS" in result
            assert "Powered by Claude AI" in result

    def test_format_includes_header_spanish(self, sample_us_stock, mock_claude_response):
        """Test that Spanish format includes proper header."""
        config = ClaudeConfig(api_key="test-key")
        formatter = ClaudeFormatter(language="es", config=config)
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)

        with patch.object(formatter, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_claude_response
            mock_get_client.return_value = mock_client

            result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)

            assert "ANALISIS DE AAPL" in result
            assert "Potenciado por Claude AI" in result

    def test_format_includes_timestamp(self, sample_us_stock, mock_claude_response):
        """Test that format includes timestamp."""
        config = ClaudeConfig(api_key="test-key")
        formatter = ClaudeFormatter(config=config)
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)

        with patch.object(formatter, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.messages.create.return_value = mock_claude_response
            mock_get_client.return_value = mock_client

            result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)

            assert "Generated:" in result or "Generado:" in result

    def test_format_handles_api_error(self, sample_us_stock):
        """Test that format handles API errors gracefully."""
        config = ClaudeConfig(api_key="test-key")
        formatter = ClaudeFormatter(config=config)
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)

        with patch.object(formatter, '_get_client') as mock_get_client:
            mock_client = MagicMock()
            mock_client.messages.create.side_effect = Exception("API Error")
            mock_get_client.return_value = mock_client

            result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)

            # Should fall back gracefully
            assert sample_us_stock.ticker in result
            assert "API Error" in result


class TestClaudeFormatterBatch:
    """Tests for Claude formatter batch processing."""

    @pytest.fixture
    def sample_batch_results(self, sample_us_stock):
        """Create sample batch results."""
        stock1 = sample_us_stock
        risk1 = RiskAnalysis(ticker=stock1.ticker)

        stock2 = StockInfo(
            ticker="MSFT",
            long_name="Microsoft Corporation",
            exchange="NASDAQ",
            market_cap=3000000000000,
        )
        risk2 = RiskAnalysis(ticker="MSFT")

        return [
            TickerResult(ticker="AAPL", stock_info=stock1, risk_analysis=risk1),
            TickerResult(ticker="MSFT", stock_info=stock2, risk_analysis=risk2),
            TickerResult(ticker="INVALID", error="Unable to fetch data"),
        ]

    def test_batch_format_without_api_key(self, sample_batch_results):
        """Test batch formatting without API key uses fallback."""
        config = ClaudeConfig(api_key="")
        formatter = ClaudeFormatter(config=config)
        result = formatter.format_batch(sample_batch_results, 3_000_000)

        assert "AAPL" in result
        assert "MSFT" in result
        assert "INVALID" in result
        assert "Unable to fetch data" in result

    def test_batch_format_includes_errors(self, sample_batch_results):
        """Test that batch format includes error results."""
        config = ClaudeConfig(api_key="")
        formatter = ClaudeFormatter(config=config)
        result = formatter.format_batch(sample_batch_results, 3_000_000)

        assert "INVALID" in result
        assert "Unable to fetch data" in result

    def test_batch_format_empty_list(self):
        """Test batch formatting with empty list."""
        config = ClaudeConfig(api_key="")
        formatter = ClaudeFormatter(config=config)
        result = formatter.format_batch([], 3_000_000)
        assert isinstance(result, str)


class TestClaudeFormatterIntegration:
    """Integration tests for Claude formatter."""

    @pytest.mark.parametrize("language", ["en", "es"])
    def test_formatter_handles_minimal_stock(self, language):
        """Test that formatter handles stock with minimal data."""
        config = ClaudeConfig(api_key="")  # Use fallback
        formatter = ClaudeFormatter(language=language, config=config)
        stock = StockInfo(ticker="TEST")
        risk_analysis = RiskAnalysis(ticker="TEST")
        result = formatter.format(stock, risk_analysis, 3_000_000)
        assert "TEST" in result
        assert isinstance(result, str)

    @pytest.mark.parametrize("language", ["en", "es"])
    def test_formatter_handles_none_values(self, language):
        """Test that formatter handles None values gracefully."""
        config = ClaudeConfig(api_key="")
        formatter = ClaudeFormatter(language=language, config=config)
        stock = StockInfo(
            ticker="NULL",
            long_name=None,
            market_cap=None,
            regular_market_price=None,
        )
        risk_analysis = RiskAnalysis(ticker="NULL")
        result = formatter.format(stock, risk_analysis, 3_000_000, vix_value=None)
        assert isinstance(result, str)

    @pytest.mark.parametrize("language", ["en", "es"])
    def test_formatter_handles_risk_flags(self, language, sample_us_stock):
        """Test that formatter handles risk flags."""
        config = ClaudeConfig(api_key="")
        formatter = ClaudeFormatter(language=language, config=config)
        risk_analysis = RiskAnalysis(ticker=sample_us_stock.ticker)
        risk_analysis.add_flag("test", "Test risk flag", RiskSeverity.HIGH)
        result = formatter.format(sample_us_stock, risk_analysis, 3_000_000)
        assert "Test risk flag" in result
