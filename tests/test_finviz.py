"""Tests for FinViz fetcher module."""

import pytest
from unittest.mock import Mock, patch
from sangre_signal.fetchers.finviz import (
    is_adr_finviz,
    get_directors,
    determine_adr_status,
)


class TestIsAdrFinviz:
    """Tests for is_adr_finviz function."""

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_is_adr_finviz_detects_adr(self, mock_get):
        """Test ADR detection when ADR is found in content."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
            <html>
                <table class="fullview-title">
                    <tr><td>Alibaba Group ADR</td></tr>
                </table>
            </html>
        '''
        mock_get.return_value = mock_response

        result = is_adr_finviz('BABA')

        assert result is True
        mock_get.assert_called_once()

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_is_adr_finviz_american_depositary(self, mock_get):
        """Test ADR detection with 'American Depositary' text."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
            <html>
                <table class="snapshot-table2">
                    <tr><td>American Depositary Receipt</td></tr>
                </table>
            </html>
        '''
        mock_get.return_value = mock_response

        result = is_adr_finviz('TEST')

        assert result is True

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_is_adr_finviz_not_adr(self, mock_get):
        """Test when stock is not an ADR."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
            <html>
                <table class="fullview-title">
                    <tr><td>Apple Inc.</td></tr>
                </table>
                <table class="snapshot-table2">
                    <tr><td>Technology Company</td></tr>
                </table>
            </html>
        '''
        mock_get.return_value = mock_response

        result = is_adr_finviz('AAPL')

        assert result is False

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_is_adr_finviz_non_200_status(self, mock_get):
        """Test handling of non-200 HTTP status."""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        result = is_adr_finviz('INVALID')

        assert result is None

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_is_adr_finviz_no_tables(self, mock_get):
        """Test when expected tables are not found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><body>No tables here</body></html>'
        mock_get.return_value = mock_response

        result = is_adr_finviz('TEST')

        assert result is None

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_is_adr_finviz_network_error(self, mock_get):
        """Test handling of network errors."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")

        result = is_adr_finviz('TEST')

        assert result is None

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_is_adr_finviz_parsing_error(self, mock_get):
        """Test handling of parsing errors."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = Mock(side_effect=Exception("Parse error"))
        mock_get.return_value = mock_response

        result = is_adr_finviz('TEST')

        assert result is None

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_is_adr_finviz_case_insensitive(self, mock_get):
        """Test that ADR detection is case-insensitive."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
            <html>
                <table class="fullview-title">
                    <tr><td>Company Name adr</td></tr>
                </table>
            </html>
        '''
        mock_get.return_value = mock_response

        result = is_adr_finviz('TEST')

        assert result is True

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_is_adr_finviz_checks_both_tables(self, mock_get):
        """Test that both tables are checked."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
            <html>
                <table class="fullview-title">
                    <tr><td>Regular Company</td></tr>
                </table>
                <table class="snapshot-table2">
                    <tr><td>Contains ADR indicator</td></tr>
                </table>
            </html>
        '''
        mock_get.return_value = mock_response

        result = is_adr_finviz('TEST')

        assert result is True


