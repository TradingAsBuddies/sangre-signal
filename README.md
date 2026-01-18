# Sangre Signal - Advanced Stock Analysis Tool

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

A comprehensive stock analysis application that analyzes stocks for various risk factors including country of origin, ADR status, low float, and more. Now with **AI-powered analysis** using Claude or Perplexity for plain-language risk explanations in English and Spanish.

## Features

- Real-time stock data from Yahoo Finance
- Multi-factor risk analysis (country, ADR status, float, headquarters)
- **AI-powered analysis** with Claude or Perplexity
- **Bilingual support** - English and Spanish (Mexican) output
- Portfolio-level analysis for multiple stocks
- Multiple output formats: text, JSON, CSV, Claude AI, and Perplexity AI
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

Copy the example environment file and add your API keys:

```bash
cp .env.example .env
```

Edit `.env` and add your API key(s):
```bash
# For Claude AI analysis
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# For Perplexity AI analysis
PERPLEXITY_API_KEY=pplx-your-key-here
```

Get your API keys at:
- Claude: https://console.anthropic.com/
- Perplexity: https://www.perplexity.ai/settings/api

## Quick Start

```bash
# Basic stock analysis (text format)
python -m sangre_signal -t AAPL

# Multiple stocks
python -m sangre_signal -t AAPL,TSLA,MSFT

# Interactive mode
python -m sangre_signal
```

## AI-Powered Analysis

Both Claude and Perplexity AI formats provide natural language explanations of stock risks that anyone can understand.

### Claude AI Analysis

```bash
# English
python -m sangre_signal -t AAPL -f claude

# Spanish (Mexican Spanish)
python -m sangre_signal -t AAPL -f claude -L es
```

### Perplexity AI Analysis

```bash
# English
python -m sangre_signal -t AAPL -f perplexity

# Spanish (Mexican Spanish)
python -m sangre_signal -t AAPL -f perplexity -L es
```

### Portfolio Analysis

When analyzing multiple stocks with either AI provider, you get individual analyses plus a consolidated portfolio summary:

```bash
# With Claude
python -m sangre_signal -t AAPL,TSLA,BABA -f claude

# With Perplexity
python -m sangre_signal -t AAPL,TSLA,BABA -f perplexity
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
python -m sangre_signal -t AAPL -f text

# JSON - machine-readable format
python -m sangre_signal -t AAPL -f json

# CSV - spreadsheet format
python -m sangre_signal -t AAPL -f csv

# Claude - AI-powered analysis
python -m sangre_signal -t AAPL -f claude

# Perplexity - AI-powered analysis
python -m sangre_signal -t AAPL -f perplexity

# AI formats in Spanish
python -m sangre_signal -t AAPL -f claude -L es
python -m sangre_signal -t AAPL -f perplexity -L es
```

## Cache and Rate Limiting

The tool includes built-in protections against Yahoo Finance rate limiting:

### Persistent Cache

Stock data is cached locally to minimize API requests:

- **Location:** `~/.cache/sangre-signal/stock_cache.db`
- **TTL:** 4 hours (stock data doesn't change frequently)
- **Persists across sessions** - previously fetched tickers load instantly

### Rate Limit Status

Check your current rate limit usage:

```bash
python -m sangre_signal --status
```

Example output:
```
=== Rate Limit Status ===
Requests made (last hour): 12/80
Requests remaining: 68
Status: OK

=== Cache Info ===
Cache location: /home/user/.cache/sangre-signal/stock_cache.db
Cache TTL: 4.0 hours
```

### Clear Cache

If you need fresh data or want to reset the cache:

```bash
python -m sangre_signal --clear-cache
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
# For Claude AI analysis
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here

# For Perplexity AI analysis
PERPLEXITY_API_KEY=pplx-your-key-here
```

### Risk Thresholds

Edit `sangre_signal/config.py` to customize risk detection:

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
├── sangre_signal/
│   ├── __init__.py
│   ├── __main__.py           # Entry point
│   ├── main.py               # CLI argument parsing
│   ├── cli.py                # Command-line interface
│   ├── config.py             # Configuration (loads .env)
│   ├── cache.py              # Persistent cache & rate limiting
│   ├── models.py             # Data classes
│   ├── fetchers/
│   │   ├── yahoo_finance.py  # Yahoo Finance API (with retry logic)
│   │   └── finviz.py         # FinViz scraping
│   ├── analyzers/
│   │   └── risk_analyzer.py  # Risk detection
│   └── formatters/
│       ├── base.py              # Formatter base class
│       ├── text_formatter.py    # Colored terminal output
│       ├── json_formatter.py    # JSON output
│       ├── csv_formatter.py     # CSV output
│       ├── claude_formatter.py  # Claude AI analysis
│       └── perplexity_formatter.py # Perplexity AI analysis
└── tests/
```

## Requirements

- Python 3.10 or higher
- Internet connection
- Anthropic API key (for Claude AI features) and/or Perplexity API key (for Perplexity AI features)

### Dependencies

- yfinance - Yahoo Finance data
- requests - HTTP requests
- beautifulsoup4 - Web scraping
- lxml - HTML parsing
- anthropic - Claude AI API
- openai - Perplexity AI API (OpenAI-compatible)
- python-dotenv - Environment variable management

## Troubleshooting

### Claude Analysis Shows Fallback Message

If you see "AI analysis unavailable - ANTHROPIC_API_KEY not set":

1. Make sure you have a `.env` file in the project root
2. Verify your API key is correct
3. Check that python-dotenv is installed: `pip install python-dotenv`

### Perplexity Analysis Shows Fallback Message

If you see "AI analysis unavailable - PERPLEXITY_API_KEY not set":

1. Make sure you have a `.env` file in the project root
2. Add your Perplexity API key: `PERPLEXITY_API_KEY=pplx-your-key-here`
3. Get your API key at: https://www.perplexity.ai/settings/api

### No Data for Ticker

- Verify the ticker symbol is correct
- Check your internet connection
- Yahoo Finance may be temporarily unavailable

### Rate Limited by Yahoo Finance (429 Error)

If you see "429 Too Many Requests" errors:

1. **Wait 15-60 minutes** - Yahoo Finance rate limits typically expire within an hour
2. **Check status**: `python -m sangre_signal --status`
3. **Use cached data** - Previously fetched tickers are cached for 4 hours
4. **Reduce batch sizes** - Analyze fewer stocks at once

The tool automatically:
- Limits requests to 80/hour
- Adds delays between requests
- Retries with exponential backoff
- Caches results to avoid repeat requests

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## Acknowledgments

- Built with [yfinance](https://github.com/ranaroussi/yfinance) for Yahoo Finance data
- Web scraping powered by [BeautifulSoup](https://www.crummy.com/software/BeautifulSoup/)
- AI analysis powered by [Claude](https://www.anthropic.com/claude) from Anthropic and [Perplexity AI](https://www.perplexity.ai/)
- Developed with assistance from [Claude Code](https://claude.ai/code)
