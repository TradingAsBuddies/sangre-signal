"""Display formatting module for stock information.

This module provides functions for formatting and displaying stock information
with ANSI color codes for terminal output.
"""

import datetime
from typing import List, Optional
from zoneinfo import ZoneInfo

from ..models import StockInfo, RiskAnalysis
from ..config import ANSIColor, DISPLAY_CONFIG, FIELD_LABELS, US_COUNTRY_VARIATIONS


def format_number(n: Optional[float]) -> str:
    """Format a number with magnitude suffixes (K, M, B).

    Args:
        n: Number to format

    Returns:
        Formatted string (e.g., "1.23M", "4.56B")
    """
    if isinstance(n, (int, float)):
        if abs(n) >= 1_000_000_000:
            return f"{n/1_000_000_000:.2f}B"
        if abs(n) >= 1_000_000:
            return f"{n/1_000_000:.2f}M"
        if abs(n) >= 1_000:
            return f"{n/1_000:.2f}K"
        return str(n)
    return str(n) if n is not None else ""


def format_percent(v: Optional[float]) -> str:
    """Format a number as a percentage.

    Args:
        v: Number to format

    Returns:
        Formatted percentage string (e.g., "12.34%")
    """
    if isinstance(v, (int, float)):
        return f"{v:.2f}%"
    return str(v) if v is not None else ""


def calculate_relative_volume(
    current_volume: Optional[float],
    avg_volume: Optional[float]
) -> Optional[float]:
    """Calculate relative volume (RVOL).

    Args:
        current_volume: Current day's trading volume
        avg_volume: Average volume (typically 10-day)

    Returns:
        Relative volume ratio, or None if cannot calculate
    """
    if (isinstance(current_volume, (int, float)) and
            isinstance(avg_volume, (int, float)) and
            avg_volume > 0):
        return current_volume / avg_volume
    return None


def format_relative_volume(rvol: Optional[float]) -> str:
    """Format relative volume with color coding.

    Args:
        rvol: Relative volume ratio

    Returns:
        Formatted and colorized RVOL string
    """
    if rvol is None:
        return ""

    rvol_str = f"{rvol:.2f}x"

    # Color code: green for high volume (>1.5x), yellow for low (<0.5x)
    if rvol >= 1.5:
        return f"{ANSIColor.LIGHT_GREEN.value}{rvol_str}{ANSIColor.RESET.value}"
    elif rvol < 0.5:
        return f"{ANSIColor.YELLOW.value}{rvol_str}{ANSIColor.RESET.value}"

    return rvol_str


def format_vix(vix_value: Optional[float]) -> str:
    """Format VIX value with color coding based on volatility level.

    Args:
        vix_value: Current VIX index value

    Returns:
        Formatted and colorized VIX string

    Color coding:
        - Green: VIX < 15 (low volatility)
        - Yellow: 15 <= VIX < 25 (moderate volatility)
        - Red: VIX >= 25 (high volatility)
    """
    if vix_value is None:
        return ""

    vix_str = f"{vix_value:.2f}"

    if vix_value >= 25:
        return f"{ANSIColor.RED.value}{vix_str}{ANSIColor.RESET.value}"
    elif vix_value >= 15:
        return f"{ANSIColor.YELLOW.value}{vix_str}{ANSIColor.RESET.value}"
    else:
        return f"{ANSIColor.LIGHT_GREEN.value}{vix_str}{ANSIColor.RESET.value}"


def colorize_country(country: str) -> str:
    """Colorize country name (red if non-US).

    Args:
        country: Country name

    Returns:
        Colorized country string
    """
    if not country:
        return ""

    if country.lower() not in US_COUNTRY_VARIATIONS:
        return f"{ANSIColor.RED.value}{country}{ANSIColor.RESET.value}"

    return country


def colorize_headquarters(hq: str) -> str:
    """Colorize headquarters location (yellow if non-US).

    Args:
        hq: Headquarters address string

    Returns:
        Colorized headquarters string
    """
    if not hq:
        return ""

    hq_lower = hq.lower()
    if not any(us in hq_lower for us in US_COUNTRY_VARIATIONS):
        return f"{ANSIColor.YELLOW.value}{hq}{ANSIColor.RESET.value}"

    return hq


