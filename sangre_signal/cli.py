"""Command-line interface for the stock screener.

This module provides the interactive CLI for running stock screenings
with colored terminal output.
"""

import os
import sys
import logging
import time
from dataclasses import dataclass
from typing import Optional, List
from concurrent.futures import ThreadPoolExecutor, as_completed

from .fetchers.yahoo_finance import fetch_stock_info, fetch_vix, is_adr_yahoo
from .fetchers.finviz import determine_adr_status, get_directors
from .analyzers import analyze_stock_risks
from .formatters.display import print_stock_summary
from .formatters import get_formatter
from .config import ANSIColor, RED_FLAGS, DISPLAY_CONFIG
from .models import StockInfo, RiskAnalysis

logger = logging.getLogger("sangre_signal.cli")


@dataclass
class TickerResult:
    """Result of processing a single ticker.

    Attributes:
        ticker: Stock ticker symbol
        stock_info: Stock information if successful
        risk_analysis: Risk analysis if successful
        error: Error message if failed
    """
    ticker: str
    stock_info: Optional[StockInfo] = None
    risk_analysis: Optional[RiskAnalysis] = None
    error: Optional[str] = None

    @property
    def success(self) -> bool:
        """Check if the ticker was processed successfully."""
        return self.stock_info is not None


def normalize_tickers(ticker_args: List[str]) -> List[str]:
    """Normalize ticker arguments into a flat list of unique tickers.

    Handles both comma-separated values and multiple -t flags.

    Args:
        ticker_args: List of ticker arguments (may contain commas)

    Returns:
        Deduplicated list of uppercase ticker symbols preserving first occurrence order

    Examples:
        >>> normalize_tickers(["AAPL,GOOG", "MSFT"])
        ['AAPL', 'GOOG', 'MSFT']
        >>> normalize_tickers(["AAPL", "AAPL,GOOG"])
        ['AAPL', 'GOOG']
    """
    seen = set()
    result = []
    for arg in ticker_args:
        for ticker in arg.split(","):
            ticker = ticker.strip().upper()
            if ticker and ticker not in seen:
                seen.add(ticker)
                result.append(ticker)
    return result


def clear_screen() -> None:
    """Clear terminal screen (Windows / Unix compatible)."""
    os.system("cls" if os.name == "nt" else "clear")


def set_console_title(title: str) -> None:
    """Set the console window title (Windows only).

    Args:
        title: Title to set for the console window
    """
    if os.name == "nt":
        os.system(f"title {title}")


def run_for_ticker(
    ticker_symbol: str,
    output_format: str = "text",
    language: str = "en"
) -> bool:
    """Run stock screening for a single ticker.

    Args:
        ticker_symbol: Stock ticker symbol to screen
        output_format: Output format ('text', 'json', 'csv', or 'claude')
        language: Output language ('en' or 'es') for Claude format

    Returns:
        True if successful, False if an error occurred
    """
    ticker_symbol = ticker_symbol.strip().upper()
    if not ticker_symbol:
        print("No ticker entered; skipping.", file=sys.stderr)
        return False

    try:
        logger.info(f"Starting screening for {ticker_symbol}")

        # Fetch stock info from Yahoo Finance
        stock_info = fetch_stock_info(ticker_symbol)

        if stock_info is None:
            print(
                f"Error: Unable to retrieve data for {ticker_symbol}",
                file=sys.stderr
            )
            logger.error(f"Failed to fetch stock info for {ticker_symbol}")
            return False

        # Determine ADR status
        yahoo_adr_check = is_adr_yahoo(stock_info)
        stock_info.is_adr = determine_adr_status(ticker_symbol, yahoo_adr_check)

        # Get directors
        stock_info.directors = get_directors(
            ticker_symbol,
            max_count=DISPLAY_CONFIG.directors_max_count
        )

        # Analyze risks
        risk_analysis = analyze_stock_risks(stock_info)

        # Fetch VIX index
        vix_value = fetch_vix()

        # Format and display results
        formatter = get_formatter(output_format, language=language)
        output = formatter.format(
            stock_info,
            risk_analysis,
            RED_FLAGS.min_free_float,
            vix_value
        )
        print(output)

        logger.info(f"Successfully completed screening for {ticker_symbol}")
        return True

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        logger.info("User cancelled operation")
        return False

    except Exception as e:
        print(f"Error retrieving data for {ticker_symbol}: {e}", file=sys.stderr)
        logger.exception(f"Unexpected error screening {ticker_symbol}")
        return False


