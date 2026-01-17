# Sangre Signal - Advanced Stock Analysis Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A comprehensive stock analysis application that analyzes stocks for various risk factors including country of origin, ADR status, low float, and more. Now with **Claude AI-powered analysis** for plain-language risk explanations in English and Spanish.

## Features

- Real-time stock data from Yahoo Finance
- Multi-factor risk analysis (country, ADR status, float, headquarters)
- **Claude AI-powered analysis** with plain-language risk explanations
- **Bilingual support** - English and Spanish (Mexican) output
- Portfolio-level analysis for multiple stocks
- Multiple output formats: text, JSON, CSV, and Claude AI
- Colorful terminal output with ANSI colors
- Automatic logging to file
- Modular, extensible architecture

## Installation

### From GitHub

```bash
# Clone the repository
git clone https://github.com/TradingAsBuddies/sangre-signal.git
cd sangre-signal

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate

# Activate (Linux/Mac)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Configuration

Copy the example environment file and add your Anthropic API key:

```bash
cp .env.example .env
```

Edit `.env` and add your API key:
```
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

Get your API key at: https://console.anthropic.com/

## Quick Start

```bash
# Basic stock analysis (text format)
python -m super_signal -t AAPL

# Multiple stocks
python -m super_signal -t AAPL,TSLA,MSFT

# Interactive mode
python -m super_signal
```

## Claude AI Analysis

The Claude AI format provides natural language explanations of stock risks that anyone can understand.

### English Analysis

```bash
python -m super_signal -t AAPL -f claude
```

### Spanish Analysis (Mexican Spanish)

```bash
python -m super_signal -t AAPL -f claude -L es
```

### Portfolio Analysis

When analyzing multiple stocks with Claude, you get individual analyses plus a consolidated portfolio summary:

```bash
python -m super_signal -t AAPL,TSLA,BABA -f claude
```

This provides:
- Individual risk analysis for each stock
- Plain-language explanations of what each risk means
- Actionable investment insights
- Portfolio-level risk distribution summary
- Common risk factors across holdings

### Example Output

```
============================================================
  AAPL ANALYSIS (Powered by Claude AI)
============================================================

# Apple Inc. (AAPL) Stock Analysis

## Company Overview
Apple Inc. is the world's largest technology company...

## RISK ASSESSMENT: LOW RISK

Apple presents a LOW RISK investment profile based on current
market data. The company shows strong institutional backing,
minimal short interest, and manageable debt levels...

## KEY METRICS
- Market Cap: $3.78 trillion
- Current Price: $255.53
- Institutional Ownership: 64.82%
...

## BOTTOM LINE
Apple represents a low-risk investment opportunity for retail
investors seeking exposure to a proven technology leader...
============================================================
```

## Output Formats

```bash
# Text - colored terminal output (default)
python -m super_signal -t AAPL -f text

# JSON - machine-readable format
python -m super_signal -t AAPL -f json

# CSV - spreadsheet format
python -m super_signal -t AAPL -f csv

# Claude - AI-powered analysis
python -m super_signal -t AAPL -f claude

# Claude in Spanish
python -m super_signal -t AAPL -f claude -L es
```

## Risk Factors Detected

The screener analyzes stocks for the following risk factors:

- **Non-US Country of Origin** - Companies headquartered outside the US
- **High-Risk Countries** - RU, CN, IR (configurable)
- **Tax Haven Headquarters** - Cayman Islands, BVI, etc.
- **ADR Status** - American Depositary Receipts
- **Low Float** - Less than 3M freely tradable shares

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Required for Claude AI analysis
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### Risk Thresholds

Edit `super_signal/config.py` to customize risk detection:

```python
RED_FLAGS = RiskThresholds(
    risky_countries=["RU", "CN", "IR", "KP"],  # Add countries
    risky_headquarters_keywords=["Cayman", "BVI", "Bermuda"],
    min_free_float=5_000_000,  # Adjust float threshold
)
```

## Project Structure

```
sangre-signal/
├── .env.example              # Environment template
├── requirements.txt          # Dependencies
├── super_signal/
│   ├── __init__.py
│   ├── __main__.py           # Entry point
│   ├── main.py               # CLI argument parsing
│   ├── cli.py                # Command-line interface
│   ├── config.py             # Configuration (loads .env)
│   ├── models.py             # Data classes
│   ├── fetchers/
│   │   ├── yahoo_finance.py  # Yahoo Finance API
│   │   └── finviz.py         # FinViz scraping
│   ├── analyzers/
│   │   └── risk_analyzer.py  # Risk detection
│   └── formatters/
│       ├── base.py           # Formatter base class
│       ├── text_formatter.py # Colored terminal output
│       ├── json_formatter.py # JSON output
│       ├── csv_formatter.py  # CSV output
│       └── claude_formatter.py # Claude AI analysis
└── tests/
```

## Requirements

- Python 3.10 or higher
- Internet connection
- Anthropic API key (for Claude AI features)

### Dependencies

- yfinance - Yahoo Finance data
- requests - HTTP requests
- beautifulsoup4 - Web scraping
- lxml - HTML parsing
- anthropic - Claude AI API
- python-dotenv - Environment variable management

## Troubleshooting

### Claude Analysis Shows Fallback Message

If you see "AI analysis unavailable - ANTHROPIC_API_KEY not set":

1. Make sure you have a `.env` file in the project root
2. Verify your API key is correct
3. Check that python-dotenv is installed: `pip install python-dotenv`

### No Data for Ticker

- Verify the ticker symbol is correct
- Check your internet connection
- Yahoo Finance may be temporarily unavailable

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Built with [yfinance](https://github.com/ranaroussi/yfinance) for Yahoo Finance data
- Web scraping powered by [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- AI analysis powered by [Claude](https://www.anthropic.com/claude) from Anthropic
- Developed with assistance from [Claude Code](https://claude.ai/code)
