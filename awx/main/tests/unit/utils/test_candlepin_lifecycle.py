# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

from datetime import datetime, timezone
from unittest import mock

from awx.main.utils.candlepin.lifecycle import (
    parse_cert,
    is_cert_valid,
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
        mock_settings.AWX_ANALYTICS_CANDLEPIN_URL = 'https://subscription.rhsm.redhat.com/subscription/'
        url = get_candlepin_url()
        assert url == 'https://subscription.rhsm.redhat.com/subscription/'

    @mock.patch('awx.main.utils.candlepin.lifecycle.settings')
    def test_get_candlepin_url_custom(self, mock_settings):
        """Test custom Candlepin URL from Django settings."""
        mock_settings.AWX_ANALYTICS_CANDLEPIN_URL = 'https://custom.example.com'
        url = get_candlepin_url()
        assert url == 'https://custom.example.com'

    @mock.patch('awx.main.utils.candlepin.lifecycle.settings')
    def test_get_renewal_days_default(self, mock_settings):
        """Test default renewal days."""
        mock_settings.AWX_ANALYTICS_CANDLEPIN_RENEWAL_THRESHOLD_DAYS = 90
        days = get_renewal_days()
        assert days == 90

    @mock.patch('awx.main.utils.candlepin.lifecycle.settings')
    def test_get_renewal_days_from_settings(self, mock_settings):
        """Test renewal days from Django settings."""
        mock_settings.AWX_ANALYTICS_CANDLEPIN_RENEWAL_THRESHOLD_DAYS = 45
        days = get_renewal_days()
        assert days == 45

    @mock.patch('awx.main.utils.candlepin.lifecycle.settings')
    def test_get_candlepin_ca_none(self, mock_settings):
        """Test Candlepin CA returns None when not set."""
        mock_settings.AWX_ANALYTICS_CANDLEPIN_CA = None
        ca = get_candlepin_ca()
        assert ca is None

    @mock.patch('awx.main.utils.candlepin.lifecycle.settings')
    def test_get_candlepin_ca_from_settings(self, mock_settings):
        """Test Candlepin CA from Django settings."""
        mock_settings.AWX_ANALYTICS_CANDLEPIN_CA = '/path/to/ca.pem'
        ca = get_candlepin_ca()
        assert ca == '/path/to/ca.pem'

    @mock.patch('awx.main.utils.candlepin.lifecycle.settings')
    def test_get_proxy_url_none(self, mock_settings):
        """Test proxy URL returns None when not set."""
        mock_settings.AWX_ANALYTICS_CANDLEPIN_PROXY_URL = None
        proxy = get_proxy_url()
        assert proxy is None

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

    def test_is_cert_valid_unparseable(self):
        """Test is_cert_valid returns False for unparseable cert."""
        result = is_cert_valid('invalid-cert-data')
        assert result is False

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
    def test_run_candlepin_lifecycle_serial_mismatch(self, mock_parse, mock_client_class):
        """Test lifecycle when server cert serial differs from local cert."""
        # parse_cert is called:
        # 1. Parse local cert
        # 2. Parse server cert from get_consumer
        # 3. Parse new cert after regeneration for logging
        mock_parse.side_effect = [
            {'serial': '123', 'cn': 'test', 'not_after': '2027-01-01', 'days_remaining': 100},  # Local cert
            {'serial': '456', 'cn': 'test', 'not_after': '2027-01-01', 'days_remaining': 100},  # Server cert (different serial!)
            {'serial': '789', 'cn': 'test', 'not_after': '2027-02-01', 'days_remaining': 130},  # Regenerated cert
        ]

        mock_client = mock.Mock()
        mock_client.checkin.return_value = True
        mock_client.get_consumer.return_value = {'uuid': 'consumer-uuid', 'idCert': {'cert': 'server-cert-pem'}}
        mock_client.regenerate_cert.return_value = ('regenerated-cert', 'regenerated-key')
        mock_client_class.return_value = mock_client

        cert_pem, key_pem = run_candlepin_lifecycle('local-cert', 'local-key', 'consumer-uuid', renewal_days=30)

        # Should return regenerated cert due to serial mismatch
        assert cert_pem == 'regenerated-cert'
        assert key_pem == 'regenerated-key'
        mock_client.regenerate_cert.assert_called_once()

    @mock.patch('awx.main.utils.candlepin.lifecycle.CandlepinClient')
    @mock.patch('awx.main.utils.candlepin.lifecycle.parse_cert')
    def test_run_candlepin_lifecycle_serial_match(self, mock_parse, mock_client_class):
        """Test lifecycle when server cert serial matches local cert (no action needed)."""
        # parse_cert is called:
        # 1. Parse local cert
        # 2. Parse server cert from get_consumer (same serial)
        # 3. In needs_renewal() - cert is healthy, no renewal
        mock_parse.side_effect = [
            {'serial': '123', 'cn': 'test', 'not_after': '2027-01-01', 'days_remaining': 100},  # Local cert
            {'serial': '123', 'cn': 'test', 'not_after': '2027-01-01', 'days_remaining': 100},  # Server cert (same serial)
            {'serial': '123', 'cn': 'test', 'not_after': '2027-01-01', 'days_remaining': 100},  # needs_renewal check
        ]

        mock_client = mock.Mock()
        mock_client.checkin.return_value = True
        mock_client.get_consumer.return_value = {'uuid': 'consumer-uuid', 'idCert': {'cert': 'server-cert-pem'}}
        mock_client_class.return_value = mock_client

        cert_pem, key_pem = run_candlepin_lifecycle('local-cert', 'local-key', 'consumer-uuid', renewal_days=30)

        # Should return original cert since serial matches and cert is healthy
        assert cert_pem == 'local-cert'
        assert key_pem == 'local-key'
        mock_client.regenerate_cert.assert_not_called()
