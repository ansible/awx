# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

import os
import pytest
from datetime import datetime, timedelta, timezone
from unittest import mock

from awx.main.utils.candlepin.lifecycle import (
    parse_cert,
    is_cert_valid,
    needs_renewal,
    run_candlepin_lifecycle,
    get_candlepin_url,
    get_renewal_days,
    get_candlepin_ca,
    RENEWAL_DAYS_DEFAULT,
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

    def test_get_candlepin_url_default(self):
        """Test default Candlepin URL."""
        with mock.patch.dict(os.environ, {}, clear=True):
            url = get_candlepin_url()
            assert url == 'https://subscription.rhsm.redhat.com/subscription'

    def test_get_candlepin_url_from_env(self):
        """Test Candlepin URL from environment variable."""
        with mock.patch.dict(os.environ, {'METRICS_UTILITY_CANDLEPIN_URL': 'https://custom.example.com'}):
            url = get_candlepin_url()
            assert url == 'https://custom.example.com'

    def test_get_renewal_days_default(self):
        """Test default renewal days."""
        with mock.patch.dict(os.environ, {}, clear=True):
            days = get_renewal_days()
            assert days == RENEWAL_DAYS_DEFAULT

    def test_get_renewal_days_from_env(self):
        """Test renewal days from environment variable."""
        with mock.patch.dict(os.environ, {'METRICS_UTILITY_CANDLEPIN_RENEWAL_DAYS': '45'}):
            days = get_renewal_days()
            assert days == 45

    def test_get_renewal_days_invalid(self):
        """Test invalid renewal days falls back to default."""
        with mock.patch.dict(os.environ, {'METRICS_UTILITY_CANDLEPIN_RENEWAL_DAYS': 'invalid'}):
            days = get_renewal_days()
            assert days == RENEWAL_DAYS_DEFAULT

    def test_get_candlepin_ca_none(self):
        """Test Candlepin CA returns None when not set."""
        with mock.patch.dict(os.environ, {}, clear=True):
            ca = get_candlepin_ca()
            assert ca is None

    def test_get_candlepin_ca_from_env(self):
        """Test Candlepin CA from environment variable."""
        with mock.patch.dict(os.environ, {'METRICS_UTILITY_CANDLEPIN_CA': '/path/to/ca.pem'}):
            ca = get_candlepin_ca()
            assert ca == '/path/to/ca.pem'

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
        mock_parse.return_value = {
            'days_remaining': 10
        }

        result = needs_renewal('fake-cert', days_before_expiry=30)
        assert result is True

    @mock.patch('awx.main.utils.candlepin.lifecycle.parse_cert')
    def test_needs_renewal_false(self, mock_parse):
        """Test needs_renewal returns False when cert has time remaining."""
        mock_parse.return_value = {
            'days_remaining': 100
        }

        result = needs_renewal('fake-cert', days_before_expiry=30)
        assert result is False

    @mock.patch('awx.main.utils.candlepin.lifecycle.CandlepinClient')
    @mock.patch('awx.main.utils.candlepin.lifecycle.parse_cert')
    def test_run_candlepin_lifecycle_no_renewal_needed(self, mock_parse, mock_client_class):
        """Test lifecycle when no renewal is needed."""
        mock_parse.return_value = {
            'serial': '123',
            'cn': 'test',
            'not_after': '2027-01-01T00:00:00+00:00',
            'days_remaining': 100
        }

        mock_client = mock.Mock()
        mock_client.checkin.return_value = True
        mock_client_class.return_value = mock_client

        cert_pem, key_pem = run_candlepin_lifecycle(
            'cert-pem', 'key-pem', 'consumer-uuid',
            candlepin_url='https://test.example.com',
            renewal_days=30
        )

        assert cert_pem == 'cert-pem'
        assert key_pem == 'key-pem'
        mock_client.checkin.assert_called_once()
        mock_client.regenerate_cert.assert_not_called()

    @mock.patch('awx.main.utils.candlepin.lifecycle.CandlepinClient')
    @mock.patch('awx.main.utils.candlepin.lifecycle.parse_cert')
    def test_run_candlepin_lifecycle_with_renewal(self, mock_parse, mock_client_class):
        """Test lifecycle when renewal is needed."""
        # First call for old cert, second for new cert
        mock_parse.side_effect = [
            {'serial': '123', 'cn': 'test', 'not_after': '2026-02-01', 'days_remaining': 10},
            {'serial': '456', 'cn': 'test', 'not_after': '2027-02-01', 'days_remaining': 365}
        ]

        mock_client = mock.Mock()
        mock_client.checkin.return_value = True
        mock_client.regenerate_cert.return_value = ('new-cert', 'new-key')
        mock_client_class.return_value = mock_client

        cert_pem, key_pem = run_candlepin_lifecycle(
            'old-cert', 'old-key', 'consumer-uuid',
            renewal_days=30
        )

        assert cert_pem == 'new-cert'
        assert key_pem == 'new-key'
        mock_client.regenerate_cert.assert_called_once()
