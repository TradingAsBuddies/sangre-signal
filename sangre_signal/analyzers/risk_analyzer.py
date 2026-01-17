"""Risk analysis module for detecting stock risk factors.

This module provides the RiskAnalyzer class which evaluates stocks against
various risk criteria including country of origin, headquarters location,
float size, and ADR status.
"""

import logging
from typing import List

from ..models import StockInfo, RiskAnalysis, RiskFlag, RiskSeverity
from ..config import RED_FLAGS, US_COUNTRY_VARIATIONS

logger = logging.getLogger("sangre_signal.analyzers.risk_analyzer")


def _country_matches(value: str, patterns: List[str]) -> bool:
    """Check if a value contains any of the specified patterns (case-insensitive).

    Args:
        value: String value to check
        patterns: List of pattern strings to match

    Returns:
        True if any pattern is found in value, False otherwise.
    """
    if not value:
        return False
    value_lower = str(value).lower()
    return any(str(p).lower() in value_lower for p in patterns)


class RiskAnalyzer:
    """Analyzer for detecting risk factors in stocks.

    This class evaluates stocks against configurable risk thresholds and
    generates a comprehensive risk analysis.
    """

    def __init__(self):
        """Initialize the risk analyzer with default configuration."""
        self.config = RED_FLAGS

    def analyze_country_risk(self, stock_info: StockInfo) -> List[RiskFlag]:
        """Analyze country-related risk factors.

        Args:
            stock_info: Stock information to analyze

        Returns:
            List of risk flags related to country of origin.
        """
        flags = []
        country = stock_info.get_country()

        if not country:
            return flags

        # Check for high-risk countries
        if _country_matches(country, self.config.risky_countries):
            flags.append(RiskFlag(
                flag_type="country",
                message="Country of origin is in red-flag list",
                severity=RiskSeverity.HIGH
            ))

        # Check for non-US origin
        if country.lower() not in US_COUNTRY_VARIATIONS:
            flags.append(RiskFlag(
                flag_type="country",
                message="Country of origin is non-US",
                severity=RiskSeverity.MEDIUM
            ))

        return flags

    def analyze_headquarters_risk(self, stock_info: StockInfo) -> List[RiskFlag]:
        """Analyze headquarters location risk factors.

        Args:
            stock_info: Stock information to analyze

        Returns:
            List of risk flags related to headquarters location.
        """
        flags = []
        headquarters = stock_info.get_headquarters()

        if not headquarters:
            return flags

        # Check for risky headquarters keywords (e.g., Cayman, BVI)
        if _country_matches(headquarters, self.config.risky_headquarters_keywords):
            flags.append(RiskFlag(
                flag_type="headquarters",
                message="Headquarters location includes red-flag keywords",
                severity=RiskSeverity.HIGH
            ))

        return flags

    def analyze_float_risk(self, stock_info: StockInfo) -> List[RiskFlag]:
        """Analyze float shares risk factors.

        Low float shares can indicate illiquidity and manipulation risk.

        Args:
            stock_info: Stock information to analyze

        Returns:
            List of risk flags related to float shares.
        """
        flags = []
        float_shares = stock_info.float_shares

        if float_shares is None:
            return flags

        # Check if float is below minimum threshold
        if isinstance(float_shares, (int, float)) and float_shares < self.config.min_free_float:
            flags.append(RiskFlag(
                flag_type="float",
                message=f"Float below {self.config.min_free_float / 1_000_000:.1f}M shares",
                severity=RiskSeverity.MEDIUM
            ))

        return flags

    def analyze_adr_risk(self, stock_info: StockInfo) -> List[RiskFlag]:
        """Analyze ADR-related risk factors.

        Args:
            stock_info: Stock information to analyze

        Returns:
            List of risk flags related to ADR status.
        """
        flags = []

        if stock_info.is_adr:
            flags.append(RiskFlag(
                flag_type="adr",
                message="ADR/listed foreign issuer",
                severity=RiskSeverity.MEDIUM
            ))

        return flags

    def analyze_all(self, stock_info: StockInfo) -> RiskAnalysis:
        """Perform comprehensive risk analysis on a stock.

        Args:
            stock_info: Stock information to analyze

        Returns:
            RiskAnalysis object containing all detected risk flags.
        """
        logger.info(f"Analyzing risk factors for {stock_info.ticker}")

        analysis = RiskAnalysis(ticker=stock_info.ticker)

        # Run all risk checks
        country_flags = self.analyze_country_risk(stock_info)
        hq_flags = self.analyze_headquarters_risk(stock_info)
        float_flags = self.analyze_float_risk(stock_info)
        adr_flags = self.analyze_adr_risk(stock_info)

        # Combine all flags
        all_flags = country_flags + hq_flags + float_flags + adr_flags

        # Add flags to analysis
        for flag in all_flags:
            analysis.flags.append(flag)

        logger.info(f"Found {len(analysis.flags)} risk flag(s) for {stock_info.ticker}")

        return analysis


# Convenience function for one-shot analysis
def analyze_stock_risks(stock_info: StockInfo) -> RiskAnalysis:
    """Convenience function to analyze stock risks.

    Args:
        stock_info: Stock information to analyze

    Returns:
        RiskAnalysis object with all detected risk flags.
    """
    analyzer = RiskAnalyzer()
    return analyzer.analyze_all(stock_info)
