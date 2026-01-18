"""Yahoo Finance data fetcher module.

This module handles all interactions with the Yahoo Finance API through yfinance,
including fetching stock information, cash flow data, and split history.
"""

import logging
import datetime
import numbers
from typing import Optional
import yfinance as yf

from ..models import StockInfo
from ..config import US_COUNTRY_VARIATIONS
from ..cache import get_cache

logger = logging.getLogger("sangre_signal.fetchers.yahoo_finance")


def fetch_stock_info(ticker: str) -> Optional[StockInfo]:
    """Fetch comprehensive stock information from Yahoo Finance.

    Args:
        ticker: Stock ticker symbol (e.g., 'AAPL')

    Returns:
        StockInfo object with all available data, or None if fetch fails.
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
        stock = yf.Ticker(ticker)
        info = stock.info

        if not info or len(info) == 0:
            logger.error(f"No data returned for ticker {ticker}")
            return None

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

    except Exception as e:
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


def fetch_vix() -> Optional[float]:
    """Fetch the current VIX (CBOE Volatility Index) value.

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
        vix = yf.Ticker("^VIX")
        info = vix.info

        if not info:
            logger.warning("No VIX data returned")
            return None

        price = info.get("regularMarketPrice") or info.get("price")

        if price is not None:
            # Cache it as a minimal StockInfo
            vix_info = StockInfo(ticker="^VIX", regular_market_price=price)
            cache.set_stock_info(vix_info)
            logger.info(f"VIX fetched: {price}")

        return price

    except Exception as e:
        logger.warning(f"Error fetching VIX: {e}")
        return None
