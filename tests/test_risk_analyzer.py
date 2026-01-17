"""Tests for risk analyzer module."""

import pytest
from sangre_signal.models import StockInfo, RiskSeverity
from sangre_signal.analyzers.risk_analyzer import (
    RiskAnalyzer,
    analyze_stock_risks,
    _country_matches,
)


class TestCountryMatches:
    """Tests for _country_matches helper function."""

    def test_country_matches_exact(self):
        """Test exact country match."""
        assert _country_matches("China", ["China"])
        assert _country_matches("CN", ["CN"])

    def test_country_matches_case_insensitive(self):
        """Test case-insensitive matching."""
        assert _country_matches("china", ["China"])
        assert _country_matches("CHINA", ["china"])
        assert _country_matches("China", ["CHINA"])

    def test_country_matches_substring(self):
        """Test substring matching."""
        assert _country_matches("People's Republic of China", ["China"])
        assert _country_matches("Russian Federation", ["Russia"])

    def test_country_matches_multiple_patterns(self):
        """Test matching against multiple patterns."""
        patterns = ["CN", "China", "PRC"]
        assert _country_matches("China", patterns)
        assert _country_matches("CN", patterns)
        assert _country_matches("People's Republic of China (PRC)", patterns)

    def test_country_matches_no_match(self):
        """Test when no patterns match."""
        assert not _country_matches("United States", ["China", "Russia"])

    def test_country_matches_empty_value(self):
        """Test with empty/None value."""
        assert not _country_matches("", ["China"])
        assert not _country_matches(None, ["China"])

    def test_country_matches_empty_patterns(self):
        """Test with empty patterns list."""
        assert not _country_matches("China", [])


class TestRiskAnalyzer:
    """Tests for RiskAnalyzer class."""

    def test_analyzer_initialization(self):
        """Test RiskAnalyzer initialization."""
        analyzer = RiskAnalyzer()
        assert analyzer.config is not None
        assert hasattr(analyzer.config, 'risky_countries')
        assert hasattr(analyzer.config, 'min_free_float')

    def test_analyze_country_risk_us_stock(self, sample_us_stock):
        """Test country risk analysis for US stock."""
        analyzer = RiskAnalyzer()
        flags = analyzer.analyze_country_risk(sample_us_stock)
        # US stocks should have no country flags
        assert len(flags) == 0

    def test_analyze_country_risk_foreign_stock(self, sample_foreign_stock):
        """Test country risk analysis for non-US stock."""
        analyzer = RiskAnalyzer()
        flags = analyzer.analyze_country_risk(sample_foreign_stock)
        # Foreign stock should have non-US flag
        assert len(flags) == 1
        assert flags[0].flag_type == "country"
        assert "non-US" in flags[0].message
        assert flags[0].severity == RiskSeverity.MEDIUM

    def test_analyze_country_risk_risky_country(self, sample_risky_country_stock):
        """Test country risk analysis for high-risk country."""
        analyzer = RiskAnalyzer()
        flags = analyzer.analyze_country_risk(sample_risky_country_stock)
        # Should have both high-risk and non-US flags
        assert len(flags) == 2
        flag_types = [f.message for f in flags]
        assert any("red-flag list" in msg for msg in flag_types)
        assert any("non-US" in msg for msg in flag_types)
        # At least one should be HIGH severity
        severities = [f.severity for f in flags]
        assert RiskSeverity.HIGH in severities

    def test_analyze_country_risk_no_country_data(self):
        """Test country risk when country data is missing."""
        stock = StockInfo(ticker="TEST")
        analyzer = RiskAnalyzer()
        flags = analyzer.analyze_country_risk(stock)
        assert len(flags) == 0

    def test_analyze_headquarters_risk_clean(self, sample_us_stock):
        """Test headquarters risk for clean location."""
        analyzer = RiskAnalyzer()
        flags = analyzer.analyze_headquarters_risk(sample_us_stock)
        assert len(flags) == 0

    def test_analyze_headquarters_risk_cayman(self, sample_cayman_hq_stock):
        """Test headquarters risk for Cayman Islands location."""
        analyzer = RiskAnalyzer()
        flags = analyzer.analyze_headquarters_risk(sample_cayman_hq_stock)
        assert len(flags) == 1
        assert flags[0].flag_type == "headquarters"
        assert "red-flag keywords" in flags[0].message
        assert flags[0].severity == RiskSeverity.HIGH

    def test_analyze_headquarters_risk_no_hq_data(self):
        """Test headquarters risk when HQ data is missing."""
        stock = StockInfo(ticker="TEST")
        analyzer = RiskAnalyzer()
        flags = analyzer.analyze_headquarters_risk(stock)
        assert len(flags) == 0

    def test_analyze_float_risk_normal_float(self, sample_us_stock):
        """Test float risk for normal float size."""
        analyzer = RiskAnalyzer()
        flags = analyzer.analyze_float_risk(sample_us_stock)
        # Large float should have no flags
        assert len(flags) == 0

    def test_analyze_float_risk_low_float(self, sample_low_float_stock):
        """Test float risk for low float stock."""
        analyzer = RiskAnalyzer()
        flags = analyzer.analyze_float_risk(sample_low_float_stock)
        assert len(flags) == 1
        assert flags[0].flag_type == "float"
        assert "Float below" in flags[0].message
        assert flags[0].severity == RiskSeverity.MEDIUM

    def test_analyze_float_risk_no_float_data(self):
        """Test float risk when float data is missing."""
        stock = StockInfo(ticker="TEST")
        analyzer = RiskAnalyzer()
        flags = analyzer.analyze_float_risk(stock)
        assert len(flags) == 0

    def test_analyze_adr_risk_not_adr(self, sample_us_stock):
        """Test ADR risk for non-ADR stock."""
        analyzer = RiskAnalyzer()
        flags = analyzer.analyze_adr_risk(sample_us_stock)
        assert len(flags) == 0

    def test_analyze_adr_risk_is_adr(self, sample_adr_stock):
        """Test ADR risk for ADR stock."""
        analyzer = RiskAnalyzer()
        flags = analyzer.analyze_adr_risk(sample_adr_stock)
        assert len(flags) == 1
        assert flags[0].flag_type == "adr"
        assert "ADR" in flags[0].message
        assert flags[0].severity == RiskSeverity.MEDIUM

    def test_analyze_all_clean_stock(self, sample_us_stock):
        """Test comprehensive analysis for clean US stock."""
        analyzer = RiskAnalyzer()
        analysis = analyzer.analyze_all(sample_us_stock)

        assert analysis.ticker == "AAPL"
        assert len(analysis.flags) == 0
        assert not analysis.has_risks

    def test_analyze_all_risky_stock(self):
        """Test comprehensive analysis for stock with multiple risks."""
        stock = StockInfo(
            ticker="RISK",
            country="CN",  # Risky country
            address1="PO Box 123",
            city="George Town",
            state="Cayman Islands",  # Risky HQ
            exchange="NYSE",
            float_shares=2000000,  # Low float
            is_adr=True,  # ADR
        )

        analyzer = RiskAnalyzer()
        analysis = analyzer.analyze_all(stock)

        assert analysis.ticker == "RISK"
        assert analysis.has_risks
        # Should have multiple risk flags
        assert len(analysis.flags) >= 4

        # Check that different risk types are present
        flag_types = [f.flag_type for f in analysis.flags]
        assert "country" in flag_types
        assert "headquarters" in flag_types
        assert "float" in flag_types
        assert "adr" in flag_types

    def test_analyze_all_foreign_stock_moderate_risk(self, sample_foreign_stock):
        """Test analysis for foreign stock with moderate risk."""
        analyzer = RiskAnalyzer()
        analysis = analyzer.analyze_all(sample_foreign_stock)

        assert analysis.ticker == "ASML"
        assert analysis.has_risks
        # Should have at least non-US flag
        assert len(analysis.flags) >= 1

    def test_analyze_stock_risks_convenience_function(self, sample_us_stock):
        """Test the convenience function analyze_stock_risks."""
        analysis = analyze_stock_risks(sample_us_stock)

        assert analysis.ticker == "AAPL"
        assert isinstance(analysis.flags, list)

    def test_analyzer_custom_config(self):
        """Test that analyzer uses its config."""
        analyzer = RiskAnalyzer()

        # Verify config is loaded
        assert len(analyzer.config.risky_countries) > 0
        assert analyzer.config.min_free_float > 0

        # Test that config is used in analysis
        stock = StockInfo(
            ticker="TEST",
            country=analyzer.config.risky_countries[0],
            float_shares=analyzer.config.min_free_float - 1,
        )

        analysis = analyzer.analyze_all(stock)
        assert analysis.has_risks
        assert len(analysis.flags) >= 2  # Country + float flags


