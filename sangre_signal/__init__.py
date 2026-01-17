"""Super Signal - Advanced Stock Analysis Tool.

A comprehensive stock analysis application that analyzes stocks for various
risk factors including country of origin, ADR status, low float, and more.

Modules:
    models: Data classes for stock information and risk analysis
    config: Configuration settings and constants
    fetchers: Data fetching from Yahoo Finance and FinViz
    analyzers: Risk analysis logic
    formatters: Display formatting and output
    cli: Command-line interface
    main: Application entry point
"""

__version__ = "2.5.0"
__author__ = "Super Signal Team"

from .models import StockInfo, RiskFlag, RiskAnalysis, RiskSeverity
from .config import RED_FLAGS, setup_logging
from .cli import run_cli

__all__ = [
    "StockInfo",
    "RiskFlag",
    "RiskAnalysis",
    "RiskSeverity",
    "RED_FLAGS",
    "setup_logging",
    "run_cli",
]
