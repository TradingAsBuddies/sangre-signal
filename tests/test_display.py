"""Tests for the display formatting module."""

import pytest

from super_signal.formatters.display import (
    calculate_relative_volume,
    format_relative_volume,
    format_vix,
    format_number,
    format_percent,
)
from super_signal.config import ANSIColor


class TestCalculateRelativeVolume:
    """Tests for relative volume calculation."""

    def test_calculate_rvol_normal(self):
        """Test normal RVOL calculation."""
        rvol = calculate_relative_volume(5000000, 2500000)
        assert rvol == 2.0

    def test_calculate_rvol_below_average(self):
        """Test RVOL below average."""
        rvol = calculate_relative_volume(1000000, 2500000)
        assert rvol == 0.4

    def test_calculate_rvol_equal_to_average(self):
        """Test RVOL equal to average."""
        rvol = calculate_relative_volume(2500000, 2500000)
        assert rvol == 1.0

    def test_calculate_rvol_none_current_volume(self):
        """Test RVOL with None current volume."""
        rvol = calculate_relative_volume(None, 2500000)
        assert rvol is None

    def test_calculate_rvol_none_avg_volume(self):
        """Test RVOL with None average volume."""
        rvol = calculate_relative_volume(5000000, None)
        assert rvol is None

    def test_calculate_rvol_zero_avg_volume(self):
        """Test RVOL with zero average volume (division by zero protection)."""
        rvol = calculate_relative_volume(5000000, 0)
        assert rvol is None

    def test_calculate_rvol_both_none(self):
        """Test RVOL with both values None."""
        rvol = calculate_relative_volume(None, None)
        assert rvol is None

    def test_calculate_rvol_with_integers(self):
        """Test RVOL calculation with integer inputs."""
        rvol = calculate_relative_volume(3000000, 1500000)
        assert rvol == 2.0

    def test_calculate_rvol_with_floats(self):
        """Test RVOL calculation with float inputs."""
        rvol = calculate_relative_volume(3500000.5, 1000000.0)
        assert rvol == pytest.approx(3.5000005)


class TestFormatRelativeVolume:
    """Tests for relative volume formatting."""

    def test_format_rvol_none(self):
        """Test formatting None RVOL."""
        result = format_relative_volume(None)
        assert result == ""

    def test_format_rvol_normal(self):
        """Test formatting normal RVOL (no color)."""
        result = format_relative_volume(1.0)
        assert result == "1.00x"
        assert ANSIColor.LIGHT_GREEN.value not in result
        assert ANSIColor.YELLOW.value not in result

    def test_format_rvol_high_volume_green(self):
        """Test formatting high RVOL (green color)."""
        result = format_relative_volume(2.0)
        assert "2.00x" in result
        assert ANSIColor.LIGHT_GREEN.value in result
        assert ANSIColor.RESET.value in result

    def test_format_rvol_threshold_high(self):
        """Test formatting RVOL at high threshold (1.5x)."""
        result = format_relative_volume(1.5)
        assert "1.50x" in result
        assert ANSIColor.LIGHT_GREEN.value in result

    def test_format_rvol_just_below_high_threshold(self):
        """Test formatting RVOL just below high threshold."""
        result = format_relative_volume(1.49)
        assert result == "1.49x"
        assert ANSIColor.LIGHT_GREEN.value not in result

    def test_format_rvol_low_volume_yellow(self):
        """Test formatting low RVOL (yellow color)."""
        result = format_relative_volume(0.3)
        assert "0.30x" in result
        assert ANSIColor.YELLOW.value in result
        assert ANSIColor.RESET.value in result

    def test_format_rvol_threshold_low(self):
        """Test formatting RVOL at low threshold (0.5x)."""
        result = format_relative_volume(0.5)
        assert result == "0.50x"
        assert ANSIColor.YELLOW.value not in result

    def test_format_rvol_just_below_low_threshold(self):
        """Test formatting RVOL just below low threshold."""
        result = format_relative_volume(0.49)
        assert "0.49x" in result
        assert ANSIColor.YELLOW.value in result

    def test_format_rvol_very_high(self):
        """Test formatting very high RVOL."""
        result = format_relative_volume(10.5)
        assert "10.50x" in result
        assert ANSIColor.LIGHT_GREEN.value in result

    def test_format_rvol_very_low(self):
        """Test formatting very low RVOL."""
        result = format_relative_volume(0.1)
        assert "0.10x" in result
        assert ANSIColor.YELLOW.value in result