def colorize_adr_status(is_adr: bool) -> str:
    """Format and colorize ADR status.

    Args:
        is_adr: Whether the stock is an ADR

    Returns:
        Formatted ADR status string
    """
    if is_adr:
        status = "Is ADR - YES"
        return f"{ANSIColor.RED.value}{status}{ANSIColor.RESET.value}"
    return "No"


def colorize_float(float_shares: Optional[float], threshold: int) -> str:
    """Format and colorize float shares (red if below threshold).

    Args:
        float_shares: Float shares value
        threshold: Minimum float threshold

    Returns:
        Formatted and colorized float string
    """
    float_str = format_number(float_shares)

    if isinstance(float_shares, (int, float)) and float_shares < threshold:
        return f"{ANSIColor.RED.value}{float_str}{ANSIColor.RESET.value}"

    return float_str


def format_header(ticker: str) -> str:
    """Format the header section with ticker symbol.

    Args:
        ticker: Stock ticker symbol

    Returns:
        Formatted header string
    """
    width = DISPLAY_CONFIG.summary_width
    line = DISPLAY_CONFIG.horizontal_line * width

    title = f" - {ANSIColor.NEGATIVE.value}{ticker}{ANSIColor.RESET.value} - "
    centered_title = title.center(width)

    return f"\n{line}\n{centered_title}\n{line}"


def format_risk_flags(risk_analysis: RiskAnalysis) -> str:
    """Format the risk flag summary line.

    Args:
        risk_analysis: Risk analysis results

    Returns:
        Formatted risk flag string
    """
    if risk_analysis.has_risks:
        flag_text = f"{ANSIColor.RED.value}!  POTENTIAL HIGH RISKS !{ANSIColor.RESET.value}"
    else:
        flag_text = f"{ANSIColor.BRIGHT_BLUE.value}No Major Flags Detected{ANSIColor.RESET.value}"

    return f"{FIELD_LABELS['flag_risk']:20}: {flag_text}"


def format_basic_info(stock_info: StockInfo) -> str:
    """Format basic company information section.

    Args:
        stock_info: Stock information

    Returns:
        Formatted basic info string
    """
    lines = []

    lines.append(f"{FIELD_LABELS['company']:20}: {stock_info.get_display_name()}")
    lines.append(
        f"{ANSIColor.BRIGHT_BLUE.value}{FIELD_LABELS['ticker']:20}: "
        f"{stock_info.ticker}{ANSIColor.RESET.value}"
    )
    lines.append(f"{FIELD_LABELS['exchange']:20}: {stock_info.exchange or ''}")
    lines.append(
        f"{FIELD_LABELS['adr']:20}: {colorize_adr_status(stock_info.is_adr)}"
    )
    lines.append(
        f"{FIELD_LABELS['country']:20}: {colorize_country(stock_info.get_country())}"
    )

    return "\n".join(lines)


def format_headquarters(stock_info: StockInfo) -> str:
    """Format headquarters address with line wrapping.

    Args:
        stock_info: Stock information

    Returns:
        Formatted headquarters string
    """
    hq = stock_info.get_headquarters()
    visible_hq = colorize_headquarters(hq)
    max_width = DISPLAY_CONFIG.max_field_width

    if len(visible_hq) > max_width:
        break_pos = visible_hq.rfind(" ", 0, max_width + 1)
        if break_pos == -1:
            break_pos = max_width
        first_line = visible_hq[:break_pos].rstrip()
        remainder = visible_hq[break_pos:].lstrip()

        result = f"{FIELD_LABELS['headquarters']:20}: {first_line}"
        if remainder:
            result += f"\n{' ' * 24}{remainder}"
        return result
    else:
        return f"{FIELD_LABELS['headquarters']:20}: {visible_hq}"


