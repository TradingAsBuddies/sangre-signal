"""Tests for data models."""

import pytest
from super_signal.models import StockInfo, RiskFlag, RiskAnalysis, RiskSeverity


class TestStockInfo:
    """Tests for StockInfo model."""

    def test_get_country_prefers_country_field(self):
        """Test that get_country() prefers 'country' over 'country_of_origin'."""
        stock = StockInfo(
            ticker="TEST",
            country="United States",
            country_of_origin="Canada"
        )
        assert stock.get_country() == "United States"

    def test_get_country_falls_back_to_country_of_origin(self):
        """Test that get_country() uses country_of_origin when country is None."""
        stock = StockInfo(
            ticker="TEST",
            country=None,
            country_of_origin="Canada"
        )
        assert stock.get_country() == "Canada"

    def test_get_country_returns_empty_string_when_both_none(self):
        """Test that get_country() returns empty string when both fields are None."""
        stock = StockInfo(ticker="TEST")
        assert stock.get_country() == ""

    def test_get_headquarters_builds_full_address(self):
        """Test that get_headquarters() properly formats full address."""
        stock = StockInfo(
            ticker="TEST",
            address1="123 Main St",
            city="New York",
            state="NY",
            zip_code="10001",
            country="United States"
        )
        expected = "123 Main St, New York, NY, 10001, United States"
        assert stock.get_headquarters() == expected

    def test_get_headquarters_handles_missing_fields(self):
        """Test that get_headquarters() skips None fields."""
        stock = StockInfo(
            ticker="TEST",
            city="New York",
            country="United States"
        )
        assert stock.get_headquarters() == "New York, United States"

    def test_get_display_name_prefers_long_name(self):
        """Test that get_display_name() prefers long_name."""
        stock = StockInfo(
            ticker="TEST",
            long_name="Test Company Inc.",
            short_name="Test Co."
        )
        assert stock.get_display_name() == "Test Company Inc."

    def test_get_display_name_falls_back_to_short_name(self):
        """Test that get_display_name() uses short_name when long_name is None."""
        stock = StockInfo(
            ticker="TEST",
            short_name="Test Co."
        )
        assert stock.get_display_name() == "Test Co."

    def test_get_display_name_returns_empty_when_both_none(self):
        """Test that get_display_name() returns empty string when both names are None."""
        stock = StockInfo(ticker="TEST")
        assert stock.get_display_name() == ""

    def test_get_price_returns_regular_market_price(self):
        """Test that get_price() returns regular_market_price."""
        stock = StockInfo(ticker="TEST", regular_market_price=150.75)
        assert stock.get_price() == 150.75

    def test_get_price_returns_none_when_not_set(self):
        """Test that get_price() returns None when price not set."""
        stock = StockInfo(ticker="TEST")
        assert stock.get_price() is None

    def test_percent_off_52week_high_calculates_correctly(self):
        """Test percent_off_52week_high() calculation."""
        stock = StockInfo(
            ticker="TEST",
            regular_market_price=90.0,
            fifty_two_week_high=100.0
        )
        result = stock.percent_off_52week_high()
        assert result is not None
        assert abs(result - (-10.0)) < 0.01  # -10% off high

    def test_percent_off_52week_high_handles_at_high(self):
        """Test percent_off_52week_high() when at 52-week high."""
        stock = StockInfo(
            ticker="TEST",
            regular_market_price=100.0,
            fifty_two_week_high=100.0
        )
        result = stock.percent_off_52week_high()
        assert result is not None
        assert abs(result) < 0.01  # 0% off high

    def test_percent_off_52week_high_returns_none_when_missing_data(self):
        """Test percent_off_52week_high() returns None when data missing."""
        stock = StockInfo(ticker="TEST", regular_market_price=100.0)
        assert stock.percent_off_52week_high() is None

        stock = StockInfo(ticker="TEST", fifty_two_week_high=100.0)
        assert stock.percent_off_52week_high() is None

    def test_percent_off_52week_high_handles_zero_high(self):
        """Test percent_off_52week_high() handles zero high gracefully."""
        stock = StockInfo(
            ticker="TEST",
            regular_market_price=100.0,
            fifty_two_week_high=0.0
        )
        assert stock.percent_off_52week_high() is None


