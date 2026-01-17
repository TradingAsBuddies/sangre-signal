"""FinViz data fetcher module.

This module handles web scraping from FinViz.com for additional stock information
including ADR detection and key executives/directors.
"""

import logging
from typing import Optional, List
import requests
from bs4 import BeautifulSoup
import yfinance as yf

from ..config import NETWORK_CONFIG
from ..cache import get_cache

logger = logging.getLogger("super_signal.fetchers.finviz")


def is_adr_finviz(ticker: str) -> Optional[bool]:
    """Check if a stock is an ADR by scraping FinViz.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')

    Returns:
        True if ADR, False if not, None if unable to determine.
    """
    ticker = ticker.upper()
    cache = get_cache()

    # Check cache first
    cached_result, cache_hit = cache.get_adr_status(ticker)
    if cache_hit:
        return cached_result

    url = f"https://finviz.com/quote.ashx?t={ticker}"
    headers = {"User-Agent": NETWORK_CONFIG.user_agent}

    try:
        logger.info(f"Checking ADR status on FinViz for {ticker}")
        resp = requests.get(
            url,
            headers=headers,
            timeout=NETWORK_CONFIG.request_timeout
        )

        if resp.status_code != 200:
            logger.warning(f"FinViz returned status {resp.status_code} for {ticker}")
            return None

        soup = BeautifulSoup(resp.text, "html.parser")

        # Check header table
        header_table = soup.find("table", class_="fullview-title")
        text_chunks = []
        if header_table:
            text_chunks.append(header_table.get_text(" ", strip=True))

        # Check snapshot table
        snap_table = soup.find("table", class_="snapshot-table2")
        if snap_table:
            text_chunks.append(snap_table.get_text(" ", strip=True))

        combined = " ".join(text_chunks).lower()
        if not combined:
            logger.debug(f"No content found in FinViz tables for {ticker}")
            return None

        # Check for ADR indicators
        if " adr" in combined or "american depositary" in combined:
            logger.info(f"{ticker} identified as ADR on FinViz")
            cache.set_adr_status(ticker, True)
            return True

        cache.set_adr_status(ticker, False)
        return False

    except requests.RequestException as e:
        logger.warning(f"Network error checking FinViz for {ticker}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error parsing FinViz data for {ticker}: {e}")
        return None


def get_directors(ticker: str, max_count: int = 10) -> List[str]:
    """Get key executives and directors from yfinance API.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')
        max_count: Maximum number of directors to return (default: 10)

    Returns:
        List of director names and titles, or empty list if unavailable.
    """
    ticker = ticker.upper()
    cache = get_cache()

    # Check cache first
    cached_directors, cache_hit = cache.get_directors(ticker)
    if cache_hit:
        # Apply max_count limit to cached result
        return cached_directors[:max_count] if cached_directors else []

    try:
        logger.info(f"Fetching directors for {ticker} via yfinance API")
        stock = yf.Ticker(ticker)
        info = stock.info

        # Get company officers from yfinance
        officers = info.get("companyOfficers", [])
        if not officers:
            logger.debug(f"No company officers found for {ticker}")
            cache.set_directors(ticker, [])
            return []

        # Extract directors (those with "director" in title)
        directors = []
        for officer in officers:
            name = officer.get("name", "")
            title = officer.get("title", "")

            if not name or not title:
                continue

            # Only include entries with "director" in the title
            if "director" in title.lower():
                directors.append(f"{name} - {title}")

            if len(directors) >= max_count:
                break

        logger.info(f"Found {len(directors)} director(s) for {ticker}")

        # Cache the result
        cache.set_directors(ticker, directors)

        return directors

    except Exception as e:
        logger.warning(f"Error fetching directors for {ticker}: {e}")
        return []


def determine_adr_status(ticker: str, yahoo_check: bool) -> bool:
    """Determine ADR status using both FinViz and Yahoo Finance checks.

    FinViz check takes precedence over Yahoo Finance heuristics.

    Args:
        ticker: Stock ticker symbol
        yahoo_check: Result from Yahoo Finance ADR check

    Returns:
        True if determined to be an ADR, False otherwise.
    """
    finviz_result = is_adr_finviz(ticker)

    # FinViz has definitive answer
    if finviz_result is True:
        return True

    # FinViz says it's not an ADR
    if finviz_result is False:
        return False

    # FinViz couldn't determine, fall back to Yahoo check
    return yahoo_check
