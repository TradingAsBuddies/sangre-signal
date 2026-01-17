"""Tests for Yahoo Finance fetcher module."""

import pytest
from unittest.mock import Mock, MagicMock, patch
import pandas as pd
from sangre_signal.fetchers.yahoo_finance import (
    fetch_stock_info,
    is_adr_yahoo,
    get_operating_cash_flow,
    interpret_split_factor,
    get_last_split_details,
)
from sangre_signal.models import StockInfo


class TestFetchStockInfo:
    """Tests for fetch_stock_info function."""

    @patch('sangre_signal.fetchers.yahoo_finance.yf.Ticker')
    def test_fetch_stock_info_success(self, mock_ticker_class):
        """Test successful stock info fetch."""
        # Setup mock
        mock_ticker = Mock()
        mock_ticker.info = {
            'longName': 'Apple Inc.',
            'shortName': 'Apple',
            'country': 'United States',
            'exchange': 'NASDAQ',
            'marketCap': 3000000000000,
            'regularMarketPrice': 180.50,
            'floatShares': 16000000000,
        }
        mock_ticker.cashflow = None
        mock_ticker.splits = pd.Series()
        mock_ticker_class.return_value = mock_ticker

        # Execute
        result = fetch_stock_info('AAPL')

        # Verify
        assert result is not None
        assert result.ticker == 'AAPL'
        assert result.long_name == 'Apple Inc.'
        assert result.country == 'United States'
        assert result.regular_market_price == 180.50

    @patch('sangre_signal.fetchers.yahoo_finance.yf.Ticker')
    def test_fetch_stock_info_no_data(self, mock_ticker_class):
        """Test fetch when no data is returned."""
        mock_ticker = Mock()
        mock_ticker.info = {}
        mock_ticker_class.return_value = mock_ticker

        result = fetch_stock_info('INVALID')

        assert result is None

    @patch('sangre_signal.fetchers.yahoo_finance.yf.Ticker')
    def test_fetch_stock_info_exception(self, mock_ticker_class):
        """Test fetch handles exceptions gracefully."""
        mock_ticker_class.side_effect = Exception("Network error")

        result = fetch_stock_info('AAPL')

        assert result is None

    @patch('sangre_signal.fetchers.yahoo_finance.yf.Ticker')
    def test_fetch_stock_info_uses_price_fallback(self, mock_ticker_class):
        """Test that fetch uses 'price' field as fallback for regularMarketPrice."""
        mock_ticker = Mock()
        mock_ticker.info = {
            'longName': 'Test Company',
            'price': 100.50,  # No regularMarketPrice
        }
        mock_ticker.cashflow = None
        mock_ticker.splits = pd.Series()
        mock_ticker_class.return_value = mock_ticker

        result = fetch_stock_info('TEST')

        assert result is not None
        assert result.regular_market_price == 100.50

    @patch('sangre_signal.fetchers.yahoo_finance.yf.Ticker')
    def test_fetch_stock_info_includes_all_fields(self, mock_ticker_class):
        """Test that fetch_stock_info includes all expected fields."""
        mock_ticker = Mock()
        mock_ticker.info = {
            'longName': 'Test Inc.',
            'shortName': 'Test',
            'country': 'United States',
            'countryOfOrigin': 'USA',
            'address1': '123 Main St',
            'city': 'TestCity',
            'state': 'TS',
            'zip': '12345',
            'exchange': 'TEST',
            'market': 'us_market',
            'sector': 'Technology',
            'industry': 'Software',
            'marketCap': 1000000000,
            'regularMarketPrice': 50.0,
            'preMarketPrice': 49.5,
            'postMarketPrice': 50.5,
            'fiftyTwoWeekHigh': 60.0,
            'fiftyTwoWeekLow': 40.0,
            'averageVolume10days': 1000000,
            'sharesOutstanding': 10000000,
            'floatShares': 9000000,
            'totalDebt': 5000000,
            'debtToEquity': 0.5,
            'fullTimeEmployees': 1000,
            'website': 'https://test.com',
            'shortPercentOfFloat': 0.05,
            'shortRatio': 2.5,
            'heldPercentInsiders': 0.1,
            'heldPercentInstitutions': 0.6,
            'lastSplitFactor': '2:1',
            'lastSplitDate': 1609459200,
        }
        mock_ticker.cashflow = None
        mock_ticker.splits = pd.Series()
        mock_ticker_class.return_value = mock_ticker

        result = fetch_stock_info('TEST')

        assert result is not None
        assert result.long_name == 'Test Inc.'
        assert result.country == 'United States'
        assert result.market_cap == 1000000000
        assert result.website == 'https://test.com'