class TestGetDirectors:
    """Tests for get_directors function."""

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_get_directors_success(self, mock_get):
        """Test successful director retrieval."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
            <html>
                <h2>Key Executives</h2>
                <table>
                    <tr>
                        <td>John Doe</td>
                        <td>Independent Director</td>
                        <td>Pay info</td>
                    </tr>
                    <tr>
                        <td>Jane Smith</td>
                        <td>Board Director</td>
                        <td>Pay info</td>
                    </tr>
                    <tr>
                        <td>Bob CEO</td>
                        <td>Chief Executive Officer</td>
                        <td>Pay info</td>
                    </tr>
                </table>
            </html>
        '''
        mock_get.return_value = mock_response

        result = get_directors('AAPL')

        assert len(result) == 2  # Only directors, not CEO
        assert 'John Doe – Independent Director' in result
        assert 'Jane Smith – Board Director' in result
        assert not any('CEO' in d for d in result)

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_get_directors_max_count(self, mock_get):
        """Test that max_count parameter limits results."""
        mock_response = Mock()
        mock_response.status_code = 200
        # Create HTML with many directors
        directors_html = '\n'.join([
            f'<tr><td>Director {i}</td><td>Board Director</td><td>Pay</td></tr>'
            for i in range(20)
        ])
        mock_response.text = f'''
            <html>
                <h2>Key Executives</h2>
                <table>{directors_html}</table>
            </html>
        '''
        mock_get.return_value = mock_response

        result = get_directors('TEST', max_count=5)

        assert len(result) == 5

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_get_directors_no_table_found(self, mock_get):
        """Test when Key Executives table is not found."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><body>No executives table</body></html>'
        mock_get.return_value = mock_response

        result = get_directors('TEST')

        assert result == []

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_get_directors_non_200_status(self, mock_get):
        """Test handling of non-200 HTTP status."""
        mock_response = Mock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        result = get_directors('TEST')

        assert result == []

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_get_directors_network_error(self, mock_get):
        """Test handling of network errors."""
        import requests
        mock_get.side_effect = requests.RequestException("Network error")

        result = get_directors('TEST')

        assert result == []

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_get_directors_parsing_error(self, mock_get):
        """Test handling of parsing errors."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><h2>Key Executives</h2><table>Invalid</table></html>'
        mock_get.return_value = mock_response

        result = get_directors('TEST')

        # Should handle gracefully, return empty list
        assert isinstance(result, list)

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_get_directors_case_insensitive_director_filter(self, mock_get):
        """Test that director filtering is case-insensitive."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
            <html>
                <h2>Key Executives</h2>
                <table>
                    <tr>
                        <td>Person 1</td>
                        <td>DIRECTOR</td>
                        <td>Pay</td>
                    </tr>
                    <tr>
                        <td>Person 2</td>
                        <td>Director</td>
                        <td>Pay</td>
                    </tr>
                    <tr>
                        <td>Person 3</td>
                        <td>director</td>
                        <td>Pay</td>
                    </tr>
                </table>
            </html>
        '''
        mock_get.return_value = mock_response

        result = get_directors('TEST')

        assert len(result) == 3

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_get_directors_filters_non_directors(self, mock_get):
        """Test that non-director executives are filtered out."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
            <html>
                <h2>Key Executives</h2>
                <table>
                    <tr>
                        <td>CEO Name</td>
                        <td>Chief Executive Officer</td>
                        <td>Pay</td>
                    </tr>
                    <tr>
                        <td>CFO Name</td>
                        <td>Chief Financial Officer</td>
                        <td>Pay</td>
                    </tr>
                    <tr>
                        <td>Director Name</td>
                        <td>Independent Director</td>
                        <td>Pay</td>
                    </tr>
                </table>
            </html>
        '''
        mock_get.return_value = mock_response

        result = get_directors('TEST')

        assert len(result) == 1
        assert 'Director Name' in result[0]

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_get_directors_handles_malformed_rows(self, mock_get):
        """Test handling of table rows with insufficient cells."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
            <html>
                <h2>Key Executives</h2>
                <table>
                    <tr>
                        <td>Only one cell</td>
                    </tr>
                    <tr>
                        <td>Valid Name</td>
                        <td>Director</td>
                        <td>Pay</td>
                    </tr>
                </table>
            </html>
        '''
        mock_get.return_value = mock_response

        result = get_directors('TEST')

        assert len(result) == 1
        assert 'Valid Name' in result[0]


class TestDetermineAdrStatus:
    """Tests for determine_adr_status function."""

    @patch('sangre_signal.fetchers.finviz.is_adr_finviz')
    def test_determine_adr_status_finviz_true(self, mock_is_adr):
        """Test when FinViz definitively says it's an ADR."""
        mock_is_adr.return_value = True

        result = determine_adr_status('TEST', yahoo_check=False)

        assert result is True
        mock_is_adr.assert_called_once_with('TEST')

    @patch('sangre_signal.fetchers.finviz.is_adr_finviz')
    def test_determine_adr_status_finviz_false(self, mock_is_adr):
        """Test when FinViz definitively says it's not an ADR."""
        mock_is_adr.return_value = False

        result = determine_adr_status('TEST', yahoo_check=True)

        # FinViz takes precedence over Yahoo check
        assert result is False

    @patch('sangre_signal.fetchers.finviz.is_adr_finviz')
    def test_determine_adr_status_finviz_none_yahoo_true(self, mock_is_adr):
        """Test fallback to Yahoo check when FinViz returns None."""
        mock_is_adr.return_value = None

        result = determine_adr_status('TEST', yahoo_check=True)

        assert result is True

    @patch('sangre_signal.fetchers.finviz.is_adr_finviz')
    def test_determine_adr_status_finviz_none_yahoo_false(self, mock_is_adr):
        """Test fallback to Yahoo check when FinViz returns None."""
        mock_is_adr.return_value = None

        result = determine_adr_status('TEST', yahoo_check=False)

        assert result is False

    @patch('sangre_signal.fetchers.finviz.is_adr_finviz')
    def test_determine_adr_status_precedence(self, mock_is_adr):
        """Test that FinViz takes precedence over Yahoo."""
        # FinViz says False, Yahoo says True
        mock_is_adr.return_value = False

        result = determine_adr_status('TEST', yahoo_check=True)

        # Should use FinViz result
        assert result is False


class TestFinvizEdgeCases:
    """Tests for edge cases in FinViz fetcher."""

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_is_adr_finviz_empty_response(self, mock_get):
        """Test with empty response body."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = ''
        mock_get.return_value = mock_response

        result = is_adr_finviz('TEST')

        assert result is None

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_is_adr_finviz_timeout(self, mock_get):
        """Test handling of request timeout."""
        import requests
        mock_get.side_effect = requests.Timeout("Request timeout")

        result = is_adr_finviz('TEST')

        assert result is None

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_get_directors_empty_table(self, mock_get):
        """Test with empty Key Executives table."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
            <html>
                <h2>Key Executives</h2>
                <table></table>
            </html>
        '''
        mock_get.return_value = mock_response

        result = get_directors('TEST')

        assert result == []

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_get_directors_finds_h3_heading(self, mock_get):
        """Test that function works with h3 heading instead of h2."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '''
            <html>
                <h3>Key Executives</h3>
                <table>
                    <tr>
                        <td>Director Name</td>
                        <td>Board Director</td>
                        <td>Pay</td>
                    </tr>
                </table>
            </html>
        '''
        mock_get.return_value = mock_response

        result = get_directors('TEST')

        assert len(result) == 1
        assert 'Director Name' in result[0]

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_is_adr_finviz_uses_user_agent(self, mock_get):
        """Test that requests include proper User-Agent header."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html><table class="fullview-title">Test</table></html>'
        mock_get.return_value = mock_response

        is_adr_finviz('TEST')

        # Verify User-Agent was included in headers
        call_args = mock_get.call_args
        assert 'headers' in call_args.kwargs
        assert 'User-Agent' in call_args.kwargs['headers']

    @patch('sangre_signal.fetchers.finviz.requests.get')
    def test_get_directors_uses_timeout(self, mock_get):
        """Test that requests include timeout parameter."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.text = '<html></html>'
        mock_get.return_value = mock_response

        get_directors('TEST')

        # Verify timeout was included
        call_args = mock_get.call_args
        assert 'timeout' in call_args.kwargs