class TestRiskAnalyzerEdgeCases:
    """Tests for edge cases in risk analysis."""

    def test_analyze_with_minimal_data(self):
        """Test analysis with minimal stock data."""
        stock = StockInfo(ticker="MIN")
        analyzer = RiskAnalyzer()
        analysis = analyzer.analyze_all(stock)

        # Should complete without errors
        assert analysis.ticker == "MIN"
        assert isinstance(analysis.flags, list)

    def test_analyze_with_none_values(self):
        """Test analysis handles None values gracefully."""
        stock = StockInfo(
            ticker="NONE",
            country=None,
            float_shares=None,
            is_adr=False,
        )
        analyzer = RiskAnalyzer()
        analysis = analyzer.analyze_all(stock)

        assert analysis.ticker == "NONE"
        # Should not crash, minimal or no flags
        assert isinstance(analysis.flags, list)

    def test_float_risk_boundary_conditions(self):
        """Test float risk at boundary values."""
        analyzer = RiskAnalyzer()
        threshold = analyzer.config.min_free_float

        # Just above threshold - no flag
        stock_above = StockInfo(ticker="ABOVE", float_shares=threshold + 1)
        flags_above = analyzer.analyze_float_risk(stock_above)
        assert len(flags_above) == 0

        # Exactly at threshold - no flag
        stock_at = StockInfo(ticker="AT", float_shares=threshold)
        flags_at = analyzer.analyze_float_risk(stock_at)
        assert len(flags_at) == 0

        # Just below threshold - flag
        stock_below = StockInfo(ticker="BELOW", float_shares=threshold - 1)
        flags_below = analyzer.analyze_float_risk(stock_below)
        assert len(flags_below) == 1