def format_ownership_info(stock_info: StockInfo) -> str:
    """Format ownership and market cap information.

    Args:
        stock_info: Stock information

    Returns:
        Formatted ownership info string
    """
    lines = []

    market_cap = format_number(stock_info.market_cap)
    lines.append(f"{FIELD_LABELS['market_cap']:20}: {market_cap}")

    insider_pct = stock_info.held_percent_insiders
    insider_display = (
        f"{insider_pct * 100:.2f}%"
        if isinstance(insider_pct, (int, float))
        else ""
    )
    lines.append(f"{FIELD_LABELS['insider_ownership']:20}: {insider_display}")

    inst_pct = stock_info.held_percent_institutions
    inst_display = (
        f"{inst_pct * 100:.2f}%"
        if isinstance(inst_pct, (int, float))
        else ""
    )
    lines.append(f"{FIELD_LABELS['institutional_ownership']:20}: {inst_display}")

    return "\n".join(lines)


def format_price_info(stock_info: StockInfo) -> str:
    """Format price information (market, premarket, postmarket).

    Args:
        stock_info: Stock information

    Returns:
        Formatted price info string
    """
    lines = []

    # Regular market price
    price = stock_info.get_price()
    if isinstance(price, (int, float)):
        price_display = f"${price:.2f}"
    else:
        price_display = f"${price}" if price else ""
    lines.append(f"{FIELD_LABELS['price_market']:20}: {price_display}")

    # Premarket price
    pre_price = stock_info.pre_market_price
    if isinstance(pre_price, (int, float)):
        pre_display = f"${pre_price:.2f}"
    else:
        pre_display = f"${pre_price}" if pre_price is not None else ""
    lines.append(f"{FIELD_LABELS['price_premarket']:20}: {pre_display}")

    # Postmarket price
    post_price = stock_info.post_market_price
    if isinstance(post_price, (int, float)):
        post_display = f"${post_price:.2f}"
    else:
        post_display = f"${post_price}" if post_price is not None else ""
    lines.append(f"{FIELD_LABELS['price_postmarket']:20}: {post_display}")

    # Last split
    lines.append(f"{FIELD_LABELS['last_split']:20}: {stock_info.last_split_display}")

    # 52-week high/low
    high_52w = stock_info.fifty_two_week_high
    low_52w = stock_info.fifty_two_week_low
    lines.append(f"{FIELD_LABELS['week_52_high']:20}: ${high_52w if high_52w else ''}")
    lines.append(f"{FIELD_LABELS['week_52_low']:20}: ${low_52w if low_52w else ''}")

    # Percent off 52-week high
    pct_off = stock_info.percent_off_52week_high()
    pct_display = format_percent(pct_off) if pct_off is not None else ""
    lines.append(f"{FIELD_LABELS['pct_off_high']:20}: {pct_display}")

    return "\n".join(lines)


def format_trading_info(stock_info: StockInfo, float_threshold: int) -> str:
    """Format trading-related information (volume, shares, float, short interest).

    Args:
        stock_info: Stock information
        float_threshold: Minimum float threshold for colorization

    Returns:
        Formatted trading info string
    """
    lines = []

    # Average volume with relative volume
    avg_vol = format_number(stock_info.average_volume_10days)
    rvol = calculate_relative_volume(
        stock_info.regular_market_volume,
        stock_info.average_volume_10days
    )
    rvol_str = format_relative_volume(rvol)
    if rvol_str:
        lines.append(f"{FIELD_LABELS['avg_volume_10d']:20}: {avg_vol} (RVOL: {rvol_str})")
    else:
        lines.append(f"{FIELD_LABELS['avg_volume_10d']:20}: {avg_vol}")

    shares_out = format_number(stock_info.shares_outstanding)
    lines.append(f"{FIELD_LABELS['shares_outstanding']:20}: {shares_out}")

    float_str = colorize_float(stock_info.float_shares, float_threshold)
    lines.append(f"{FIELD_LABELS['float']:20}: {float_str}")

    short_pct = stock_info.short_percent_of_float
    short_pct_display = (
        f"{short_pct * 100:.2f}%"
        if isinstance(short_pct, (int, float))
        else ""
    )
    lines.append(f"{FIELD_LABELS['short_pct_float']:20}: {short_pct_display}")

    short_ratio = stock_info.short_ratio
    short_ratio_display = (
        f"{short_ratio:.2f}"
        if isinstance(short_ratio, (int, float))
        else ""
    )
    lines.append(f"{FIELD_LABELS['short_ratio']:20}: {short_ratio_display}")

    return "\n".join(lines)


