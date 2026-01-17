"""JSON formatter for machine-readable output.

This formatter produces structured JSON output suitable for
scripts, APIs, and programmatic consumption.
"""

import json
import datetime
from typing import Optional, Any, Dict, List, TYPE_CHECKING
from zoneinfo import ZoneInfo

from .base import BaseFormatter
from .display import calculate_relative_volume
from ..models import StockInfo, RiskAnalysis

if TYPE_CHECKING:
    from ..cli import TickerResult


class JsonFormatter(BaseFormatter):
    """Formatter that produces JSON output."""

    def format(
        self,
        stock_info: StockInfo,
        risk_analysis: RiskAnalysis,
        float_threshold: int,
        vix_value: Optional[float] = None
    ) -> str:
        """Format stock data as JSON.

        Args:
            stock_info: Stock information data
            risk_analysis: Risk analysis results
            float_threshold: Minimum float threshold for risk highlighting
            vix_value: Current VIX index value (optional)

        Returns:
            JSON string with structured stock data
        """
        data = self._build_data_dict(stock_info, risk_analysis, vix_value)
        return json.dumps(data, indent=2)

    def _build_data_dict(
        self,
        stock_info: StockInfo,
        risk_analysis: RiskAnalysis,
        vix_value: Optional[float] = None
    ) -> Dict[str, Any]:
        """Build the data dictionary for a single stock.

        Args:
            stock_info: Stock information data
            risk_analysis: Risk analysis results
            vix_value: Current VIX index value (optional)

        Returns:
            Dictionary with structured stock data
        """
        now_est = datetime.datetime.now(ZoneInfo("America/New_York"))
        timestamp = now_est.isoformat()

        rvol = calculate_relative_volume(
            stock_info.regular_market_volume,
            stock_info.average_volume_10days
        )

        return {
            "ticker": stock_info.ticker,
            "success": True,
            "company": {
                "name": stock_info.get_display_name(),
                "short_name": stock_info.short_name,
                "exchange": stock_info.exchange,
                "sector": stock_info.sector,
                "industry": stock_info.industry,
                "website": stock_info.website,
                "employees": stock_info.full_time_employees,
            },
            "location": {
                "country": stock_info.get_country(),
                "headquarters": stock_info.get_headquarters(),
                "is_adr": stock_info.is_adr,
            },
            "price": {
                "current": stock_info.regular_market_price,
                "premarket": stock_info.pre_market_price,
                "postmarket": stock_info.post_market_price,
                "week_52_high": stock_info.fifty_two_week_high,
                "week_52_low": stock_info.fifty_two_week_low,
                "percent_off_52w_high": stock_info.percent_off_52week_high(),
                "last_split": stock_info.last_split_display or None,
            },
            "shares": {
                "outstanding": stock_info.shares_outstanding,
                "float": stock_info.float_shares,
                "market_cap": stock_info.market_cap,
            },
            "volume": {
                "current": stock_info.regular_market_volume,
                "average_10day": stock_info.average_volume_10days,
                "relative_volume": round(rvol, 2) if rvol else None,
            },
            "ownership": {
                "insider_percent": self._to_percent(
                    stock_info.held_percent_insiders
                ),
                "institutional_percent": self._to_percent(
                    stock_info.held_percent_institutions
                ),
            },
            "short_interest": {
                "percent_of_float": self._to_percent(
                    stock_info.short_percent_of_float
                ),
                "ratio_days": stock_info.short_ratio,
            },
            "financials": {
                "total_debt": stock_info.total_debt,
                "debt_to_equity": stock_info.debt_to_equity,
                "operating_cash_flow": stock_info.operating_cash_flow,
            },
            "executives": stock_info.directors,
            "risk_analysis": {
                "has_risks": risk_analysis.has_risks,
                "flags": [
                    {
                        "type": flag.flag_type,
                        "message": flag.message,
                        "severity": flag.severity.value,
                    }
                    for flag in risk_analysis.flags
                ],
            },
            "vix": vix_value,
            "timestamp": timestamp,
        }

    def format_batch(
        self,
        results: List["TickerResult"],
        float_threshold: int,
        vix_value: Optional[float] = None
    ) -> str:
        """Format multiple ticker results as a JSON wrapper object.

        Args:
            results: List of TickerResult objects
            float_threshold: Minimum float threshold for risk highlighting
            vix_value: Current VIX index value (optional)

        Returns:
            JSON string with wrapper object containing results array
        """
        now_est = datetime.datetime.now(ZoneInfo("America/New_York"))
        timestamp = now_est.isoformat()

        result_data = []
        successes = 0
        failures = 0

        for result in results:
            if result.success:
                data = self._build_data_dict(
                    result.stock_info,
                    result.risk_analysis,
                    vix_value
                )
                result_data.append(data)
                successes += 1
            else:
                result_data.append({
                    "ticker": result.ticker,
                    "success": False,
                    "error": result.error or "Unknown error"
                })
                failures += 1

        wrapper = {
            "timestamp": timestamp,
            "count": len(results),
            "successes": successes,
            "failures": failures,
            "vix": vix_value,
            "results": result_data
        }

        return json.dumps(wrapper, indent=2)

    @staticmethod
    def _to_percent(value: Optional[float]) -> Optional[float]:
        """Convert decimal to percentage.

        Args:
            value: Decimal value (e.g., 0.15)

        Returns:
            Percentage value (e.g., 15.0), or None if input is None
        """
        if value is not None:
            return round(value * 100, 2)
        return None