class TestIsAdrYahoo:
    """Tests for is_adr_yahoo function."""

    def test_is_adr_yahoo_explicit_adr_in_name(self):
        """Test ADR detection when 'ADR' is in the name."""
        stock = StockInfo(
            ticker='BABA',
            long_name='Alibaba Group Holding Limited ADR',
            country='China',
            exchange='NYSE',
            market='us_market',
        )
        assert is_adr_yahoo(stock) is True

    def test_is_adr_yahoo_american_depositary_in_name(self):
        """Test ADR detection with 'American Depositary' in name."""
        stock = StockInfo(
            ticker='TEST',
            long_name='Test Company American Depositary Receipt',
            country='China',
            exchange='NYSE',
        )
        assert is_adr_yahoo(stock) is True

    def test_is_adr_yahoo_foreign_on_us_exchange(self):
        """Test ADR detection for foreign company on US exchange."""
        stock = StockInfo(
            ticker='ASML',
            long_name='ASML Holding N.V.',
            country='Netherlands',
            exchange='NASDAQ',
            market='us_market',
        )
        assert is_adr_yahoo(stock) is True

    def test_is_adr_yahoo_us_company(self):
        """Test that US companies are not marked as ADR."""
        stock = StockInfo(
            ticker='AAPL',
            long_name='Apple Inc.',
            country='United States',
            exchange='NASDAQ',
            market='us_market',
        )
        assert is_adr_yahoo(stock) is False

    def test_is_adr_yahoo_foreign_not_on_us_exchange(self):
        """Test foreign company not on US exchange."""
        stock = StockInfo(
            ticker='TEST',
            long_name='Test Company',
            country='Germany',
            exchange='FRA',
            market='de_market',
        )
        assert is_adr_yahoo(stock) is False

    def test_is_adr_yahoo_no_country_data(self):
        """Test ADR detection when country data is missing."""
        stock = StockInfo(
            ticker='TEST',
            long_name='Test Company',
            exchange='NYSE',
            market='us_market',
        )
        # No country means can't determine if foreign
        assert is_adr_yahoo(stock) is False

    def test_is_adr_yahoo_various_us_exchanges(self):
        """Test ADR detection on various US exchanges."""
        for exchange in ['NYSE', 'NASDAQ', 'AMEX', 'BATS', 'ARCA']:
            stock = StockInfo(
                ticker='TEST',
                country='China',
                exchange=exchange,
            )
            assert is_adr_yahoo(stock) is True, f"Failed for exchange {exchange}"


class TestGetOperatingCashFlow:
    """Tests for get_operating_cash_flow function."""

    def test_get_operating_cash_flow_success(self):
        """Test successful cash flow retrieval."""
        # Create actual DataFrame (not mock) for proper pandas behavior
        cf_data = pd.DataFrame({
            '2023-12-31': [1000000, 500000, 200000],
            '2022-12-31': [900000, 450000, 180000],
        }, index=['Total Cash From Operating Activities', 'Other1', 'Other2'])

        mock_ticker = Mock()
        mock_ticker.cashflow = cf_data

        result = get_operating_cash_flow(mock_ticker)

        assert result == 1000000

    def test_get_operating_cash_flow_alternative_field_name(self):
        """Test cash flow with alternative field name."""
        # Create actual DataFrame (not mock) for proper pandas behavior
        cf_data = pd.DataFrame({
            '2023-12-31': [2000000, 500000],
            '2022-12-31': [1800000, 450000],
        }, index=['totalCashFromOperatingActivities', 'Other'])

        mock_ticker = Mock()
        mock_ticker.cashflow = cf_data

        result = get_operating_cash_flow(mock_ticker)

        assert result == 2000000

    def test_get_operating_cash_flow_no_data(self):
        """Test when cash flow data is unavailable."""
        mock_ticker = Mock()
        mock_ticker.cashflow = None

        result = get_operating_cash_flow(mock_ticker)

        assert result is None

    def test_get_operating_cash_flow_empty_dataframe(self):
        """Test when cash flow dataframe is empty."""
        mock_ticker = Mock()
        mock_ticker.cashflow = pd.DataFrame()

        result = get_operating_cash_flow(mock_ticker)

        assert result is None

    def test_get_operating_cash_flow_field_not_found(self):
        """Test when operating cash flow field is not in data."""
        mock_ticker = Mock()
        cf_data = pd.DataFrame({
            0: [500000],
        }, index=['Some Other Field'])
        mock_ticker.cashflow = cf_data

        result = get_operating_cash_flow(mock_ticker)

        assert result is None

    def test_get_operating_cash_flow_exception(self):
        """Test that exceptions are handled gracefully."""
        mock_ticker = Mock()
        mock_ticker.cashflow = Mock(side_effect=Exception("Error"))

        result = get_operating_cash_flow(mock_ticker)

        assert result is None


