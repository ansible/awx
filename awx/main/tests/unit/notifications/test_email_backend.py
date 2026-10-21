import socket
from unittest import mock

import pytest

from awx.main.notifications.email_backend import CustomEmailBackend


def _make_addrinfo(ip_str, family=socket.AF_INET):
    """Build a single getaddrinfo result tuple for the given IP string."""
    if family == socket.AF_INET:
        sockaddr = (ip_str, 0)
    else:
        sockaddr = (ip_str, 0, 0, 0)
    return [(family, socket.SOCK_STREAM, 0, '', sockaddr)]


class TestValidateHostNotInternal:
    """Unit tests for CustomEmailBackend._validate_host_not_internal."""

    def test_loopback_ipv4_rejected(self):
        with mock.patch(
            'awx.main.notifications.email_backend.socket.getaddrinfo',
            return_value=_make_addrinfo('127.0.0.1'),
        ):
            with pytest.raises(ValueError, match='blocked address'):
                CustomEmailBackend._validate_host_not_internal('127.0.0.1')

    def test_private_10_network_rejected(self):
        with mock.patch(
            'awx.main.notifications.email_backend.socket.getaddrinfo',
            return_value=_make_addrinfo('10.0.0.1'),
        ):
            with pytest.raises(ValueError, match='blocked address'):
                CustomEmailBackend._validate_host_not_internal('10.0.0.1')

    def test_private_192_168_rejected(self):
        with mock.patch(
            'awx.main.notifications.email_backend.socket.getaddrinfo',
            return_value=_make_addrinfo('192.168.1.1'),
        ):
            with pytest.raises(ValueError, match='blocked address'):
                CustomEmailBackend._validate_host_not_internal('192.168.1.1')

    def test_loopback_ipv6_rejected(self):
        with mock.patch(
            'awx.main.notifications.email_backend.socket.getaddrinfo',
            return_value=_make_addrinfo('::1', family=socket.AF_INET6),
        ):
            with pytest.raises(ValueError, match='blocked address'):
                CustomEmailBackend._validate_host_not_internal('::1')

    def test_link_local_rejected(self):
        with mock.patch(
            'awx.main.notifications.email_backend.socket.getaddrinfo',
            return_value=_make_addrinfo('169.254.1.1'),
        ):
            with pytest.raises(ValueError, match='link-local'):
                CustomEmailBackend._validate_host_not_internal('169.254.1.1')

    def test_bracketed_host_stripped(self):
        """Brackets around IPv6 literals should be removed before resolving."""
        with mock.patch(
            'awx.main.notifications.email_backend.socket.getaddrinfo',
            return_value=_make_addrinfo('::1', family=socket.AF_INET6),
        ) as mock_gai:
            with pytest.raises(ValueError, match='blocked address'):
                CustomEmailBackend._validate_host_not_internal('[::1]')
            mock_gai.assert_called_once_with('::1', None)

    def test_public_ip_allowed(self):
        """A host resolving to a public IP must NOT raise."""
        with mock.patch(
            'awx.main.notifications.email_backend.socket.getaddrinfo',
            return_value=_make_addrinfo('8.8.8.8'),
        ):
            CustomEmailBackend._validate_host_not_internal('smtp.example.com')

    def test_empty_host_allowed(self):
        """An empty or None host should return without error."""
        CustomEmailBackend._validate_host_not_internal('')
        CustomEmailBackend._validate_host_not_internal(None)

    def test_dns_failure_allowed(self):
        """If DNS resolution fails (gaierror), the method should return
        without raising — the actual SMTP open will fail later with a
        clearer error."""
        with mock.patch(
            'awx.main.notifications.email_backend.socket.getaddrinfo',
            side_effect=socket.gaierror('Name or service not known'),
        ):
            CustomEmailBackend._validate_host_not_internal('no-such-host.invalid')

    def test_invalid_ip_in_addrinfo_skipped(self):
        """If getaddrinfo returns a sockaddr whose first element is not a
        valid IP (ValueError from ip_address), that entry is skipped."""
        bad_entry = [(socket.AF_INET, socket.SOCK_STREAM, 0, '', ('not-an-ip', 0))]
        with mock.patch(
            'awx.main.notifications.email_backend.socket.getaddrinfo',
            return_value=bad_entry,
        ):
            CustomEmailBackend._validate_host_not_internal('weird-host')


