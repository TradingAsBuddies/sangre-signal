Name:           super-signal
Version:        2.0.0
Release:        1%{?dist}
Summary:        Advanced stock analysis tool with risk factor detection

License:        MIT
URL:            https://github.com/TradingAsBuddies/super-signal
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

%description
Super Signal is a comprehensive stock analysis application that analyzes
stocks for various risk factors including country of origin, ADR status,
low float, and more.

Features:
- Real-time stock data from Yahoo Finance
- Multi-factor risk analysis
- Colorful terminal output with ANSI colors
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
%{python3} -m py_compile %{buildroot}%{python3_sitelib}/super_signal/*.py

%files
%license LICENSE
%doc README.md CONTRIBUTING.md
%{python3_sitelib}/super_signal/
%{python3_sitelib}/super_signal-%{version}-py%{python3_version}.egg-info/
%{_bindir}/super-signal

%changelog
* Mon Dec 30 2024 David Duncan <tradingasbuddies@davidduncan.org> - 2.0.0-1
- Initial Fedora package
- Modular Python package for advanced stock analysis
- Risk factor detection (country, ADR, float, headquarters)
- Real-time data from Yahoo Finance and FinViz
- CLI interface with colorful terminal output
- Comprehensive logging and error handling
- Type hints and docstrings throughout
- Ready for GUI development