class TestInterpretSplitFactor:
    """Tests for interpret_split_factor function."""

    def test_interpret_split_factor_forward_split(self):
        """Test interpreting a forward split (2:1)."""
        result = interpret_split_factor("2:1")
        assert result == "2:1, split"

    def test_interpret_split_factor_reverse_split(self):
        """Test interpreting a reverse split (1:10)."""
        result = interpret_split_factor("1:10")
        assert result == "1:10, reverse split"

    def test_interpret_split_factor_from_ratio_forward(self):
        """Test interpreting split from ratio float (forward split)."""
        result = interpret_split_factor(None, 2.0)
        assert result == "2:1, split"

    def test_interpret_split_factor_from_ratio_reverse(self):
        """Test interpreting split from ratio float (reverse split)."""
        result = interpret_split_factor(None, 0.5)
        assert result == "1:2, reverse split"

    def test_interpret_split_factor_invalid_string(self):
        """Test with invalid split factor string."""
        result = interpret_split_factor("invalid")
        assert result == ""

    def test_interpret_split_factor_no_data(self):
        """Test with no split data."""
        result = interpret_split_factor(None, None)
        assert result == ""

    def test_interpret_split_factor_zero_ratio(self):
        """Test with zero ratio."""
        result = interpret_split_factor(None, 0.0)
        assert result == ""

    def test_interpret_split_factor_various_ratios(self):
        """Test various split ratios."""
        assert "3:1, split" == interpret_split_factor("3:1")
        assert "1:5, reverse split" == interpret_split_factor("1:5")
        assert "4:1, split" == interpret_split_factor(None, 4.0)
        assert "1:3, reverse split" == interpret_split_factor(None, 0.333)


class TestGetLastSplitDetails:
    """Tests for get_last_split_details function."""

    def test_get_last_split_details_from_info(self):
        """Test getting split details from info dict."""
        mock_ticker = Mock()
        mock_ticker.splits = pd.Series()

        info = {
            'lastSplitFactor': '2:1',
            'lastSplitDate': 1609459200,  # 2021-01-01 00:00:00 UTC
        }

        result = get_last_split_details(mock_ticker, info)

        assert '2021-01-01' in result
        assert '2:1, split' in result

    def test_get_last_split_details_no_date(self):
        """Test split details when date is missing."""
        mock_ticker = Mock()
        mock_ticker.splits = pd.Series()

        info = {
            'lastSplitFactor': '2:1',
        }

        result = get_last_split_details(mock_ticker, info)

        assert result == '2:1, split'

    def test_get_last_split_details_from_ticker_splits(self):
        """Test getting split details from ticker splits history."""
        mock_ticker = Mock()
        split_data = pd.Series(
            [2.0],
            index=[pd.Timestamp('2022-06-15')]
        )
        mock_ticker.splits = split_data

        info = {}

        result = get_last_split_details(mock_ticker, info)

        assert '2022-06-15' in result
        assert 'split' in result

    def test_get_last_split_details_no_data(self):
        """Test when no split data is available."""
        mock_ticker = Mock()
        mock_ticker.splits = pd.Series()

        info = {}

        result = get_last_split_details(mock_ticker, info)

        assert result == ""

    def test_get_last_split_details_exception(self):
        """Test that exceptions return empty string."""
        mock_ticker = Mock()
        mock_ticker.splits = Mock(side_effect=Exception("Error"))

        info = {}

        result = get_last_split_details(mock_ticker, info)

        assert result == ""


class TestYahooFinanceEdgeCases:
    """Tests for edge cases in Yahoo Finance fetcher."""

    def test_is_adr_yahoo_handles_none_values(self):
        """Test is_adr_yahoo handles None values gracefully."""
        stock = StockInfo(
            ticker='TEST',
            long_name=None,
            short_name=None,
            country=None,
            exchange=None,
            market=None,
        )
        # Should not crash
        result = is_adr_yahoo(stock)
        assert isinstance(result, bool)

    def test_is_adr_yahoo_case_insensitive(self):
        """Test that ADR detection is case-insensitive."""
        stock = StockInfo(
            ticker='TEST',
            long_name='Test Company adr',  # lowercase
            country='China',
            exchange='nyse',  # lowercase
        )
        assert is_adr_yahoo(stock) is True

    @patch('sangre_signal.fetchers.yahoo_finance.yf.Ticker')
    def test_fetch_handles_missing_optional_fields(self, mock_ticker_class):
        """Test that fetch handles missing optional fields."""
        mock_ticker = Mock()
        mock_ticker.info = {
            'longName': 'Minimal Company',
            # Most fields missing
        }
        mock_ticker.cashflow = None
        mock_ticker.splits = pd.Series()
        mock_ticker_class.return_value = mock_ticker

        result = fetch_stock_info('MIN')

        assert result is not None
        assert result.long_name == 'Minimal Company'
        assert result.country is None
        assert result.market_cap is None