def format_financial_info(stock_info: StockInfo) -> str:
    """Format financial information (debt, cash flow).

    Args:
        stock_info: Stock information

    Returns:
        Formatted financial info string
    """
    lines = []

    debt_str = format_number(stock_info.total_debt)
    lines.append(f"{FIELD_LABELS['debt']:20}: {debt_str}")

    op_cash_flow = stock_info.operating_cash_flow
    if isinstance(op_cash_flow, (int, float)):
        cf_label = "Positive" if op_cash_flow >= 0 else "Negative"
        cf_str = f"{cf_label} ({format_number(op_cash_flow)})"
    else:
        cf_str = ""
    lines.append(f"{FIELD_LABELS['cash_flow']:20}: {cf_str}")

    return "\n".join(lines)


def format_company_info(stock_info: StockInfo) -> str:
    """Format company information (employees, website).

    Args:
        stock_info: Stock information

    Returns:
        Formatted company info string
    """
    lines = []

    employees = stock_info.full_time_employees or ""
    lines.append(f"{FIELD_LABELS['employees']:20}: {employees}")

    website = stock_info.website or ""
    lines.append(f"{FIELD_LABELS['website']:20}: {website}")

    return "\n".join(lines)


def format_timestamp() -> str:
    """Format current timestamp in EST.

    Returns:
        Formatted timestamp string
    """
    now_est = datetime.datetime.now(ZoneInfo("America/New_York"))
    now_str = now_est.strftime("%Y-%m-%d %I:%M:%S %p")
    return f"{FIELD_LABELS['timestamp']:20}: {now_str}"


def format_executives(directors: List[str]) -> str:
    """Format key executives section.

    Args:
        directors: List of director names and titles

    Returns:
        Formatted executives string
    """
    lines = ["Key Executives:"]

    if directors:
        for d in directors:
            lines.append(f" - {d}")
    else:
        lines.append(" - (none found)")

    return "\n".join(lines)


def format_risk_details(risk_analysis: RiskAnalysis) -> str:
    """Format detailed risk flags section.

    Args:
        risk_analysis: Risk analysis results

    Returns:
        Formatted risk details string
    """
    if not risk_analysis.has_risks:
        return ""

    lines = [
        f"{ANSIColor.UNDERLINE.value}RED FLAGS:{ANSIColor.RESET.value} - "
        f"{ANSIColor.NEGATIVE.value}{risk_analysis.ticker}{ANSIColor.RESET.value}"
    ]

    for flag in risk_analysis.flags:
        lines.append(f" [!] -> {flag.message}")

    return "\n".join(lines)


def print_stock_summary(
    stock_info: StockInfo,
    risk_analysis: RiskAnalysis,
    float_threshold: int,
    vix_value: Optional[float] = None
) -> None:
    """Print comprehensive stock summary with formatting and colors.

    Args:
        stock_info: Stock information
        risk_analysis: Risk analysis results
        float_threshold: Minimum float threshold for risk highlighting
        vix_value: Current VIX index value (optional)
    """
    print(format_header(stock_info.ticker))
    print(format_risk_flags(risk_analysis))
    print(format_basic_info(stock_info))
    print(format_headquarters(stock_info))
    print(format_ownership_info(stock_info))
    print(format_price_info(stock_info))
    print(format_trading_info(stock_info, float_threshold))
    print(format_financial_info(stock_info))
    print(format_company_info(stock_info))
    print(format_timestamp())
    if vix_value is not None:
        print(f"{FIELD_LABELS['vix']:20}: {format_vix(vix_value)}")
    print()
    print(format_executives(stock_info.directors))
    print(DISPLAY_CONFIG.horizontal_line * DISPLAY_CONFIG.summary_width)

    if risk_analysis.has_risks:
        print(format_risk_details(risk_analysis))
