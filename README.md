# Super Signal - Advanced Stock Analysis Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![PyPI version](https://badge.fury.io/py/super-signal.svg)](https://badge.fury.io/py/super-signal)
[![COPR](https://copr.fedorainfracloud.org/coprs/tradingasbuddies/super-signal/package/super-signal/status_image/last_build.png)](https://copr.fedorainfracloud.org/coprs/tradingasbuddies/super-signal/)

A comprehensive stock analysis application that analyzes stocks for various risk factors including country of origin, ADR status, low float, and more.

## Features

- 📊 Real-time stock data from Yahoo Finance
- 🚩 Multi-factor risk analysis (country, ADR status, float, headquarters)
- 🎨 Colorful terminal output with ANSI colors
- 📝 Automatic logging to file
- 🔧 Modular, extensible architecture
- 🖥️ Ready for future GUI development

## Installation

### PyPI (All Platforms)

**Easiest method - works on Windows, macOS, and Linux:**

```bash
# Install from PyPI
pip install super-signal

# Run
super-signal --ticker AAPL
```

### From GitHub (Latest Development Version)

**Install directly from GitHub using pip:**

```bash
# Install latest from main branch
pip install git+https://github.com/TradingAsBuddies/super-signal.git

# Install a specific version/tag
pip install git+https://github.com/TradingAsBuddies/super-signal.git@v2.5.0

# Install a specific branch
pip install git+https://github.com/TradingAsBuddies/super-signal.git@feature/branch-name
```

### Fedora / RHEL / CentOS (RPM)

**Option 1: Install from COPR (Recommended)**

```bash
# Enable COPR repository
sudo dnf copr enable tradingasbuddies/super-signal

# Install
sudo dnf install super-signal

# Run
super-signal --ticker AAPL
```

**Option 2: Build from Source**

```bash
# Build RPM (see RPM_PACKAGING.md for details)
rpmbuild -ba super-signal.spec

# Install the built RPM
sudo dnf install ~/rpmbuild/RPMS/noarch/super-signal-2.0.0-1.*.noarch.rpm
```

See [RPM_PACKAGING.md](RPM_PACKAGING.md) for complete build instructions or [COPR_SETUP.md](COPR_SETUP.md) for publishing to COPR.

### From Source (Development)

**Windows:**

```batch
REM 1. Create virtual environment
python -m venv venv

REM 2. Activate virtual environment (WINDOWS)
venv\Scripts\activate

REM 3. Install the package
pip install .

REM 4. Run the application
super-signal
```

**Linux / macOS:**

```bash
# 1. Create virtual environment
python3 -m venv venv

# 2. Activate virtual environment (LINUX/MAC)
source venv/bin/activate

# 3. Install the package
pip install .

# 4. Run the application
super-signal
```

## Quick Start

After installation, you can run the stock screener in several ways:

### Windows Users - Three Options:

**Option 1: Direct path (always works)**
```batch
venv\Scripts\super-signal.exe --ticker AAPL
```

**Option 2: Python module syntax (recommended)**
```batch
python -m super_signal --ticker AAPL
```

**Option 3: Command name (if PATH is set)**
```batch
super-signal --ticker AAPL
```
*Note: If this doesn't work, deactivate and reactivate your venv, or use Option 1 or 2.*

### Linux/Mac Users:

```bash
super-signal --ticker AAPL
# or
python -m super_signal --ticker AAPL
```

### Interactive Mode (All Platforms)
```bash
python -m super_signal
```
Enter ticker symbols one at a time. Press Enter without input to exit.

### Windows Batch File
Double-click `super-signal.bat` or run:
```batch
super-signal.bat
```

## Usage Examples

```bash
# Interactive mode
super-signal

# Check a single stock
super-signal --ticker TSLA

# Check multiple stocks at once
super-signal -t AAPL -t GOOG -t MSFT
super-signal -t AAPL,GOOG,MSFT

# Output formats: text (default), json, csv
super-signal -t AAPL,GOOG -f json
super-signal -t AAPL,GOOG -f csv

# Change log level
super-signal --log-level DEBUG --ticker NVDA
```

## Risk Factors Detected

The screener analyzes stocks for the following risk factors:

- ⚠️ **Non-US Country of Origin** - Companies headquartered outside the US
- ⚠️ **High-Risk Countries** - RU, CN, IR (configurable)
- ⚠️ **Tax Haven Headquarters** - Cayman Islands, BVI, etc.
- ⚠️ **ADR Status** - American Depositary Receipts
- ⚠️ **Low Float** - Less than 3M freely tradable shares

## Output Information

For each ticker, the screener displays:

- Company name and basic info
- Exchange and market details
- Country of origin and headquarters
- Market prices (regular, pre-market, after-market)
- 52-week high/low and percentage off high
- Trading volume and shares outstanding
- Float shares (highlighted if low)
- Short interest metrics
- Insider and institutional ownership
- Debt and cash flow
- Key executives and directors
- **Risk flags** with severity indicators

## Configuration

Edit `super_signal/config.py` to customize:

- Risk detection thresholds
- Display formatting
- Logging settings
- Network timeout values
- ANSI color schemes

### Example: Adjusting Risk Thresholds

```python
# In super_signal/config.py
RED_FLAGS = RiskThresholds(
    risky_countries=["RU", "CN", "IR", "KP"],  # Add North Korea
    risky_headquarters_keywords=["Cayman", "BVI", "Bermuda"],
    min_free_float=5_000_000,  # Increase to 5M shares
)
```

## Project Structure

```
super_signal/
├── __init__.py              # Package initialization
├── __main__.py              # Module entry point
├── main.py                  # Main application logic & CLI arg parsing
├── cli.py                   # Interactive CLI interface
├── config.py                # Configuration & settings
├── models.py                # Data classes (StockInfo, RiskAnalysis)
├── fetchers/
│   ├── yahoo_finance.py     # Yahoo Finance API integration
│   └── finviz.py            # FinViz web scraping
├── analyzers/
│   └── risk_analyzer.py     # Risk detection logic
└── formatters/
    └── display.py           # Terminal output formatting
```

## Development

### Install in Development Mode (with dev tools)

**Windows:**
```batch
venv\Scripts\activate
pip install -e ".[dev]"
```

**Linux/Mac:**
```bash
source venv/bin/activate
pip install -e ".[dev]"
```

This installs the package in editable mode with development tools:
- `pytest` - Testing framework
- `black` - Code formatter
- `mypy` - Type checker
- `ruff` - Fast linter

### Adding New Features

- **New risk checks** → `super_signal/analyzers/risk_analyzer.py`
- **New data sources** → Create new file in `super_signal/fetchers/`
- **Display changes** → `super_signal/formatters/display.py`
- **Configuration** → `super_signal/config.py`

### Publishing to PyPI

Maintainers can publish new versions to PyPI. See [PYPI_DEPLOYMENT.md](PYPI_DEPLOYMENT.md) for complete instructions.

**Quick publish:**
```bash
# Update version in pyproject.toml and super_signal/__init__.py
# Commit changes and create tag
git add .
git commit -m "Release v2.1.0"
git tag v2.1.0
git push && git push --tags

# GitHub Actions will automatically build and publish to PyPI
```

Or manually:
```bash
python -m build
twine upload dist/*
```

## Logging

Logs are automatically written to `super_signal.log` in the current directory.

- **INFO**: Stock lookups, API calls
- **WARNING**: Network issues, parsing problems
- **ERROR**: Failed API calls, data unavailable

Change log level with `--log-level` flag or edit `config.py`.

## Future Enhancements

- [ ] Desktop GUI using tkinter or PyQt5
- [ ] Database storage for historical analysis
- [ ] Additional data sources (SEC filings, etc.)
- [x] ~~Portfolio screening (multiple tickers at once)~~ ✅ Added in v2.5.0
- [x] ~~Export to CSV/Excel~~ ✅ Added in v2.4.0
- [ ] Custom risk profiles
- [ ] Email/alert notifications

## Requirements

- Python 3.10 or higher
- Internet connection (for fetching stock data)
- Dependencies: yfinance, requests, beautifulsoup4, lxml, tzdata

## Troubleshooting

### "Command not found: super-signal"

Make sure your virtual environment is activated:

**Windows:** `venv\Scripts\activate`
**Linux/Mac:** `source venv/bin/activate`

### Import Errors

Reinstall the package:
```bash
pip install --force-reinstall .
```

### No Data for Ticker

- Verify the ticker symbol is correct
- Check your internet connection
- Yahoo Finance may be temporarily unavailable

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## Acknowledgments

- Built with [yfinance](https://github.com/ranaroussi/yfinance) for Yahoo Finance data
- Web scraping powered by [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- 🤖 Refactored with assistance from [Claude Code](https://claude.com/claude-code)
