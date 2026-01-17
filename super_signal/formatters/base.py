"""Base formatter classes for stock output.

This module provides the abstract base class for formatters and
a factory function to get the appropriate formatter.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, TYPE_CHECKING

from ..models import StockInfo, RiskAnalysis

if TYPE_CHECKING:
    from ..cli import TickerResult


class BaseFormatter(ABC):
    """Abstract base class for stock data formatters.

    Subclasses must implement the format() method to convert
    stock data into a specific output format.
    """

    @abstractmethod
    def format(
        self,
        stock_info: StockInfo,
        risk_analysis: RiskAnalysis,
        float_threshold: int,
        vix_value: Optional[float] = None
    ) -> str:
        """Format stock data into the desired output format.

        Args:
            stock_info: Stock information data
            risk_analysis: Risk analysis results
            float_threshold: Minimum float threshold for risk highlighting
            vix_value: Current VIX index value (optional)

        Returns:
            Formatted string output
        """
        pass

    def format_batch(
        self,
        results: List["TickerResult"],
        float_threshold: int,
        vix_value: Optional[float] = None
    ) -> str:
        """Format multiple ticker results.

        Default implementation formats each result separately and joins them.
        Subclasses can override for format-specific batch handling.

        Args:
            results: List of TickerResult objects
            float_threshold: Minimum float threshold for risk highlighting
            vix_value: Current VIX index value (optional)

        Returns:
            Formatted string output for all results
        """
        outputs = []
        for result in results:
            if result.success:
                outputs.append(self.format(
                    result.stock_info,
                    result.risk_analysis,
                    float_threshold,
                    vix_value
                ))
            else:
                outputs.append(self.format_error(result.ticker, result.error))
        return "\n".join(outputs)

    def format_error(self, ticker: str, error: Optional[str]) -> str:
        """Format an error result for a ticker.

        Args:
            ticker: Stock ticker symbol
            error: Error message

        Returns:
            Formatted error string
        """
        return f"Error for {ticker}: {error or 'Unknown error'}"


def get_formatter(format_type: str, language: str = "en") -> BaseFormatter:
    """Factory function to get the appropriate formatter.

    Args:
        format_type: Output format type ('text', 'json', 'csv', or 'claude')
        language: Language for output ('en' or 'es'). Only applies to claude format.

    Returns:
        Formatter instance for the specified format

    Raises:
        ValueError: If format_type is not supported
    """
    from .text_formatter import TextFormatter
    from .json_formatter import JsonFormatter
    from .csv_formatter import CsvFormatter
    from .claude_formatter import ClaudeFormatter

    # Claude formatter needs special handling for language parameter
    if format_type == 'claude':
        return ClaudeFormatter(language=language)

    formatters = {
        'text': TextFormatter,
        'json': JsonFormatter,
        'csv': CsvFormatter,
    }

    if format_type not in formatters:
        valid_formats = ', '.join(sorted(list(formatters.keys()) + ['claude']))
        raise ValueError(
            f"Unsupported format: '{format_type}'. "
            f"Valid formats are: {valid_formats}"
        )

    return formatters[format_type]()
