"""Configuration settings for the stock screener application.

This module centralizes all configuration including risk thresholds,
display settings, ANSI colors, logging configuration, and Claude AI integration.
"""

import logging
import os
import sys
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Literal


# --- Risk Detection Configuration ---

@dataclass
class RiskThresholds:
    """Configurable thresholds for risk detection.

    Attributes:
        risky_countries: List of country codes considered high-risk
        risky_headquarters_keywords: Keywords in HQ location that indicate risk
        min_free_float: Minimum float shares to avoid illiquidity risk
    """
    risky_countries: List[str]
    risky_headquarters_keywords: List[str]
    min_free_float: int


# Default risk detection thresholds
RED_FLAGS = RiskThresholds(
    risky_countries=["RU", "CN", "IR"],
    risky_headquarters_keywords=["Cayman", "BVI", "SpA", "India", "China"],
    min_free_float=3_000_000,
)


# List of US country variations for comparisons
US_COUNTRY_VARIATIONS = (
    "united states",
    "usa",
    "u.s.a.",
    "us",
    "u.s.",
)


# --- ANSI Color Configuration ---

class ANSIColor(Enum):
    """ANSI color codes for terminal output.

    These codes enable colored text output in terminal applications.
    """
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    NEGATIVE = "\033[7m"  # Inverted colors

    # Standard colors
    RED = "\033[31m"
    YELLOW = "\033[33m"
    CYAN = "\033[36m"
    WHITE = "\033[97m"

    # Bright/bold colors
    BOLD_CYAN = "\033[1;36m"
    LIGHT_GREEN = "\033[1;32m"
    BRIGHT_BLUE = "\033[94m"

    # Background colors
    BG_BRIGHT_RED = "\033[101m"


# --- Display Configuration ---

def _get_safe_horizontal_line() -> str:
    """Get a horizontal line character safe for the terminal encoding.

    Returns Unicode box-drawing character if the terminal supports it,
    otherwise returns ASCII hyphen as fallback.

    Returns:
        Horizontal line character (either "-" or "-")
    """
    try:
        # Check if stdout encoding supports Unicode
        encoding = sys.stdout.encoding or 'ascii'

        # Try to encode the Unicode box-drawing character
        test_char = "-"
        test_char.encode(encoding)

        return test_char
    except (UnicodeEncodeError, LookupError, AttributeError):
        # Fallback to ASCII hyphen if Unicode isn't supported
        return "-"


@dataclass
class DisplayConfig:
    """Display formatting configuration.

    Attributes:
        summary_width: Width of the summary display box
        label_width: Width of field labels
        max_field_width: Maximum width for field values before wrapping
        horizontal_line: Character used for horizontal lines
        directors_max_count: Maximum number of directors to display
    """
    summary_width: int = 70
    label_width: int = 20
    max_field_width: int = 40
    horizontal_line: str = field(default_factory=_get_safe_horizontal_line)
    directors_max_count: int = 10


# Default display configuration
DISPLAY_CONFIG = DisplayConfig()


# Field labels for stock summary display
FIELD_LABELS = {
    "flag_risk": "FLAG RISK ----------- ",
    "company": "Company ------------- ",
    "ticker": "Stock Symbol -------- ",
    "exchange": "Exchange ------------ ",
    "adr": "ADR ----------------- ",
    "country": "Country of Origin --- ",
    "headquarters": "Headquarters -------- ",
    "market_cap": "Market Cap ---------- ",
    "insider_ownership": "Insider Ownership --- ",
    "institutional_ownership": "Institutional Own. -- ",
    "price_market": "Price (Market Hrs) -- ",
    "price_premarket": "Premarket Price ----- ",
    "price_postmarket": "Aftermarket Price --- ",
    "last_split": "Last Split ---------- ",
    "week_52_high": "52W High ------------ ",
    "week_52_low": "52W Low ------------- ",
    "pct_off_high": "% Off 52W High ------ ",
    "avg_volume_10d": "Avg Volume (10D) ---- ",
    "shares_outstanding": "Shares Outstanding -- ",
    "float": "Float --------------- ",
    "short_pct_float": "Short % of Float ---- ",
    "short_ratio": "Short Ratio (days) -- ",
    "debt": "Debt ---------------- ",
    "cash_flow": "Cash Flow (oper.) --- ",
    "employees": "Employee Count ------ ",
    "website": "Homepage ------------ ",
    "timestamp": "As Of (EST) --------- ",
    "vix": "VIX Index ----------- ",
}


# --- Logging Configuration ---

@dataclass
class LoggingConfig:
    """Logging configuration for the application.

    Attributes:
        log_file: Path to the log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        console_log_level: Logging level for console output
        log_format: Format string for log messages
        date_format: Format string for timestamps in log messages
    """
    log_file: str = "super_signal.log"
    log_level: int = logging.INFO
    console_log_level: int = logging.WARNING
    log_format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"


# Default logging configuration
LOGGING_CONFIG = LoggingConfig()


def setup_logging(config: LoggingConfig = LOGGING_CONFIG) -> None:
    """Set up logging configuration for the application.

    Configures both file and console logging handlers with appropriate
    log levels and formatting.

    Args:
        config: Logging configuration to use (defaults to LOGGING_CONFIG).
    """
    # Create logger
    logger = logging.getLogger("super_signal")
    logger.setLevel(config.log_level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # File handler - logs everything at log_level and above
    file_handler = logging.FileHandler(config.log_file)
    file_handler.setLevel(config.log_level)
    file_formatter = logging.Formatter(config.log_format, config.date_format)
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # Console handler - only logs warnings and above
    console_handler = logging.StreamHandler()
    console_handler.setLevel(config.console_log_level)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)


# --- Network Configuration ---

@dataclass
class NetworkConfig:
    """Network request configuration.

    Attributes:
        user_agent: User agent string for HTTP requests
        request_timeout: Timeout in seconds for HTTP requests
    """
    user_agent: str = "Mozilla/5.0 (compatible; stock-inspector/1.0)"
    request_timeout: int = 10


# Default network configuration
NETWORK_CONFIG = NetworkConfig()


# --- Claude AI Configuration ---

@dataclass
class ClaudeConfig:
    """Claude AI integration configuration.

    Attributes:
        api_key: Anthropic API key (loaded from ANTHROPIC_API_KEY env var)
        model: Claude model to use for analysis
        max_tokens: Maximum tokens for response
        language: Output language ('en' for English, 'es' for Spanish)
    """
    api_key: str = field(default_factory=lambda: os.environ.get("ANTHROPIC_API_KEY", ""))
    model: str = "claude-sonnet-4-20250514"
    max_tokens: int = 2000
    language: Literal["en", "es"] = "en"

    def is_configured(self) -> bool:
        """Check if Claude API is properly configured.

        Returns:
            True if API key is set, False otherwise.
        """
        return bool(self.api_key)


# Default Claude configuration
CLAUDE_CONFIG = ClaudeConfig()
