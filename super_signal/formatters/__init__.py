"""Formatters package for displaying stock information.

This package provides modules for formatting and displaying stock data
in various formats: text (ANSI colored), JSON, CSV, and Claude AI-powered.
"""

from .display import (
    format_number,
    format_percent,
    colorize_country,
    colorize_headquarters,
    colorize_adr_status,
    colorize_float,
    format_header,
    format_risk_flags,
    format_basic_info,
    format_headquarters,
    format_ownership_info,
    format_price_info,
    format_trading_info,
    format_financial_info,
    format_company_info,
    format_timestamp,
    format_executives,
    format_risk_details,
    print_stock_summary,
)
from .base import BaseFormatter, get_formatter
from .text_formatter import TextFormatter
from .json_formatter import JsonFormatter
from .csv_formatter import CsvFormatter
from .claude_formatter import ClaudeFormatter

__all__ = [
    # Display functions
    "format_number",
    "format_percent",
    "colorize_country",
    "colorize_headquarters",
    "colorize_adr_status",
    "colorize_float",
    "format_header",
    "format_risk_flags",
    "format_basic_info",
    "format_headquarters",
    "format_ownership_info",
    "format_price_info",
    "format_trading_info",
    "format_financial_info",
    "format_company_info",
    "format_timestamp",
    "format_executives",
    "format_risk_details",
    "print_stock_summary",
    # Formatter classes and factory
    "BaseFormatter",
    "get_formatter",
    "TextFormatter",
    "JsonFormatter",
    "CsvFormatter",
    "ClaudeFormatter",
]
