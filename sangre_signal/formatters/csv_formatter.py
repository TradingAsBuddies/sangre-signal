"""CSV formatter for spreadsheet-compatible output.

This formatter produces CSV output with a header row and data row,
suitable for importing into spreadsheets and data analysis tools.
"""

import csv
import io
import datetime
from typing import Optional, List, Any, TYPE_CHECKING
from zoneinfo import ZoneInfo

from .base import BaseFormatter
from .display import calculate_relative_volume
from ..models import StockInfo, RiskAnalysis

if TYPE_CHECKING:
    from ..cli import TickerResult


class CsvFormatter(BaseFormatter):
    """Formatter that produces CSV output."""

    # Column definitions: (header, getter_function)
    COLUMNS: List[tuple] = [
        ("ticker", lambda s, r, v: s.ticker),
        ("company_name", lambda s, r, v: s.get_display_name()),
        ("exchange", lambda s, r, v: s.exchange),
        ("sector", lambda s, r, v: s.sector),
        ("industry", lambda s, r, v: s.industry),
        ("country", lambda s, r, v: s.get_country()),
        ("headquarters", lambda s, r, v: s.get_headquarters()),
        ("is_adr", lambda s, r, v: s.is_adr),
        ("market_cap", lambda s, r, v: s.market_cap),
        ("price_current", lambda s, r, v: s.regular_market_price),
        ("price_premarket", lambda s, r, v: s.pre_market_price),
        ("price_postmarket", lambda s, r, v: s.post_market_price),
        ("week_52_high", lambda s, r, v: s.fifty_two_week_high),
        ("week_52_low", lambda s, r, v: s.fifty_two_week_low),
        ("percent_off_52w_high", lambda s, r, v: s.percent_off_52week_high()),
        ("last_split", lambda s, r, v: s.last_split_display or ""),
        ("shares_outstanding", lambda s, r, v: s.shares_outstanding),
        ("float_shares", lambda s, r, v: s.float_shares),
        ("volume_current", lambda s, r, v: s.regular_market_volume),
        ("volume_avg_10day", lambda s, r, v: s.average_volume_10days),
        ("relative_volume", lambda s, r, v: CsvFormatter._calc_rvol(s)),
        ("insider_ownership_pct", lambda s, r, v: CsvFormatter._to_pct(
            s.held_percent_insiders
        )),
        ("institutional_ownership_pct", lambda s, r, v: CsvFormatter._to_pct(
            s.held_percent_institutions
        )),
        ("short_pct_of_float", lambda s, r, v: CsvFormatter._to_pct(
            s.short_percent_of_float
        )),
        ("short_ratio_days", lambda s, r, v: s.short_ratio),
        ("total_debt", lambda s, r, v: s.total_debt),
        ("debt_to_equity", lambda s, r, v: s.debt_to_equity),
        ("operating_cash_flow", lambda s, r, v: s.operating_cash_flow),
        ("employees", lambda s, r, v: s.full_time_employees),
        ("website", lambda s, r, v: s.website),
        ("has_risk_flags", lambda s, r, v: r.has_risks),
        ("risk_flag_count", lambda s, r, v: len(r.flags)),
        ("risk_flags", lambda s, r, v: "; ".join(f.message for f in r.flags)),
        ("vix", lambda s, r, v: v),
        ("timestamp", lambda s, r, v: CsvFormatter._get_timestamp()),
    ]

    def format(
        self,
        stock_info: StockInfo,
        risk_analysis: RiskAnalysis,
        float_threshold: int,
        vix_value: Optional[float] = None
    ) -> str:
        """Format stock data as CSV.

        Args:
            stock_info: Stock information data
            risk_analysis: Risk analysis results
            float_threshold: Minimum float threshold (unused in CSV)
            vix_value: Current VIX index value (optional)

        Returns:
            CSV string with header row and data row
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header row
        headers = [col[0] for col in self.COLUMNS]
        writer.writerow(headers)

        # Write data row
        values = [
            self._format_value(col[1](stock_info, risk_analysis, vix_value))
            for col in self.COLUMNS
        ]
        writer.writerow(values)

        return output.getvalue().rstrip('\r\n')

    @staticmethod
    def _format_value(value: Any) -> str:
        """Format a value for CSV output.

        Args:
            value: Value to format

        Returns:
            String representation suitable for CSV
        """
        if value is None:
            return ""
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, float):
            return f"{value:.4f}" if value != int(value) else str(int(value))
        return str(value)

    @staticmethod
    def _to_pct(value: Optional[float]) -> Optional[float]:
        """Convert decimal to percentage.

        Args:
            value: Decimal value (e.g., 0.15)

        Returns:
            Percentage value (e.g., 15.0), or None if input is None
        """
        if value is not None:
            return round(value * 100, 2)
        return None

    @staticmethod
    def _calc_rvol(stock_info: StockInfo) -> Optional[float]:
        """Calculate relative volume.

        Args:
            stock_info: Stock information

        Returns:
            Relative volume ratio, or None
        """
        rvol = calculate_relative_volume(
            stock_info.regular_market_volume,
            stock_info.average_volume_10days
        )
        return round(rvol, 2) if rvol else None

    @staticmethod
    def _get_timestamp() -> str:
        """Get current timestamp in EST.

        Returns:
            ISO format timestamp string
        """
        now_est = datetime.datetime.now(ZoneInfo("America/New_York"))
        return now_est.isoformat()

    def format_batch(
        self,
        results: List["TickerResult"],
        float_threshold: int,
        vix_value: Optional[float] = None
    ) -> str:
        """Format multiple ticker results as CSV with single header and N rows.

        Args:
            results: List of TickerResult objects
            float_threshold: Minimum float threshold (unused in CSV)
            vix_value: Current VIX index value (optional)

        Returns:
            CSV string with header row and one data row per ticker
        """
        output = io.StringIO()
        writer = csv.writer(output)

        # Write header row with error column added at the end
        headers = [col[0] for col in self.COLUMNS] + ["error"]
        writer.writerow(headers)

        # Write data rows
        for result in results:
            if result.success:
                values = [
                    self._format_value(col[1](
                        result.stock_info, result.risk_analysis, vix_value
                    ))
                    for col in self.COLUMNS
                ]
                values.append("")  # No error
            else:
                # For failed tickers, fill with ticker and empty values
                values = [result.ticker]  # ticker column
                values.extend([""] * (len(self.COLUMNS) - 1))  # other columns
                values.append(result.error or "Unknown error")  # error column
            writer.writerow(values)

        return output.getvalue().rstrip('\r\n')
