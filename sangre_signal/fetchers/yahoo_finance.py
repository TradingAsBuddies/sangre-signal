"""Yahoo Finance data fetcher module.

This module handles all interactions with the Yahoo Finance API through yfinance,
including fetching stock information, cash flow data, and split history.
"""

import logging
import datetime
import numbers
import time
import random
from typing import Optional, Callable, TypeVar
from functools import wraps
import yfinance as yf

from ..models import StockInfo
from ..config import US_COUNTRY_VARIATIONS
from ..cache import get_cache

logger = logging.getLogger("sangre_signal.fetchers.yahoo_finance")

T = TypeVar('T')


def retry_with_backoff(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 30.0,
    backoff_factor: float = 2.0
) -> Callable:
    """Decorator for retrying functions with exponential backoff.

    Handles rate limiting (429) and transient errors by retrying with
    increasing delays between attempts.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        backoff_factor: Multiplier for delay after each retry
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    error_str = str(e).lower()

                    # Check if it's a rate limit error
                    is_rate_limit = (
                        "429" in error_str or
                        "too many requests" in error_str or
                        "rate limit" in error_str
                    )

                    # Check if it's a transient error worth retrying
                    is_transient = (
                        is_rate_limit or
                        "timeout" in error_str or
                        "connection" in error_str or
                        "temporary" in error_str
                    )

                    if attempt < max_retries and is_transient:
                        # Calculate delay with jitter
                        delay = min(
                            base_delay * (backoff_factor ** attempt),
                            max_delay
                        )
                        # Add random jitter (0-25% of delay)
                        jitter = delay * random.uniform(0, 0.25)
                        total_delay = delay + jitter

                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed for "
                            f"{func.__name__}: {e}. Retrying in {total_delay:.1f}s..."
                        )
                        time.sleep(total_delay)
                    else:
                        # Not retryable or out of retries
                        break

            # Re-raise the last exception
            raise last_exception

        return wrapper
    return decorator


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""
    def __init__(self, reset_time: float = None):
        self.reset_time = reset_time
        if reset_time:
            super().__init__(f"Rate limit exceeded. Resets in {reset_time:.0f} seconds.")
        else:
            super().__init__("Rate limit exceeded.")


@retry_with_backoff(max_retries=3, base_delay=2.0, max_delay=30.0)
def _fetch_ticker_info(ticker: str) -> dict:
    """Internal function to fetch ticker info with retry logic.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Tuple of (info dict, yfinance Ticker object)

    Raises:
        RateLimitExceeded: When local rate limit is exceeded
        Exception: On failure after retries
    """
    cache = get_cache()

    # Check local rate limit before making request
    if cache.is_rate_limited():
        reset_time = cache.get_rate_limit_reset_time()
        raise RateLimitExceeded(reset_time)

    # Record the request
    cache.record_request()

    # Add a small delay to be respectful to the API
    time.sleep(0.3)

    stock = yf.Ticker(ticker)
    info = stock.info

    # Check for empty or error responses
    if not info or len(info) == 0:
        raise ValueError(f"No data returned for ticker {ticker}")

    # Check for rate limit indicators in the response
    if info.get("error"):
        raise Exception(f"Yahoo Finance error: {info.get('error')}")

    return info, stock


def fetch_stock_info(ticker: str) -> Optional[StockInfo]:
    """Fetch comprehensive stock information from Yahoo Finance.

    Includes automatic retry with exponential backoff for rate limiting
    and transient errors.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')

    Returns:
        StockInfo object with all available data, or None if fetch fails.

    Raises:
        None - errors are logged and None is returned.
    """
    ticker = ticker.upper()
    cache = get_cache()

    # Check cache first
    cached = cache.get_stock_info(ticker)
    if cached is not None:
        logger.debug(f"Cache hit for {ticker}")
        return cached

    try:
        logger.info(f"Fetching stock info for {ticker}")
        info, stock = _fetch_ticker_info(ticker)

        # Get operating cash flow
        op_cash_flow = get_operating_cash_flow(stock)

        # Get last split details
        last_split_display = get_last_split_details(stock, info)

        # Create StockInfo object
        stock_info = StockInfo(
            ticker=ticker.upper(),
            long_name=info.get("longName"),
            short_name=info.get("shortName"),
            country=info.get("country"),
            country_of_origin=info.get("countryOfOrigin"),
            address1=info.get("address1"),
            city=info.get("city"),
            state=info.get("state"),
            zip_code=info.get("zip"),
            exchange=info.get("exchange"),
            market=info.get("market"),
            sector=info.get("sector"),
            industry=info.get("industry"),
            market_cap=info.get("marketCap"),
            regular_market_price=info.get("regularMarketPrice") or info.get("price"),
            pre_market_price=info.get("preMarketPrice"),
            post_market_price=info.get("postMarketPrice"),
            fifty_two_week_high=info.get("fiftyTwoWeekHigh"),
            fifty_two_week_low=info.get("fiftyTwoWeekLow"),
            average_volume_10days=info.get("averageVolume10days"),
            regular_market_volume=info.get("regularMarketVolume") or info.get("volume"),
            shares_outstanding=info.get("sharesOutstanding"),
            float_shares=info.get("floatShares"),
            total_debt=info.get("totalDebt") or info.get("debtToEquity", 0),
            debt_to_equity=info.get("debtToEquity"),
            full_time_employees=info.get("fullTimeEmployees"),
            website=info.get("website"),
            short_percent_of_float=info.get("shortPercentOfFloat"),
            short_ratio=info.get("shortRatio"),
            held_percent_insiders=info.get("heldPercentInsiders"),
            held_percent_institutions=info.get("heldPercentInstitutions"),
            last_split_factor=info.get("lastSplitFactor"),
            last_split_date=info.get("lastSplitDate"),
            operating_cash_flow=op_cash_flow,
            last_split_display=last_split_display,
        )

        logger.info(f"Successfully fetched info for {ticker}")

        # Cache the result
        cache.set_stock_info(stock_info)

        return stock_info

    except RateLimitExceeded as e:
        logger.error(
            f"Local rate limit exceeded for {ticker}. {e}"
        )
        return None

    except Exception as e:
        error_str = str(e).lower()
        if "429" in error_str or "too many requests" in error_str:
            logger.error(
                f"Rate limited by Yahoo Finance for {ticker}. "
                "Try again in a few minutes or reduce request frequency."
            )
        else:
            logger.error(f"Error fetching stock info for {ticker}: {e}")
        return None


def is_adr_yahoo(stock_info: StockInfo) -> bool:
    """Determine if a stock is an ADR based on Yahoo Finance data.

    Checks country of origin, exchange, market, and name fields to identify
    American Depositary Receipts (foreign stocks traded on US exchanges).

    Args:
        stock_info: StockInfo object with Yahoo Finance data.

    Returns:
        True if the stock appears to be an ADR, False otherwise.
    """
    country = (stock_info.get_country() or "").lower()
    exchange = (stock_info.exchange or "").lower()
    market = (stock_info.market or "").lower()
    long_name = (stock_info.long_name or "").lower()
    short_name = (stock_info.short_name or "").lower()

    # Check if name explicitly mentions ADR
    text = " ".join([long_name, short_name])
    if " adr" in text or text.endswith("adr") or "american depositary" in text:
        return True

    # Check if foreign company on US exchange
    is_foreign = country not in US_COUNTRY_VARIATIONS and country != ""

    us_exchanges = ("nyse", "nasdaq", "ncm", "amex", "bats", "arca")
    us_markets = ("us", "us_market", "us_equity")
    is_us_exchange = any(ex in exchange for ex in us_exchanges)
    is_us_market = any(m in market for m in us_markets)

    return is_foreign and (is_us_exchange or is_us_market)


def get_operating_cash_flow(ticker_obj: yf.Ticker) -> Optional[float]:
    """Extract operating cash flow from the most recent period.

    Args:
        ticker_obj: yfinance Ticker object.

    Returns:
        Operating cash flow value, or None if unavailable.
    """
    try:
        cf = ticker_obj.cashflow
        if cf is None or cf.empty:
            logger.debug("No cash flow data available")
            return None

        # Try different possible field names
        if "Total Cash From Operating Activities" in cf.index:
            series = cf.loc["Total Cash From Operating Activities"]
        elif "totalCashFromOperatingActivities" in cf.index:
            series = cf.loc["totalCashFromOperatingActivities"]
        else:
            logger.debug("Operating cash flow field not found in cash flow data")
            return None

        latest = series.iloc[0]
        if isinstance(latest, numbers.Number):
            return float(latest)

        return None

    except Exception as e:
        logger.warning(f"Error retrieving operating cash flow: {e}")
        return None


def interpret_split_factor(factor_str: Optional[str],
                          ratio_float: Optional[float] = None) -> str:
    """Interpret and format stock split information.

    Args:
        factor_str: Split factor string (e.g., "2:1")
        ratio_float: Split ratio as float (e.g., 2.0)

    Returns:
        Formatted split description (e.g., "2:1, split") or empty string.
    """
    num = None
    den = None

    # Try to parse factor string
    if factor_str:
        parts = factor_str.split(":")
        if len(parts) == 2 and all(p.strip().isdigit() for p in parts):
            num = int(parts[0])
            den = int(parts[1]) if int(parts[1]) != 0 else 1

    # Fall back to ratio float
    if num is None or den is None:
        if isinstance(ratio_float, (int, float)) and ratio_float != 0:
            if ratio_float >= 1:
                num = int(round(ratio_float))
                den = 1
            else:
                num = 1
                den = int(round(1 / ratio_float))
        else:
            return ""

    kind = "split" if num >= den else "reverse split"
    return f"{num}:{den}, {kind}"


def get_last_split_details(ticker_obj: yf.Ticker, info: dict) -> str:
    """Get formatted last stock split details.

    Args:
        ticker_obj: yfinance Ticker object
        info: Stock info dictionary from yfinance

    Returns:
        Formatted split string (e.g., "2024-01-15 (2:1, split)") or empty string.
    """
    try:
        factor = info.get("lastSplitFactor")
        ts = info.get("lastSplitDate")

        date_str = ""
        if isinstance(ts, (int, float)) and ts > 0:
            dt = datetime.datetime.utcfromtimestamp(ts)
            date_str = dt.strftime("%Y-%m-%d")

        detail = interpret_split_factor(factor)

        if detail:
            if date_str:
                return f"{date_str} ({detail})"
            return detail

        # Try to get split history from ticker object
        splits = ticker_obj.splits
        if splits is not None and not splits.empty:
            last_date = splits.index[-1]
            last_ratio = splits.iloc[-1]
            detail = interpret_split_factor(None, last_ratio)
            if detail:
                return f"{last_date.date()} ({detail})"

    except Exception as e:
        logger.debug(f"Error retrieving split details: {e}")

    return ""


@retry_with_backoff(max_retries=2, base_delay=1.0, max_delay=10.0)
def _fetch_vix_info() -> dict:
    """Internal function to fetch VIX info with retry logic."""
    cache = get_cache()

    # Check local rate limit before making request
    if cache.is_rate_limited():
        reset_time = cache.get_rate_limit_reset_time()
        raise RateLimitExceeded(reset_time)

    # Record the request
    cache.record_request()

    # Add a small delay
    time.sleep(0.3)

    vix = yf.Ticker("^VIX")
    info = vix.info
    if not info:
        raise ValueError("No VIX data returned")
    return info


def fetch_vix() -> Optional[float]:
    """Fetch the current VIX (CBOE Volatility Index) value.

    Includes automatic retry with exponential backoff for rate limiting.

    Returns:
        Current VIX value, or None if fetch fails.
    """
    cache = get_cache()

    # Check cache first (VIX is cached under ticker "^VIX")
    cached = cache.get_stock_info("^VIX")
    if cached is not None and cached.regular_market_price is not None:
        logger.debug("Cache hit for VIX")
        return cached.regular_market_price

    try:
        logger.info("Fetching VIX index")
        info = _fetch_vix_info()

        price = info.get("regularMarketPrice") or info.get("price")

        if price is not None:
            # Cache it as a minimal StockInfo
            vix_info = StockInfo(ticker="^VIX", regular_market_price=price)
            cache.set_stock_info(vix_info)
            logger.info(f"VIX fetched: {price}")

        return price

    except Exception as e:
        error_str = str(e).lower()
        if "429" in error_str or "too many requests" in error_str:
            logger.warning("Rate limited fetching VIX, skipping")
        else:
            logger.warning(f"Error fetching VIX: {e}")
        return None
