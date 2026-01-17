Name:           sangre-signal
Version:        2.0.0
Release:        1%{?dist}
Summary:        Advanced stock analysis tool with Claude AI-powered risk explanations

License:        MIT
URL:            https://github.com/TradingAsBuddies/sangre-signal
Source0:        %{url}/archive/v%{version}/%{name}-%{version}.tar.gz

BuildArch:      noarch
BuildRequires:  python3-devel
BuildRequires:  python3-setuptools
BuildRequires:  python3-pip
BuildRequires:  python3-wheel

# Runtime dependencies
Requires:       python3-yfinance >= 0.2.28
Requires:       python3-requests >= 2.31.0
Requires:       python3-beautifulsoup4 >= 4.12.0
Requires:       python3-lxml >= 4.9.0
Requires:       python3-tzdata >= 2023.3
Requires:       python3-anthropic >= 0.40.0

%description
Sangre Signal is a comprehensive stock analysis application that analyzes
stocks for various risk factors including country of origin, ADR status,
low float, and more. Features Claude AI-powered explanations in English
and Mexican Spanish.

Features:
- Real-time stock data from Yahoo Finance
- Claude AI-powered risk analysis and explanations
- Bilingual support (English and Mexican Spanish)
- Multi-factor risk analysis
- Colorful terminal output with ANSI colors
- Persistent caching with rate limiting
- Automatic logging to file
- Modular, extensible architecture
- Ready for future GUI development

%prep
%autosetup -n %{name}-%{version}

%build
%py3_build

%install
%py3_install

%check
# Run basic syntax checks
%{python3} -m py_compile %{buildroot}%{python3_sitelib}/sangre_signal/*.py

%files
%license LICENSE
%doc README.md CONTRIBUTING.md
%{python3_sitelib}/sangre_signal/
%{python3_sitelib}/sangre_signal-%{version}-py%{python3_version}.egg-info/
%{_bindir}/sangre-signal

%changelog
* Fri Jan 17 2025 David Duncan <tradingasbuddies@davidduncan.org> - 2.0.0-1
- Renamed from super-signal to sangre-signal
- Added Claude AI-powered risk explanations
- Bilingual support (English and Mexican Spanish)
- Persistent file-based caching with SQLite
- Local rate limiting for Yahoo Finance API
- Retry logic with exponential backoff
- New CLI options: --status, --clear-cache, --language
- Improved Windows console encoding for Spanish characters

* Mon Dec 30 2024 David Duncan <tradingasbuddies@davidduncan.org> - 1.0.0-1
- Initial Fedora package
- Modular Python package for advanced stock analysis
- Risk factor detection (country, ADR, float, headquarters)
- Real-time data from Yahoo Finance and FinViz
- CLI interface with colorful terminal output
- Comprehensive logging and error handling
- Type hints and docstrings throughout
- Ready for GUI development