class TestOpenCallsValidation:
    """Verify that CustomEmailBackend.open() invokes the SSRF guard."""

    def test_open_rejects_internal_host(self):
        """open() must raise ValueError before attempting SMTP connect
        when the host resolves to a loopback address."""
        backend = CustomEmailBackend(
            host='127.0.0.1',
            port=25,
            username='',
            password='',
            use_tls=False,
            use_ssl=False,
        )
        with mock.patch(
            'awx.main.notifications.email_backend.socket.getaddrinfo',
            return_value=_make_addrinfo('127.0.0.1'),
        ):
            with pytest.raises(ValueError, match='blocked address'):
                backend.open()

    def test_open_proceeds_for_public_host(self):
        """open() must call super().open() when the host is public."""
        backend = CustomEmailBackend(
            host='smtp.example.com',
            port=587,
            username='',
            password='',
            use_tls=True,
            use_ssl=False,
        )
        with mock.patch(
            'awx.main.notifications.email_backend.socket.getaddrinfo',
            return_value=_make_addrinfo('93.184.216.34'),
        ), mock.patch(
            'django.core.mail.backends.smtp.EmailBackend.open',
            return_value=True,
        ) as mock_super_open:
            result = backend.open()
            mock_super_open.assert_called_once()
            assert result is True


class TestSMTPAllowList:
    """Tests for NOTIFICATION_IP_ALLOW_LIST integration with the SMTP backend."""

    def test_cidr_allows_private_smtp_host(self):
        with (
            mock.patch('awx.main.notifications.email_backend.socket.getaddrinfo', return_value=_make_addrinfo('10.50.12.40')),
            mock.patch('awx.main.notifications.email_backend.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['10.50.0.0/16']
            CustomEmailBackend._validate_host_not_internal('smtp.internal.corp')

    def test_hostname_allows_private_smtp_host(self):
        with (
            mock.patch('awx.main.notifications.email_backend.socket.getaddrinfo', return_value=_make_addrinfo('10.50.12.40')),
            mock.patch('awx.main.notifications.email_backend.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['smtp.internal.corp']
            CustomEmailBackend._validate_host_not_internal('smtp.internal.corp')

    def test_subdomain_wildcard_allows_smtp_host(self):
        with (
            mock.patch('awx.main.notifications.email_backend.socket.getaddrinfo', return_value=_make_addrinfo('192.168.1.25')),
            mock.patch('awx.main.notifications.email_backend.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['.internal.corp']
            CustomEmailBackend._validate_host_not_internal('smtp.internal.corp')

    def test_non_matching_hostname_still_blocked(self):
        with (
            mock.patch('awx.main.notifications.email_backend.socket.getaddrinfo', return_value=_make_addrinfo('10.50.12.40')),
            mock.patch('awx.main.notifications.email_backend.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['other.host.corp']
            with pytest.raises(ValueError, match='blocked address'):
                CustomEmailBackend._validate_host_not_internal('smtp.internal.corp')

    def test_empty_allowlist_blocks_private(self):
        with (
            mock.patch('awx.main.notifications.email_backend.socket.getaddrinfo', return_value=_make_addrinfo('10.0.0.1')),
            mock.patch('awx.main.notifications.email_backend.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = []
            with pytest.raises(ValueError, match='blocked address'):
                CustomEmailBackend._validate_host_not_internal('smtp.internal.corp')

    def test_link_local_blocked_even_with_allowlist(self):
        with (
            mock.patch('awx.main.notifications.email_backend.socket.getaddrinfo', return_value=_make_addrinfo('169.254.169.254')),
            mock.patch('awx.main.notifications.email_backend.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['169.254.0.0/16']
            with pytest.raises(ValueError, match='link-local'):
                CustomEmailBackend._validate_host_not_internal('metadata.internal')

    def test_link_local_blocked_even_with_hostname_allowlist(self):
        with (
            mock.patch('awx.main.notifications.email_backend.socket.getaddrinfo', return_value=_make_addrinfo('169.254.169.254')),
            mock.patch('awx.main.notifications.email_backend.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['metadata.internal']
            with pytest.raises(ValueError, match='link-local'):
                CustomEmailBackend._validate_host_not_internal('metadata.internal')

    def test_ipv4_mapped_link_local_blocked(self):
        with (
            mock.patch(
                'awx.main.notifications.email_backend.socket.getaddrinfo',
                return_value=_make_addrinfo('::ffff:169.254.169.254', family=socket.AF_INET6),
            ),
            mock.patch('awx.main.notifications.email_backend.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['metadata.internal']
            with pytest.raises(ValueError, match='link-local'):
                CustomEmailBackend._validate_host_not_internal('metadata.internal')

    def test_bracketed_ipv6_with_allowlist(self):
        with (
            mock.patch('awx.main.notifications.email_backend.socket.getaddrinfo', return_value=_make_addrinfo('fd00::1', family=socket.AF_INET6)),
            mock.patch('awx.main.notifications.email_backend.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['fd00::/8']
            CustomEmailBackend._validate_host_not_internal('[fd00::1]')

    def test_loopback_allowed_when_listed(self):
        with (
            mock.patch('awx.main.notifications.email_backend.socket.getaddrinfo', return_value=_make_addrinfo('127.0.0.1')),
            mock.patch('awx.main.notifications.email_backend.settings') as mock_settings,
        ):
            mock_settings.NOTIFICATION_IP_ALLOW_LIST = ['127.0.0.0/8']
            CustomEmailBackend._validate_host_not_internal('localhost')