class TestRiskFlag:
    """Tests for RiskFlag model."""

    def test_risk_flag_creation(self):
        """Test creating a RiskFlag."""
        flag = RiskFlag(
            flag_type="country",
            message="Test risk",
            severity=RiskSeverity.HIGH
        )
        assert flag.flag_type == "country"
        assert flag.message == "Test risk"
        assert flag.severity == RiskSeverity.HIGH

    def test_risk_flag_default_severity(self):
        """Test that RiskFlag defaults to MEDIUM severity."""
        flag = RiskFlag(flag_type="test", message="Test message")
        assert flag.severity == RiskSeverity.MEDIUM

    def test_risk_flag_str_representation(self):
        """Test RiskFlag string representation."""
        flag = RiskFlag(
            flag_type="country",
            message="High risk country",
            severity=RiskSeverity.HIGH
        )
        assert str(flag) == "[HIGH] High risk country"

        flag = RiskFlag(
            flag_type="float",
            message="Low float",
            severity=RiskSeverity.MEDIUM
        )
        assert str(flag) == "[MEDIUM] Low float"


class TestRiskAnalysis:
    """Tests for RiskAnalysis model."""

    def test_risk_analysis_creation(self):
        """Test creating a RiskAnalysis."""
        analysis = RiskAnalysis(ticker="TEST")
        assert analysis.ticker == "TEST"
        assert analysis.flags == []
        assert not analysis.has_risks

    def test_has_risks_property(self):
        """Test has_risks property."""
        analysis = RiskAnalysis(ticker="TEST")
        assert not analysis.has_risks

        analysis.flags.append(RiskFlag("test", "Test risk"))
        assert analysis.has_risks

    def test_add_flag_method(self):
        """Test adding flags using add_flag() method."""
        analysis = RiskAnalysis(ticker="TEST")
        analysis.add_flag("country", "Risky country", RiskSeverity.HIGH)

        assert len(analysis.flags) == 1
        assert analysis.flags[0].flag_type == "country"
        assert analysis.flags[0].message == "Risky country"
        assert analysis.flags[0].severity == RiskSeverity.HIGH

    def test_add_flag_default_severity(self):
        """Test add_flag() uses default severity."""
        analysis = RiskAnalysis(ticker="TEST")
        analysis.add_flag("test", "Test message")

        assert analysis.flags[0].severity == RiskSeverity.MEDIUM

    def test_get_flags_by_severity(self):
        """Test filtering flags by severity."""
        analysis = RiskAnalysis(ticker="TEST")
        analysis.add_flag("high1", "High risk 1", RiskSeverity.HIGH)
        analysis.add_flag("med1", "Medium risk 1", RiskSeverity.MEDIUM)
        analysis.add_flag("high2", "High risk 2", RiskSeverity.HIGH)
        analysis.add_flag("low1", "Low risk 1", RiskSeverity.LOW)

        high_flags = analysis.get_flags_by_severity(RiskSeverity.HIGH)
        assert len(high_flags) == 2
        assert all(f.severity == RiskSeverity.HIGH for f in high_flags)

        medium_flags = analysis.get_flags_by_severity(RiskSeverity.MEDIUM)
        assert len(medium_flags) == 1

        low_flags = analysis.get_flags_by_severity(RiskSeverity.LOW)
        assert len(low_flags) == 1

    def test_get_flags_by_severity_empty(self):
        """Test get_flags_by_severity returns empty list when no matches."""
        analysis = RiskAnalysis(ticker="TEST")
        analysis.add_flag("test", "Test", RiskSeverity.LOW)

        high_flags = analysis.get_flags_by_severity(RiskSeverity.HIGH)
        assert high_flags == []


class TestRiskSeverity:
    """Tests for RiskSeverity enum."""

    def test_risk_severity_values(self):
        """Test RiskSeverity enum values."""
        assert RiskSeverity.LOW.value == "low"
        assert RiskSeverity.MEDIUM.value == "medium"
        assert RiskSeverity.HIGH.value == "high"

    def test_risk_severity_comparison(self):
        """Test comparing RiskSeverity values."""
        assert RiskSeverity.LOW == RiskSeverity.LOW
        assert RiskSeverity.MEDIUM != RiskSeverity.HIGH
