import socket
from unittest import mock

import pytest

from awx.main.notifications.url_validation import SSRFBlockedError, get_hostname, validate_url


@pytest.mark.parametrize(
    "ip,should_block",
    [
        ("127.0.0.1", True),
        ("10.0.0.1", True),
        ("172.16.0.1", True),
        ("192.168.1.1", True),
        ("169.254.169.254", True),
        ("::1", True),
        ("8.8.8.8", False),
        ("140.82.121.3", False),
    ],
)
def test_validate_url_blocked_addresses(ip, should_block):
    addrinfo = [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', (ip, 443))]
    with mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=addrinfo):
        if should_block:
            with pytest.raises(SSRFBlockedError):
                validate_url("https://example.com/hook")
        else:
            assert validate_url("https://example.com/hook") == "https://example.com/hook"


def test_validate_url_no_hostname():
    with pytest.raises(SSRFBlockedError, match="no hostname"):
        validate_url("not-a-url")


def test_validate_url_unresolvable():
    with mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', side_effect=socket.gaierror("Name or service not known")):
        with pytest.raises(SSRFBlockedError, match="Cannot resolve"):
            validate_url("https://does.not.exist.example.com/hook")


def test_get_hostname():
    assert get_hostname("https://example.com/path") == "example.com"
    assert get_hostname("https://other.host:8443/api") == "other.host"


