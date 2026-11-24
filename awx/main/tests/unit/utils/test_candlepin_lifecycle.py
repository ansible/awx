# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

from datetime import datetime, timezone
from unittest import mock

from awx.main.utils.candlepin.lifecycle import (
    parse_cert,
    needs_renewal,
    run_candlepin_lifecycle,
    get_candlepin_url,
    get_renewal_days,
    get_candlepin_ca,
    get_proxy_url,
)

# Sample test certificate (expires far in the future for testing)
SAMPLE_CERT_PEM = """-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKJ5VZ2cPQE5MA0GCSqGSIb3DQEBCwUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
aWRnaXRzIFB0eSBMdGQwHhcNMjYwMTAxMDAwMDAwWhcNMjcwMTAxMDAwMDAwWjBF
MQswCQYDVQQGEwJBVTETMBEGA1UECAwKU29tZS1TdGF0ZTEhMB8GA1UECgwYSW50
ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB
CgKCAQEA0a7Y3l3X4L7pKq3xDl8vCRrRK6qU5dF7r3xQH5YRz4hZJN9wE3xW0qDT
-----END CERTIFICATE-----"""


class TestCandlepinLifecycle:
    """Tests for Candlepin lifecycle functions."""

    @mock.patch('awx.main.utils.candlepin.lifecycle.settings')
    def test_get_candlepin_url_default(self, mock_settings):
        """Test default Candlepin URL from defaults.py."""
        mock_settings.AWX_ANALYTICS_CANDLEPIN_URL = 'https://subscription.example.com/candlepin/'
        url = get_candlepin_url()
        assert url == 'https://subscription.example.com/candlepin/'

    @mock.patch('awx.main.utils.candlepin.lifecycle.settings')
    def test_get_renewal_days_from_settings(self, mock_settings):
        """Test renewal days from Django settings."""
        mock_settings.AWX_ANALYTICS_CANDLEPIN_RENEWAL_THRESHOLD_DAYS = 45
        days = get_renewal_days()
        assert days == 45

    @mock.patch('awx.main.utils.candlepin.lifecycle.os.path.isfile')
    @mock.patch('awx.main.utils.candlepin.lifecycle.settings')
    def test_get_candlepin_ca_from_settings(self, mock_settings, mock_isfile):
        """Test Candlepin CA from Django settings when file exists."""
        mock_settings.AWX_ANALYTICS_CANDLEPIN_CA = '/path/to/ca.pem'
        mock_isfile.return_value = True
        ca = get_candlepin_ca()
        assert ca == '/path/to/ca.pem'

    @mock.patch('awx.main.utils.candlepin.lifecycle.os.path.isfile')
    @mock.patch('awx.main.utils.candlepin.lifecycle.settings')
    def test_get_candlepin_ca_file_not_found(self, mock_settings, mock_isfile):
        """Test Candlepin CA returns None when configured path doesn't exist."""
        mock_settings.AWX_ANALYTICS_CANDLEPIN_CA = '/path/to/missing.pem'
        mock_isfile.return_value = False
        ca = get_candlepin_ca()
        assert ca is None

    @mock.patch('awx.main.utils.candlepin.lifecycle.settings')
    def test_get_proxy_url_from_settings(self, mock_settings):
        """Test proxy URL from Django settings."""
        mock_settings.AWX_ANALYTICS_CANDLEPIN_PROXY_URL = 'http://proxy.example.com:8080'
        proxy = get_proxy_url()
        assert proxy == 'http://proxy.example.com:8080'

    @mock.patch('awx.main.utils.candlepin.lifecycle.x509.load_pem_x509_certificate')
    def test_parse_cert(self, mock_load_cert):
        """Test certificate parsing."""
        # Mock a certificate object
        mock_cert = mock.Mock()
        mock_cert.serial_number = 123456
        mock_cert.not_valid_before_utc = datetime(2026, 1, 1, tzinfo=timezone.utc)
        mock_cert.not_valid_after_utc = datetime(2027, 1, 1, tzinfo=timezone.utc)

        # Mock subject and issuer
        mock_attr = mock.Mock()
        mock_attr.oid._name = 'commonName'
        mock_attr.value = 'test-cn'
        mock_cert.subject = [mock_attr]
        mock_cert.issuer = [mock_attr]

        mock_load_cert.return_value = mock_cert

        result = parse_cert('fake-pem')

        assert result['serial'] == '123456'
        assert result['cn'] == 'test-cn'
        assert 'not_before' in result
        assert 'not_after' in result
        assert 'days_remaining' in result

    @mock.patch('awx.main.utils.candlepin.lifecycle.parse_cert')
    def test_needs_renewal_true(self, mock_parse):
        """Test needs_renewal returns True when cert is expiring soon."""
        mock_parse.return_value = {'days_remaining': 10}

        result = needs_renewal('fake-cert', days_before_expiry=30)
        assert result is True

    @mock.patch('awx.main.utils.candlepin.lifecycle.parse_cert')
    def test_needs_renewal_false(self, mock_parse):
        """Test needs_renewal returns False when cert has time remaining."""
        mock_parse.return_value = {'days_remaining': 100}

        result = needs_renewal('fake-cert', days_before_expiry=30)
        assert result is False

    @mock.patch('awx.main.utils.candlepin.lifecycle.CandlepinClient')
    @mock.patch('awx.main.utils.candlepin.lifecycle.parse_cert')
    def test_run_candlepin_lifecycle_no_renewal_needed(self, mock_parse, mock_client_class):
        """Test lifecycle when no renewal is needed."""
        mock_parse.return_value = {'serial': '123', 'cn': 'test', 'not_after': '2027-01-01T00:00:00+00:00', 'days_remaining': 100}

        mock_client = mock.Mock()
        mock_client.checkin.return_value = True
        mock_client.get_consumer.return_value = None  # Skip serial comparison
        mock_client_class.return_value = mock_client

        cert_pem, key_pem = run_candlepin_lifecycle('cert-pem', 'key-pem', 'consumer-uuid', candlepin_url='https://test.example.com', renewal_days=30)

        assert cert_pem == 'cert-pem'
        assert key_pem == 'key-pem'
        mock_client.checkin.assert_called_once()
        mock_client.regenerate_cert.assert_not_called()

    @mock.patch('awx.main.utils.candlepin.lifecycle.CandlepinClient')
    @mock.patch('awx.main.utils.candlepin.lifecycle.parse_cert')
    def test_run_candlepin_lifecycle_with_renewal(self, mock_parse, mock_client_class):
        """Test lifecycle when renewal is needed."""
        # parse_cert is called multiple times:
        # 1. Parse original cert
        # 2. In needs_renewal() to check expiry
        # 3. Parse new cert after renewal for logging
        mock_parse.side_effect = [
            {'serial': '123', 'cn': 'test', 'not_after': '2026-02-01', 'days_remaining': 10},  # Original cert
            {'serial': '123', 'cn': 'test', 'not_after': '2026-02-01', 'days_remaining': 10},  # needs_renewal check
            {'serial': '456', 'cn': 'test', 'not_after': '2027-02-01', 'days_remaining': 365},  # New cert
        ]

        mock_client = mock.Mock()
        mock_client.checkin.return_value = True
        mock_client.get_consumer.return_value = None  # Skip serial comparison
        mock_client.regenerate_cert.return_value = ('new-cert', 'new-key')
        mock_client_class.return_value = mock_client

        cert_pem, key_pem = run_candlepin_lifecycle('old-cert', 'old-key', 'consumer-uuid', renewal_days=90)

        assert cert_pem == 'new-cert'
        assert key_pem == 'new-key'
        mock_client.regenerate_cert.assert_called_once()

    @mock.patch('awx.main.utils.candlepin.lifecycle.CandlepinClient')
    @mock.patch('awx.main.utils.candlepin.lifecycle.parse_cert')
    def test_run_candlepin_lifecycle_expired_cert_renewal(self, mock_parse, mock_client_class):
        """Test lifecycle renews an expired certificate."""
        # parse_cert called for:
        # 1. Parse original expired cert
        # 2. needs_renewal check (expired, so returns True)
        # 3. Parse new cert after renewal
        mock_parse.side_effect = [
            {'serial': '123', 'cn': 'test', 'not_after': '2025-12-31', 'days_remaining': -120},  # Expired cert
            {'serial': '123', 'cn': 'test', 'not_after': '2025-12-31', 'days_remaining': -120},  # needs_renewal
            {'serial': '456', 'cn': 'test', 'not_after': '2027-06-01', 'days_remaining': 365},  # New cert
        ]

        mock_client = mock.Mock()
        mock_client.checkin.return_value = True
        mock_client.get_consumer.return_value = None
        mock_client.regenerate_cert.return_value = ('new-cert', 'new-key')
        mock_client_class.return_value = mock_client

        cert_pem, key_pem = run_candlepin_lifecycle('expired-cert', 'old-key', 'consumer-uuid', renewal_days=90)

        assert cert_pem == 'new-cert'
        assert key_pem == 'new-key'
        mock_client.regenerate_cert.assert_called_once()

    @mock.patch('awx.main.utils.candlepin.lifecycle.CandlepinClient')
    @mock.patch('awx.main.utils.candlepin.lifecycle.parse_cert')
    def test_run_candlepin_lifecycle_checkin_failure_revoked_cert(self, mock_parse, mock_client_class):
        """Test lifecycle handles check-in failure (e.g., revoked certificate)."""
        mock_parse.return_value = {'serial': '123', 'cn': 'test', 'not_after': '2027-01-01', 'days_remaining': 100}

        # Check-in fails (could indicate revoked cert or deleted consumer)
        mock_client = mock.Mock()
        mock_client.checkin.return_value = False
        mock_client.get_consumer.return_value = None  # get_consumer also fails
        mock_client_class.return_value = mock_client

        # Lifecycle should continue and return original cert
        cert_pem, key_pem = run_candlepin_lifecycle('cert-pem', 'key-pem', 'consumer-uuid', renewal_days=30)

        assert cert_pem == 'cert-pem'
        assert key_pem == 'key-pem'
        mock_client.checkin.assert_called_once()
        # Regeneration should not be attempted since get_consumer indicates consumer doesn't exist
        mock_client.regenerate_cert.assert_not_called()

    @mock.patch('awx.main.utils.candlepin.lifecycle.CandlepinClient')
    @mock.patch('awx.main.utils.candlepin.lifecycle.parse_cert')
    def test_run_candlepin_lifecycle_consumer_deleted_server_side(self, mock_parse, mock_client_class):
        """Test lifecycle detects when consumer was deleted from Candlepin server."""
        mock_parse.return_value = {'serial': '123', 'cn': 'test', 'not_after': '2027-01-01', 'days_remaining': 100}

        # Both check-in and get_consumer fail (consumer deleted)
        mock_client = mock.Mock()
        mock_client.checkin.return_value = False
        mock_client.get_consumer.return_value = None
        mock_client_class.return_value = mock_client

        cert_pem, key_pem = run_candlepin_lifecycle('cert-pem', 'key-pem', 'consumer-uuid', renewal_days=30)

        # Should return original cert (caller can attempt mTLS, which will fail and fall back to service account)
        assert cert_pem == 'cert-pem'
        assert key_pem == 'key-pem'
        mock_client.checkin.assert_called_once()
        mock_client.get_consumer.assert_called_once()
        mock_client.regenerate_cert.assert_not_called()
