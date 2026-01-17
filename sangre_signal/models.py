"""Data models for the stock screener application.

This module defines the core data structures used throughout the application,
including stock information, risk flags, and analysis results.
"""

from dataclasses import dataclass, field
from typing import Optional, List
from enum import Enum


class RiskSeverity(Enum):
    """Severity levels for risk flags."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


@dataclass
class StockInfo:
    """Comprehensive stock information from Yahoo Finance.

    Attributes:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        long_name: Full company name
        short_name: Short company name
        country: Country of origin
        country_of_origin: Alternative country field
        address1: Street address
        city: City
        state: State/province
        zip_code: Postal code
        exchange: Stock exchange (e.g., 'NASDAQ')
        market: Market classification
        sector: Business sector
        industry: Industry classification
        market_cap: Market capitalization in dollars
        regular_market_price: Current market price
        pre_market_price: Pre-market trading price
        post_market_price: After-hours trading price
        fifty_two_week_high: 52-week high price
        fifty_two_week_low: 52-week low price
        average_volume_10days: 10-day average trading volume
        regular_market_volume: Current day's trading volume
        shares_outstanding: Total shares outstanding
        float_shares: Publicly traded shares (float)
        total_debt: Total company debt
        debt_to_equity: Debt-to-equity ratio
        full_time_employees: Number of full-time employees
        website: Company website URL
        short_percent_of_float: Percentage of float shares sold short
        short_ratio: Days to cover short positions
        held_percent_insiders: Percentage owned by insiders
        held_percent_institutions: Percentage owned by institutions
        last_split_factor: Stock split ratio (e.g., "2:1")
        last_split_date: Unix timestamp of last split
        operating_cash_flow: Operating cash flow from most recent period
        last_split_display: Formatted split information
        is_adr: Whether the stock is an ADR (American Depositary Receipt)
        directors: List of key executives and directors
    """
    ticker: str
    long_name: Optional[str] = None
    short_name: Optional[str] = None
    country: Optional[str] = None
    country_of_origin: Optional[str] = None
    address1: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    zip_code: Optional[str] = None
    exchange: Optional[str] = None
    market: Optional[str] = None
    sector: Optional[str] = None
    industry: Optional[str] = None
    market_cap: Optional[float] = None
    regular_market_price: Optional[float] = None
    pre_market_price: Optional[float] = None
    post_market_price: Optional[float] = None
    fifty_two_week_high: Optional[float] = None
    fifty_two_week_low: Optional[float] = None
    average_volume_10days: Optional[float] = None
    regular_market_volume: Optional[float] = None
    shares_outstanding: Optional[float] = None
    float_shares: Optional[float] = None
    total_debt: Optional[float] = None
    debt_to_equity: Optional[float] = None
    full_time_employees: Optional[int] = None
    website: Optional[str] = None
    short_percent_of_float: Optional[float] = None
    short_ratio: Optional[float] = None
    held_percent_insiders: Optional[float] = None
    held_percent_institutions: Optional[float] = None
    last_split_factor: Optional[str] = None
    last_split_date: Optional[int] = None
    operating_cash_flow: Optional[float] = None
    last_split_display: str = ""
    is_adr: bool = False
    directors: List[str] = field(default_factory=list)

    def get_country(self) -> str:
        """Get the country, preferring 'country' over 'country_of_origin'.

        Returns:
            Country name, or empty string if not available.
        """
        return self.country or self.country_of_origin or ""

    def get_headquarters(self) -> str:
        """Build full headquarters address from components.

        Returns:
            Comma-separated headquarters address string.
        """
        parts = [
            self.address1,
            self.city,
            self.state,
            self.zip_code,
            self.get_country()
        ]
        return ", ".join(str(p) for p in parts if p)

    def get_display_name(self) -> str:
        """Get the display name, preferring long_name over short_name.

        Returns:
            Company name, or empty string if not available.
        """
        return self.long_name or self.short_name or ""

    def get_price(self) -> Optional[float]:
        """Get the regular market price.

        Returns:
            Regular market price, or None if not available.
        """
        return self.regular_market_price

    def percent_off_52week_high(self) -> Optional[float]:
        """Calculate percentage off 52-week high.

        Returns:
            Percentage (e.g., -15.5 for 15.5% below high), or None if cannot calculate.
        """
        price = self.get_price()
        if price and self.fifty_two_week_high and self.fifty_two_week_high > 0:
            return (price / self.fifty_two_week_high - 1) * 100
        return None


@dataclass
class RiskFlag:
    """Individual risk flag detected during analysis.

    Attributes:
        flag_type: Type/category of the risk flag
        message: Human-readable description of the risk
        severity: Severity level of the risk
    """
    flag_type: str
    message: str
    severity: RiskSeverity = RiskSeverity.MEDIUM

    def __str__(self) -> str:
        """String representation of the risk flag.

        Returns:
            Formatted risk flag message with severity.
        """
        return f"[{self.severity.value.upper()}] {self.message}"


@dataclass
class RiskAnalysis:
    """Complete risk analysis results for a stock.

    Attributes:
        ticker: Stock ticker symbol
        flags: List of detected risk flags
        has_risks: Whether any risks were detected
    """
    ticker: str
    flags: List[RiskFlag] = field(default_factory=list)

    @property
    def has_risks(self) -> bool:
        """Check if any risk flags were detected.

        Returns:
            True if one or more risk flags exist, False otherwise.
        """
        return len(self.flags) > 0

    def get_flags_by_severity(self, severity: RiskSeverity) -> List[RiskFlag]:
        """Filter risk flags by severity level.

        Args:
            severity: The severity level to filter by.

        Returns:
            List of risk flags matching the specified severity.
        """
        return [flag for flag in self.flags if flag.severity == severity]

    def add_flag(self, flag_type: str, message: str,
                 severity: RiskSeverity = RiskSeverity.MEDIUM) -> None:
        """Add a new risk flag to the analysis.

        Args:
            flag_type: Type/category of the risk flag.
            message: Human-readable description of the risk.
            severity: Severity level (default: MEDIUM).
        """
        self.flags.append(RiskFlag(flag_type, message, severity))