class TestAllowList:
    """Tests for the NOTIFICATION_IP_ALLOW_LIST setting."""

    def _addrinfo(self, ip):
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', (ip, 443))]

    def test_cidr_allows_private_ip(self):
        with (
            mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('10.50.12.40')),
            mock.patch('awx.main.notifications.url_validation.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['10.50.0.0/16']
            assert validate_url("https://elastic.internal/hook") == "https://elastic.internal/hook"

    def test_non_allowlisted_private_ip_still_blocked(self):
        with (
            mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('10.50.12.40')),
            mock.patch('awx.main.notifications.url_validation.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['172.16.0.0/12']
            with pytest.raises(SSRFBlockedError, match="blocked address"):
                validate_url("https://elastic.internal/hook")

    def test_individual_ip_allowed(self):
        with (
            mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('192.168.1.1')),
            mock.patch('awx.main.notifications.url_validation.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['192.168.1.1']
            assert validate_url("https://grafana.local/hook") == "https://grafana.local/hook"

    def test_public_ip_unaffected_by_empty_allow_list(self):
        with (
            mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('8.8.8.8')),
            mock.patch('awx.main.notifications.url_validation.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = []
            assert validate_url("https://example.com/hook") == "https://example.com/hook"

    def test_loopback_allowed_when_explicitly_listed(self):
        with (
            mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('127.0.0.1')),
            mock.patch('awx.main.notifications.url_validation.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['127.0.0.0/8']
            assert validate_url("https://localhost/hook") == "https://localhost/hook"

    def test_metadata_ip_blocked_even_when_explicitly_listed(self):
        with (
            mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('169.254.169.254')),
            mock.patch('awx.main.notifications.url_validation.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['169.254.169.254']
            with pytest.raises(SSRFBlockedError, match="link-local"):
                validate_url("https://metadata.internal/hook")

    def test_multiple_cidrs(self):
        with (
            mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('172.16.20.15')),
            mock.patch('awx.main.notifications.url_validation.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['10.0.0.0/8', '172.16.0.0/12']
            assert validate_url("https://alerts.internal/hook") == "https://alerts.internal/hook"

    def test_default_empty_allow_list_blocks_private(self):
        with (
            mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('10.0.0.1')),
            mock.patch('awx.main.notifications.url_validation.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = []
            with pytest.raises(SSRFBlockedError, match="blocked address"):
                validate_url("https://example.com/hook")

    def test_invalid_allow_list_entry_ignored(self):
        with (
            mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('10.0.0.1')),
            mock.patch('awx.main.notifications.url_validation.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['not-a-cidr']
            with pytest.raises(SSRFBlockedError, match="blocked address"):
                validate_url("https://example.com/hook")


class TestHostnameAllowList:
    """Tests for hostname entries in NOTIFICATION_IP_ALLOW_LIST."""

    def _addrinfo(self, ip):
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', (ip, 443))]

    def test_exact_hostname_bypasses_ssrf_check(self):
        with mock.patch('awx.main.notifications.url_validation.settings') as mock_settings:
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['elastic.internal.example.com']
            with mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('10.50.12.40')):
                assert validate_url("https://elastic.internal.example.com/hook") == "https://elastic.internal.example.com/hook"

    def test_hostname_match_is_case_insensitive(self):
        with mock.patch('awx.main.notifications.url_validation.settings') as mock_settings:
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['Elastic.Internal.Example.Com']
            with mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('10.50.12.40')):
                assert validate_url("https://elastic.internal.example.com/hook") == "https://elastic.internal.example.com/hook"

    def test_dot_prefix_matches_subdomains(self):
        with mock.patch('awx.main.notifications.url_validation.settings') as mock_settings:
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['.internal.example.com']
            with mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('10.50.12.40')):
                assert validate_url("https://elastic.internal.example.com/hook") == "https://elastic.internal.example.com/hook"

    def test_dot_prefix_does_not_match_base_domain(self):
        with (
            mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('10.50.12.40')),
            mock.patch('awx.main.notifications.url_validation.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['.internal.example.com']
            with pytest.raises(SSRFBlockedError, match="blocked address"):
                validate_url("https://internal.example.com/hook")

    def test_non_matching_hostname_still_blocked(self):
        with (
            mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('10.50.12.40')),
            mock.patch('awx.main.notifications.url_validation.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['elastic.internal.example.com']
            with pytest.raises(SSRFBlockedError, match="blocked address"):
                validate_url("https://other.internal.example.com/hook")

    def test_hostname_allowed_when_dns_fails(self):
        """When hostname is allowlisted but DNS resolution fails, the request is still allowed."""
        with mock.patch('awx.main.notifications.url_validation.settings') as mock_settings:
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['elastic.internal.example.com']
            with mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', side_effect=socket.gaierror("Name or service not known")):
                assert validate_url("https://elastic.internal.example.com/hook") == "https://elastic.internal.example.com/hook"

    def test_mixed_cidr_and_hostname_entries(self):
        with mock.patch('awx.main.notifications.url_validation.settings') as mock_settings:
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['10.0.0.0/8', 'grafana.corp.internal']
            with mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('172.16.1.5')):
                assert validate_url("https://grafana.corp.internal/hook") == "https://grafana.corp.internal/hook"

    def test_cidr_still_works_with_hostname_entries_present(self):
        with (
            mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('10.50.12.40')),
            mock.patch('awx.main.notifications.url_validation.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['10.50.0.0/16', 'grafana.corp.internal']
            assert validate_url("https://unknown.host/hook") == "https://unknown.host/hook"


class TestLinkLocalDenyList:
    """Link-local addresses are always blocked, even if allowlisted."""

    def _addrinfo(self, ip):
        return [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', (ip, 443))]

    def _addrinfo6(self, ip):
        return [(socket.AF_INET6, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', (ip, 443, 0, 0))]

    def test_link_local_blocked_with_cidr_allowlist(self):
        with (
            mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('169.254.169.254')),
            mock.patch('awx.main.notifications.url_validation.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['169.254.0.0/16']
            with pytest.raises(SSRFBlockedError, match="link-local"):
                validate_url("https://metadata.example.com/hook")

    def test_link_local_blocked_with_hostname_allowlist(self):
        with (
            mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('169.254.169.254')),
            mock.patch('awx.main.notifications.url_validation.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['metadata.example.com']
            with pytest.raises(SSRFBlockedError, match="link-local"):
                validate_url("https://metadata.example.com/hook")

    def test_ipv6_link_local_blocked_with_allowlist(self):
        with (
            mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo6('fe80::1')),
            mock.patch('awx.main.notifications.url_validation.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['fe80::/10']
            with pytest.raises(SSRFBlockedError, match="link-local"):
                validate_url("https://metadata.example.com/hook")

    def test_hostname_allowed_for_non_link_local_private_ip(self):
        with (
            mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('10.50.1.20')),
            mock.patch('awx.main.notifications.url_validation.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['elastic.internal.example.com']
            assert validate_url("https://elastic.internal.example.com/hook") == "https://elastic.internal.example.com/hook"

    def test_ipv4_mapped_link_local_blocked_with_hostname_allowlist(self):
        with (
            mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo6('::ffff:169.254.169.254')),
            mock.patch('awx.main.notifications.url_validation.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['metadata.example.com']
            with pytest.raises(SSRFBlockedError, match="link-local"):
                validate_url("https://metadata.example.com/hook")

    def test_ipv4_mapped_link_local_blocked_with_cidr_allowlist(self):
        with (
            mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo6('::ffff:169.254.169.254')),
            mock.patch('awx.main.notifications.url_validation.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['169.254.0.0/16']
            with pytest.raises(SSRFBlockedError, match="link-local"):
                validate_url("https://metadata.example.com/hook")

    def test_loopback_still_allowable(self):
        with (
            mock.patch('awx.main.notifications.url_validation.socket.getaddrinfo', return_value=self._addrinfo('127.0.0.1')),
            mock.patch('awx.main.notifications.url_validation.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['127.0.0.0/8']
            assert validate_url("https://localhost/hook") == "https://localhost/hook"
