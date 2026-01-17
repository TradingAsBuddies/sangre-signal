"""Shared pytest fixtures for super-signal tests."""

import pytest
from sangre_signal.models import StockInfo, RiskFlag, RiskAnalysis, RiskSeverity
from sangre_signal.cache import clear_cache


@pytest.fixture(autouse=True)
def clear_cache_between_tests():
    """Clear the cache before and after each test to avoid test pollution."""
    clear_cache()
    yield
    clear_cache()


@pytest.fixture
def sample_us_stock():
    """Create a sample US stock with typical data."""
    return StockInfo(
        ticker="AAPL",
        long_name="Apple Inc.",
        short_name="Apple",
        country="United States",
        address1="One Apple Park Way",
        city="Cupertino",
        state="CA",
        zip_code="95014",
        exchange="NASDAQ",
        market="us_market",
        sector="Technology",
        industry="Consumer Electronics",
        market_cap=3000000000000,
        regular_market_price=180.50,
        fifty_two_week_high=200.00,
        fifty_two_week_low=140.00,
        shares_outstanding=16000000000,
        float_shares=16000000000,
        is_adr=False,
    )


@pytest.fixture
def sample_foreign_stock():
    """Create a sample foreign (non-US) stock."""
    return StockInfo(
        ticker="ASML",
        long_name="ASML Holding N.V.",
        short_name="ASML",
        country="Netherlands",
        city="Veldhoven",
        exchange="NASDAQ",
        market="us_market",
        float_shares=400000000,
        is_adr=False,
    )


@pytest.fixture
def sample_adr_stock():
    """Create a sample ADR stock."""
    return StockInfo(
        ticker="BABA",
        long_name="Alibaba Group Holding Limited ADR",
        short_name="Alibaba",
        country="China",
        city="Hangzhou",
        exchange="NYSE",
        market="us_market",
        float_shares=2500000000,
        is_adr=True,
    )


@pytest.fixture
def sample_low_float_stock():
    """Create a sample stock with low float."""
    return StockInfo(
        ticker="LOWF",
        long_name="Low Float Corp",
        country="United States",
        exchange="NASDAQ",
        float_shares=2000000,  # Below 3M threshold
    )


@pytest.fixture
def sample_risky_country_stock():
    """Create a sample stock from a risky country."""
    return StockInfo(
        ticker="RSKY",
        long_name="Risky Company Ltd",
        country="CN",
        city="Beijing",
        exchange="NYSE",
        float_shares=5000000,
    )


@pytest.fixture
def sample_cayman_hq_stock():
    """Create a sample stock with Cayman Islands HQ."""
    return StockInfo(
        ticker="CAYM",
        long_name="Offshore Holdings Inc",
        country="United States",
        address1="PO Box 123",
        city="George Town",
        state="Cayman Islands",
        exchange="NASDAQ",
        float_shares=10000000,
    )