class TestFormatVix:
    """Tests for VIX formatting."""

    def test_format_vix_none(self):
        """Test formatting None VIX."""
        result = format_vix(None)
        assert result == ""

    def test_format_vix_low_volatility_green(self):
        """Test formatting low VIX (green color)."""
        result = format_vix(12.5)
        assert "12.50" in result
        assert ANSIColor.LIGHT_GREEN.value in result
        assert ANSIColor.RESET.value in result

    def test_format_vix_at_low_threshold(self):
        """Test formatting VIX at low threshold (15)."""
        result = format_vix(15.0)
        assert "15.00" in result
        assert ANSIColor.YELLOW.value in result

    def test_format_vix_moderate_volatility_yellow(self):
        """Test formatting moderate VIX (yellow color)."""
        result = format_vix(20.0)
        assert "20.00" in result
        assert ANSIColor.YELLOW.value in result
        assert ANSIColor.RESET.value in result

    def test_format_vix_at_high_threshold(self):
        """Test formatting VIX at high threshold (25)."""
        result = format_vix(25.0)
        assert "25.00" in result
        assert ANSIColor.RED.value in result

    def test_format_vix_high_volatility_red(self):
        """Test formatting high VIX (red color)."""
        result = format_vix(35.0)
        assert "35.00" in result
        assert ANSIColor.RED.value in result
        assert ANSIColor.RESET.value in result

    def test_format_vix_very_low(self):
        """Test formatting very low VIX."""
        result = format_vix(9.5)
        assert "9.50" in result
        assert ANSIColor.LIGHT_GREEN.value in result

    def test_format_vix_extreme_high(self):
        """Test formatting extreme VIX (market panic)."""
        result = format_vix(80.0)
        assert "80.00" in result
        assert ANSIColor.RED.value in result

    def test_format_vix_just_below_moderate(self):
        """Test formatting VIX just below moderate threshold."""
        result = format_vix(14.99)
        assert "14.99" in result
        assert ANSIColor.LIGHT_GREEN.value in result

    def test_format_vix_just_below_high(self):
        """Test formatting VIX just below high threshold."""
        result = format_vix(24.99)
        assert "24.99" in result
        assert ANSIColor.YELLOW.value in result


class TestFormatNumber:
    """Tests for number formatting."""

    def test_format_number_billions(self):
        """Test formatting billions."""
        assert format_number(3000000000) == "3.00B"

    def test_format_number_millions(self):
        """Test formatting millions."""
        assert format_number(5500000) == "5.50M"

    def test_format_number_thousands(self):
        """Test formatting thousands."""
        assert format_number(2500) == "2.50K"

    def test_format_number_small(self):
        """Test formatting small numbers."""
        assert format_number(500) == "500"

    def test_format_number_none(self):
        """Test formatting None."""
        assert format_number(None) == ""

    def test_format_number_negative(self):
        """Test formatting negative numbers."""
        assert format_number(-1500000) == "-1.50M"


class TestFormatPercent:
    """Tests for percentage formatting."""

    def test_format_percent_positive(self):
        """Test formatting positive percentage."""
        assert format_percent(12.345) == "12.35%"

    def test_format_percent_negative(self):
        """Test formatting negative percentage."""
        assert format_percent(-5.5) == "-5.50%"

    def test_format_percent_zero(self):
        """Test formatting zero percentage."""
        assert format_percent(0) == "0.00%"

    def test_format_percent_none(self):
        """Test formatting None."""
        assert format_percent(None) == ""
