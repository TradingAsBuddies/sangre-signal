"""Main entry point for Super Signal.

This module sets up logging and launches the appropriate interface
(CLI for now, with future support for GUI).
"""

import sys
import argparse

from . import __version__
from .config import setup_logging
from .cli import run_cli


def parse_arguments():
    """Parse command-line arguments.

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Super Signal - Advanced stock analysis with risk factor detection"
    )

    parser.add_argument(
        "--version",
        "-V",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    parser.add_argument(
        "--ticker",
        "-t",
        action="append",
        dest="tickers",
        metavar="TICKER",
        help="Ticker symbol(s) to screen. Can be specified multiple times "
             "(-t AAPL -t GOOG) or comma-separated (-t AAPL,GOOG)"
    )

    parser.add_argument(
        "--format",
        "-f",
        choices=["text", "json", "csv", "claude"],
        default="text",
        help="Output format: text (colored terminal), json, csv, or claude "
             "(AI-powered analysis with risk explanations) (default: text)"
    )

    parser.add_argument(
        "--language",
        "-L",
        choices=["en", "es"],
        default="en",
        help="Output language for Claude format: en (English) or es (Spanish) (default: en)"
    )

    parser.add_argument(
        "--log-level",
        "-l",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Set logging level (default: INFO)"
    )

    parser.add_argument(
        "--status",
        action="store_true",
        help="Show rate limit and cache status, then exit"
    )

    parser.add_argument(
        "--clear-cache",
        action="store_true",
        help="Clear the cache and exit"
    )

    return parser.parse_args()


def show_status():
    """Display rate limit and cache status."""
    from .cache import get_cache

    cache = get_cache()
    status = cache.get_rate_limit_status()

    print("=== Rate Limit Status ===")
    print(f"Requests made (last hour): {status['requests_made']}/{status['max_requests']}")
    print(f"Requests remaining: {status['requests_remaining']}")

    if status['is_limited']:
        reset_min = status['reset_in_seconds'] / 60 if status['reset_in_seconds'] else 0
        print(f"Status: RATE LIMITED (resets in {reset_min:.1f} minutes)")
    else:
        print("Status: OK")

    print(f"\n=== Cache Info ===")
    print(f"Cache location: {cache.db_path}")
    print(f"Cache TTL: {cache.ttl / 3600:.1f} hours")


def main():
    """Main application entry point."""
    # Parse command-line arguments
    args = parse_arguments()

    # Set up logging
    setup_logging()

    # Handle status and clear-cache commands
    if args.status:
        show_status()
        sys.exit(0)

    if args.clear_cache:
        from .cache import get_cache
        cache = get_cache()
        cache.clear_all()
        print("Cache cleared successfully.")
        sys.exit(0)

    # Launch CLI interface
    try:
        if args.tickers:
            # Ticker mode (single or multiple)
            from .cli import run_for_tickers, normalize_tickers
            tickers = normalize_tickers(args.tickers)
            success = run_for_tickers(
                tickers,
                output_format=args.format,
                language=args.language
            )
            sys.exit(0 if success else 1)
        else:
            # Interactive mode (always uses text format)
            run_cli()
            sys.exit(0)

    except KeyboardInterrupt:
        print("\nInterrupted by user")
        sys.exit(0)

    except Exception as e:
        print(f"Fatal error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
