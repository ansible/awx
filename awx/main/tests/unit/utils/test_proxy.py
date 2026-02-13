# Copyright (c) 2024 Ansible, Inc.
# All Rights Reserved.

from unittest import mock

from awx.main.utils.proxy import get_first_remote_host_from_headers, is_proxy_in_headers


class TestGetFirstRemoteHostFromHeaders:
    """Tests for get_first_remote_host_from_headers function."""

    def _make_mock_request(self, environ):
        """Create a mock request with the given environ dict."""
        request = mock.MagicMock()
        request.environ = environ
        return request

    def test_single_value_headers(self):
        """Test extraction from headers with single values (no commas)."""
        request = self._make_mock_request(
            {
                "REMOTE_ADDR": "192.168.1.1",
                "REMOTE_HOST": "client.example.com",
            }
        )
        headers = ["REMOTE_ADDR", "REMOTE_HOST"]

        result = get_first_remote_host_from_headers(request, headers)

        assert result == {"192.168.1.1", "client.example.com"}

    def test_comma_separated_only_first_entry(self):
        """Test that only the first entry is extracted from comma-separated values."""
        request = self._make_mock_request(
            {
                "HTTP_X_FORWARDED_FOR": "10.0.0.1, 192.168.1.1, 172.16.0.1",
            }
        )
        headers = ["HTTP_X_FORWARDED_FOR"]

        result = get_first_remote_host_from_headers(request, headers)

        # Only the first IP should be included
        assert result == {"10.0.0.1"}
        # Subsequent IPs should NOT be included
        assert "192.168.1.1" not in result
        assert "172.16.0.1" not in result

    def test_comma_separated_with_whitespace(self):
        """Test that whitespace is properly stripped from first entry."""
        request = self._make_mock_request(
            {
                "HTTP_X_FORWARDED_FOR": "  10.0.0.1  , 192.168.1.1",
            }
        )
        headers = ["HTTP_X_FORWARDED_FOR"]

        result = get_first_remote_host_from_headers(request, headers)

        assert result == {"10.0.0.1"}

    def test_multiple_headers_with_comma_separated(self):
        """Test multiple headers where some have comma-separated values."""
        request = self._make_mock_request(
            {
                "HTTP_X_FORWARDED_FOR": "client.example.com, proxy1.example.com, proxy2.example.com",
                "REMOTE_ADDR": "172.16.0.1",
                "REMOTE_HOST": "proxy2.example.com",
            }
        )
        headers = ["HTTP_X_FORWARDED_FOR", "REMOTE_ADDR", "REMOTE_HOST"]

        result = get_first_remote_host_from_headers(request, headers)

        # Should have first entry from X-Forwarded-For plus the single values from other headers
        assert result == {"client.example.com", "172.16.0.1", "proxy2.example.com"}
        # Should NOT have subsequent entries from X-Forwarded-For
        assert "proxy1.example.com" not in result

    def test_empty_header_value(self):
        """Test handling of empty header values."""
        request = self._make_mock_request(
            {
                "HTTP_X_FORWARDED_FOR": "",
                "REMOTE_ADDR": "192.168.1.1",
            }
        )
        headers = ["HTTP_X_FORWARDED_FOR", "REMOTE_ADDR"]

        result = get_first_remote_host_from_headers(request, headers)

        assert result == {"192.168.1.1"}

    def test_missing_header(self):
        """Test handling of headers that don't exist in environ."""
        request = self._make_mock_request(
            {
                "REMOTE_ADDR": "192.168.1.1",
            }
        )
        headers = ["HTTP_X_FORWARDED_FOR", "REMOTE_ADDR", "REMOTE_HOST"]

        result = get_first_remote_host_from_headers(request, headers)

        assert result == {"192.168.1.1"}

    def test_empty_headers_list(self):
        """Test with no headers specified."""
        request = self._make_mock_request(
            {
                "REMOTE_ADDR": "192.168.1.1",
            }
        )
        headers = []

        result = get_first_remote_host_from_headers(request, headers)

        assert result == set()

    def test_whitespace_only_first_entry(self):
        """Test handling when first entry is whitespace only."""
        request = self._make_mock_request(
            {
                "HTTP_X_FORWARDED_FOR": "   , 192.168.1.1",
            }
        )
        headers = ["HTTP_X_FORWARDED_FOR"]

        result = get_first_remote_host_from_headers(request, headers)

        # Empty/whitespace first entry should be skipped
        assert result == set()

    def test_single_entry_with_trailing_comma(self):
        """Test single entry that happens to have a trailing comma."""
        request = self._make_mock_request(
            {
                "HTTP_X_FORWARDED_FOR": "10.0.0.1,",
            }
        )
        headers = ["HTTP_X_FORWARDED_FOR"]

        result = get_first_remote_host_from_headers(request, headers)

        assert result == {"10.0.0.1"}


class TestIsProxyInHeaders:
    """Tests for is_proxy_in_headers function."""

    def _make_mock_request(self, environ):
        """Create a mock request with the given environ dict."""
        request = mock.MagicMock()
        request.environ = environ
        return request

    def test_proxy_found_in_single_value(self):
        """Test proxy detection in single-value header."""
        request = self._make_mock_request(
            {
                "REMOTE_ADDR": "192.168.1.1",
            }
        )

        result = is_proxy_in_headers(request, ["192.168.1.1"], ["REMOTE_ADDR"])

        assert result is True

    def test_proxy_found_in_comma_separated(self):
        """Test proxy detection in comma-separated header value."""
        request = self._make_mock_request(
            {
                "HTTP_X_FORWARDED_FOR": "10.0.0.1, 192.168.1.1, 172.16.0.1",
            }
        )

        result = is_proxy_in_headers(request, ["192.168.1.1"], ["HTTP_X_FORWARDED_FOR"])

        assert result is True

    def test_proxy_not_found(self):
        """Test when proxy is not in any header."""
        request = self._make_mock_request(
            {
                "REMOTE_ADDR": "10.0.0.1",
            }
        )

        result = is_proxy_in_headers(request, ["192.168.1.1"], ["REMOTE_ADDR"])

        assert result is False

    def test_multiple_proxies_one_match(self):
        """Test with multiple allowed proxies, one matches."""
        request = self._make_mock_request(
            {
                "REMOTE_HOST": "proxy.example.com",
            }
        )

        result = is_proxy_in_headers(
            request,
            ["proxy1.example.com", "proxy.example.com", "proxy2.example.com"],
            ["REMOTE_HOST"],
        )

        assert result is True
