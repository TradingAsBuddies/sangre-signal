"""Tests for configuration module."""

import sys
from unittest.mock import Mock, patch
import pytest
from super_signal.config import (
    _get_safe_horizontal_line,
    DisplayConfig,
    DISPLAY_CONFIG,
)


class TestGetSafeHorizontalLine:
    """Tests for _get_safe_horizontal_line function."""

    def test_returns_unicode_when_utf8_supported(self):
        """Test that Unicode box-drawing character is returned for UTF-8."""
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.encoding = 'utf-8'
            result = _get_safe_horizontal_line()
            assert result == "─"

    def test_returns_ascii_when_latin1_encoding(self):
        """Test that ASCII hyphen is returned for latin-1 encoding."""
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.encoding = 'latin-1'
            result = _get_safe_horizontal_line()
            assert result == "-"

    def test_returns_ascii_when_ascii_encoding(self):
        """Test that ASCII hyphen is returned for ASCII encoding."""
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.encoding = 'ascii'
            result = _get_safe_horizontal_line()
            assert result == "-"

    def test_returns_ascii_when_encoding_is_none(self):
        """Test fallback to ASCII when stdout encoding is None."""
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.encoding = None
            result = _get_safe_horizontal_line()
            assert result == "-"

    def test_returns_ascii_when_attribute_error(self):
        """Test fallback to ASCII when stdout doesn't have encoding attribute."""
        with patch('sys.stdout', spec=[]):  # spec=[] means no attributes
            result = _get_safe_horizontal_line()
            assert result == "-"

    def test_returns_ascii_when_unknown_encoding(self):
        """Test fallback to ASCII for unknown encodings."""
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.encoding = 'unknown-encoding-xyz'
            result = _get_safe_horizontal_line()
            # Should fallback to ASCII due to LookupError
            assert result == "-"


class TestDisplayConfig:
    """Tests for DisplayConfig class."""

    def test_display_config_default_values(self):
        """Test that DisplayConfig has correct default values."""
        config = DisplayConfig()
        assert config.summary_width == 70
        assert config.label_width == 20
        assert config.max_field_width == 40
        assert config.directors_max_count == 10
        # horizontal_line depends on terminal encoding
        assert config.horizontal_line in ["─", "-"]

    def test_display_config_with_utf8(self):
        """Test DisplayConfig uses Unicode with UTF-8 encoding."""
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.encoding = 'utf-8'
            config = DisplayConfig()
            assert config.horizontal_line == "─"

    def test_display_config_with_latin1(self):
        """Test DisplayConfig falls back to ASCII with latin-1 encoding."""
        with patch('sys.stdout') as mock_stdout:
            mock_stdout.encoding = 'latin-1'
            config = DisplayConfig()
            assert config.horizontal_line == "-"

    def test_display_config_custom_values(self):
        """Test that DisplayConfig accepts custom values."""
        config = DisplayConfig(
            summary_width=80,
            label_width=25,
            horizontal_line="*",
        )
        assert config.summary_width == 80
        assert config.label_width == 25
        assert config.horizontal_line == "*"

    def test_global_display_config_exists(self):
        """Test that global DISPLAY_CONFIG is properly initialized."""
        assert isinstance(DISPLAY_CONFIG, DisplayConfig)
        assert DISPLAY_CONFIG.summary_width == 70
        assert DISPLAY_CONFIG.horizontal_line in ["─", "-"]


class TestEncodingFallbackIntegration:
    """Integration tests for encoding fallback behavior."""

    def test_unicode_character_can_be_encoded_utf8(self):
        """Test that Unicode box-drawing char encodes in UTF-8."""
        char = "─"
        encoded = char.encode('utf-8')
        assert encoded == b'\xe2\x94\x80'  # UTF-8 bytes for ─

    def test_unicode_character_cannot_be_encoded_latin1(self):
        """Test that Unicode box-drawing char fails in latin-1."""
        char = "─"
        with pytest.raises(UnicodeEncodeError):
            char.encode('latin-1')

    def test_ascii_hyphen_can_be_encoded_anywhere(self):
        """Test that ASCII hyphen works in all encodings."""
        char = "-"
        # These should all succeed
        char.encode('utf-8')
        char.encode('latin-1')
        char.encode('ascii')
        assert True  # If we get here, all encodings worked

    def test_display_config_horizontal_line_is_encodable(self):
        """Test that horizontal_line in DisplayConfig is always encodable."""
        config = DisplayConfig()
        encoding = sys.stdout.encoding or 'ascii'

        # This should not raise an exception
        try:
            config.horizontal_line.encode(encoding)
            success = True
        except UnicodeEncodeError:
            success = False

        assert success, f"horizontal_line '{config.horizontal_line}' cannot be encoded in {encoding}"