def fetch_ticker_data(ticker_symbol: str) -> TickerResult:
    """Fetch and analyze data for a single ticker.

    This is a thread-safe function that can be called in parallel.

    Args:
        ticker_symbol: Stock ticker symbol to process

    Returns:
        TickerResult with either stock_info/risk_analysis or error
    """
    ticker_symbol = ticker_symbol.strip().upper()
    if not ticker_symbol:
        return TickerResult(ticker=ticker_symbol, error="Empty ticker symbol")

    try:
        logger.info(f"Fetching data for {ticker_symbol}")

        # Fetch stock info from Yahoo Finance
        stock_info = fetch_stock_info(ticker_symbol)

        if stock_info is None:
            logger.error(f"Failed to fetch stock info for {ticker_symbol}")
            return TickerResult(
                ticker=ticker_symbol,
                error="Unable to retrieve data"
            )

        # Determine ADR status
        yahoo_adr_check = is_adr_yahoo(stock_info)
        stock_info.is_adr = determine_adr_status(ticker_symbol, yahoo_adr_check)

        # Get directors
        stock_info.directors = get_directors(
            ticker_symbol,
            max_count=DISPLAY_CONFIG.directors_max_count
        )

        # Analyze risks
        risk_analysis = analyze_stock_risks(stock_info)

        logger.info(f"Successfully fetched data for {ticker_symbol}")
        return TickerResult(
            ticker=ticker_symbol,
            stock_info=stock_info,
            risk_analysis=risk_analysis
        )

    except Exception as e:
        logger.exception(f"Error fetching data for {ticker_symbol}")
        return TickerResult(ticker=ticker_symbol, error=str(e))


def run_for_tickers(
    tickers: List[str],
    output_format: str = "text",
    language: str = "en",
    max_workers: int = 3
) -> bool:
    """Run stock screening for multiple tickers.

    Uses sequential processing with delays to avoid Yahoo Finance rate limiting.

    Args:
        tickers: List of stock ticker symbols to screen
        output_format: Output format ('text', 'json', 'csv', or 'claude')
        language: Output language ('en' or 'es') for Claude format
        max_workers: Maximum number of concurrent fetches (reduced to avoid rate limits)

    Returns:
        True if at least one ticker succeeded, False if all failed
    """
    if not tickers:
        print("No tickers provided.", file=sys.stderr)
        return False

    # For single ticker, use original behavior for backward compatibility
    if len(tickers) == 1:
        return run_for_ticker(tickers[0], output_format=output_format, language=language)

    try:
        logger.info(f"Starting batch screening for {len(tickers)} tickers")

        # Fetch VIX once before processing tickers
        vix_value = fetch_vix()

        # Process tickers sequentially with delay to avoid rate limiting
        # This is more reliable than parallel fetching for Yahoo Finance
        results: List[TickerResult] = []

        for i, ticker in enumerate(tickers):
            # Add delay between requests to avoid rate limiting (except first)
            if i > 0:
                time.sleep(1.5)  # 1.5 second delay between requests

            result = fetch_ticker_data(ticker)
            results.append(result)

            # Log progress for large batches
            if len(tickers) > 3:
                logger.info(f"Processed {i + 1}/{len(tickers)}: {ticker}")

        # Format and display results using batch formatter
        formatter = get_formatter(output_format, language=language)
        output = formatter.format_batch(
            results,
            RED_FLAGS.min_free_float,
            vix_value
        )
        print(output)

        # Return True if at least one ticker succeeded
        successes = sum(1 for r in results if r.success)
        logger.info(
            f"Batch screening complete: {successes}/{len(tickers)} succeeded"
        )
        return successes > 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.", file=sys.stderr)
        logger.info("User cancelled batch operation")
        return False

    except Exception as e:
        print(f"Error during batch processing: {e}", file=sys.stderr)
        logger.exception("Unexpected error in batch screening")
        return False


def run_cli() -> None:
    """Run the interactive command-line interface.

    Continuously prompts for ticker symbols and displays stock information
    until the user presses Enter without input.
    """
    # Set console title
    set_console_title("Super Signal")

    logger.info("Starting CLI interface")

    try:
        while True:
            ticker_symbol = input(
                f"{ANSIColor.CYAN.value}\nEnter Stock Symbol "
                f"(or press Enter to quit):{ANSIColor.RESET.value}"
            ).strip()

            if not ticker_symbol:
                print(f"{ANSIColor.CYAN.value}Exiting.{ANSIColor.RESET.value}")
                logger.info("User exited CLI")
                break

            clear_screen()
            run_for_ticker(ticker_symbol)

    except KeyboardInterrupt:
        print(f"\n{ANSIColor.CYAN.value}Exiting.{ANSIColor.RESET.value}")
        logger.info("CLI interrupted by user")

    except Exception as e:
        print(f"\nFatal error: {e}", file=sys.stderr)
        logger.exception("Fatal error in CLI")
        sys.exit(1)
