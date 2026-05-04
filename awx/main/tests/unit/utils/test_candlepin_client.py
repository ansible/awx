# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

import os
from unittest import mock

import pytest
import requests

from awx.main.utils.candlepin.client import CandlepinClient, _temp_cert_files


class TestCandlepinClient:
    """Tests for CandlepinClient."""

    def test_base_url_required(self):
        """Test base_url parameter is required."""
        client = CandlepinClient(base_url='https://subscription.rhsm.redhat.com/subscription')
        assert client.base_url == 'https://subscription.rhsm.redhat.com/subscription'

    def test_custom_url(self):
        """Test custom Candlepin URL."""
        client = CandlepinClient(base_url='https://custom.example.com/candlepin')
        assert client.base_url == 'https://custom.example.com/candlepin'

    def test_verify_tls_enabled_by_default(self):
        """Test TLS verification is enabled by default."""
        client = CandlepinClient(base_url='https://test.example.com')
        assert client.verify is True

    def test_verify_tls_with_ca(self):
        """Test TLS verification with custom CA."""
        client = CandlepinClient(base_url='https://test.example.com', candlepin_ca='/path/to/ca.pem')
        assert client.verify == '/path/to/ca.pem'

    def test_verify_tls_disabled(self):
        """Test TLS verification can be explicitly disabled."""
        client = CandlepinClient(base_url='https://test.example.com', verify_tls=False)
        assert client.verify is False

    def test_proxy_configuration(self):
        """Test proxy configuration."""
        client = CandlepinClient(base_url='https://test.example.com', proxy='http://proxy.example.com:8080')
        assert client.proxies == {'https': 'http://proxy.example.com:8080', 'http': 'http://proxy.example.com:8080'}

    def test_https_proxy_configuration(self):
        """Test HTTPS proxy configuration."""
        client = CandlepinClient(base_url='https://test.example.com', proxy='https://proxy.example.com:8443')
        assert client.proxies == {'https': 'https://proxy.example.com:8443', 'http': 'http://proxy.example.com:8443'}

    def test_temp_cert_files_cleanup(self):
        """Test temporary certificate files are created and cleaned up."""
        cert_pem = '-----BEGIN CERTIFICATE-----\ntest_cert\n-----END CERTIFICATE-----'
        key_pem = '-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----'

        with _temp_cert_files(cert_pem, key_pem) as (cert_path, key_path):
            assert os.path.exists(cert_path)
            assert os.path.exists(key_path)
            # Verify file permissions
            cert_stat = os.stat(cert_path)
            assert oct(cert_stat.st_mode)[-3:] == '600'

        # Verify cleanup
        assert not os.path.exists(cert_path)
        assert not os.path.exists(key_path)

    @mock.patch('awx.main.utils.candlepin.client.requests.post')
    def test_register_consumer_success(self, mock_post):
        """Test successful consumer registration."""
        mock_response = mock.Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'uuid': 'test-consumer-uuid',
            'idCert': {
                'cert': '-----BEGIN CERTIFICATE-----\ncert_data\n-----END CERTIFICATE-----',
                'key': '-----BEGIN PRIVATE KEY-----\nkey_data\n-----END PRIVATE KEY-----',
            },
        }
        mock_post.return_value = mock_response

        client = CandlepinClient(base_url='https://test.example.com')
        cert_pem, key_pem, consumer_uuid = client.register_consumer('test_user', 'test_pass', 'test_org', install_uuid='test-install-uuid')

        assert consumer_uuid == 'test-consumer-uuid'
        assert '-----BEGIN CERTIFICATE-----' in cert_pem
        assert '-----BEGIN PRIVATE KEY-----' in key_pem

    @mock.patch('awx.main.utils.candlepin.client.requests.put')
    def test_checkin_success(self, mock_put):
        """Test successful check-in."""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_put.return_value = mock_response

        client = CandlepinClient(base_url='https://test.example.com')
        cert_pem = '-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----'
        key_pem = '-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----'

        result = client.checkin('test-uuid', cert_pem, key_pem)
        assert result is True

    @mock.patch('awx.main.utils.candlepin.client.requests.get')
    def test_get_consumer_success(self, mock_get):
        """Test successful consumer retrieval."""
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'uuid': 'test-consumer-uuid',
            'name': 'aap-12345678',
            'idCert': {'cert': '-----BEGIN CERTIFICATE-----\nserver_cert\n-----END CERTIFICATE-----', 'serial': {'serial': 123456789}},
        }
        mock_get.return_value = mock_response

        client = CandlepinClient(base_url='https://test.example.com')
        cert_pem = '-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----'
        key_pem = '-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----'

        result = client.get_consumer('test-uuid', cert_pem, key_pem)
        assert result is not None
        assert result['uuid'] == 'test-consumer-uuid'
        assert 'idCert' in result

    @mock.patch('awx.main.utils.candlepin.client.requests.get')
    def test_get_consumer_failure(self, mock_get):
        """Test consumer retrieval with non-200 status."""
        mock_response = mock.Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response

        client = CandlepinClient(base_url='https://test.example.com')
        cert_pem = '-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----'
        key_pem = '-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----'

        result = client.get_consumer('test-uuid', cert_pem, key_pem)
        assert result is None

    @mock.patch('awx.main.utils.candlepin.client.requests.get')
    def test_get_consumer_exception(self, mock_get):
        """Test consumer retrieval with network exception."""
        mock_get.side_effect = Exception('Network error')

        client = CandlepinClient(base_url='https://test.example.com')
        cert_pem = '-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----'
        key_pem = '-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----'

        result = client.get_consumer('test-uuid', cert_pem, key_pem)
        assert result is None

    @mock.patch('awx.main.utils.candlepin.client.requests.post')
    def test_regenerate_cert_success(self, mock_post):
        """Test successful certificate regeneration."""
        mock_response = mock.Mock()
        mock_response.ok = True
        mock_response.json.return_value = {
            'idCert': {
                'cert': '-----BEGIN CERTIFICATE-----\nnew_cert\n-----END CERTIFICATE-----',
                'key': '-----BEGIN PRIVATE KEY-----\nnew_key\n-----END PRIVATE KEY-----',
            }
        }
        mock_post.return_value = mock_response

        client = CandlepinClient(base_url='https://test.example.com')
        old_cert = '-----BEGIN CERTIFICATE-----\nold\n-----END CERTIFICATE-----'
        old_key = '-----BEGIN PRIVATE KEY-----\nold\n-----END PRIVATE KEY-----'

        new_cert, new_key = client.regenerate_cert('test-uuid', old_cert, old_key)
        assert 'new_cert' in new_cert
        assert 'new_key' in new_key

    @mock.patch('awx.main.utils.candlepin.client.requests.post')
    def test_register_consumer_timeout(self, mock_post):
        """Test consumer registration handles timeout."""
        mock_post.side_effect = requests.exceptions.Timeout('Connection timeout')

        client = CandlepinClient(base_url='https://test.example.com')

        with pytest.raises(RuntimeError, match='Candlepin register_consumer network error: Connection timeout'):
            client.register_consumer('test_user', 'test_pass', 'test_org')

    @mock.patch('awx.main.utils.candlepin.client.requests.post')
    def test_register_consumer_connection_error(self, mock_post):
        """Test consumer registration handles connection error."""
        mock_post.side_effect = requests.exceptions.ConnectionError('Failed to connect')

        client = CandlepinClient(base_url='https://test.example.com')

        with pytest.raises(RuntimeError, match='Candlepin register_consumer network error: Failed to connect'):
            client.register_consumer('test_user', 'test_pass', 'test_org')

    @mock.patch('awx.main.utils.candlepin.client.requests.post')
    def test_register_consumer_401_unauthorized(self, mock_post):
        """Test consumer registration handles 401 unauthorized (invalid credentials)."""
        mock_response = mock.Mock()
        mock_response.ok = False
        mock_response.status_code = 401
        mock_response.text = 'Invalid credentials'
        mock_post.return_value = mock_response

        client = CandlepinClient(base_url='https://test.example.com')

        with pytest.raises(RuntimeError, match='Candlepin register_consumer failed with status 401'):
            client.register_consumer('bad_user', 'bad_pass', 'test_org')

    @mock.patch('awx.main.utils.candlepin.client.requests.put')
    def test_checkin_timeout(self, mock_put):
        """Test check-in handles timeout gracefully."""
        mock_put.side_effect = requests.exceptions.Timeout('Connection timeout')

        client = CandlepinClient(base_url='https://test.example.com')
        cert_pem = '-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----'
        key_pem = '-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----'

        result = client.checkin('test-uuid', cert_pem, key_pem)
        assert result is False

    @mock.patch('awx.main.utils.candlepin.client.requests.put')
    def test_checkin_410_gone_revoked_cert(self, mock_put):
        """Test check-in returns False for 410 Gone (consumer deleted/cert revoked)."""
        mock_response = mock.Mock()
        mock_response.status_code = 410
        mock_put.return_value = mock_response

        client = CandlepinClient(base_url='https://test.example.com')
        cert_pem = '-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----'
        key_pem = '-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----'

        result = client.checkin('test-uuid', cert_pem, key_pem)
        assert result is False

    @mock.patch('awx.main.utils.candlepin.client.requests.put')
    def test_checkin_403_forbidden_invalid_cert(self, mock_put):
        """Test check-in returns False for 403 Forbidden (invalid certificate)."""
        mock_response = mock.Mock()
        mock_response.status_code = 403
        mock_put.return_value = mock_response

        client = CandlepinClient(base_url='https://test.example.com')
        cert_pem = '-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----'
        key_pem = '-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----'

        result = client.checkin('test-uuid', cert_pem, key_pem)
        assert result is False

    @mock.patch('awx.main.utils.candlepin.client.requests.get')
    def test_get_consumer_timeout(self, mock_get):
        """Test get_consumer handles timeout gracefully."""
        mock_get.side_effect = requests.exceptions.Timeout('Connection timeout')

        client = CandlepinClient(base_url='https://test.example.com')
        cert_pem = '-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----'
        key_pem = '-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----'

        result = client.get_consumer('test-uuid', cert_pem, key_pem)
        assert result is None

    @mock.patch('awx.main.utils.candlepin.client.requests.get')
    def test_get_consumer_410_gone_consumer_deleted(self, mock_get):
        """Test get_consumer returns None for 410 Gone (consumer deleted)."""
        mock_response = mock.Mock()
        mock_response.status_code = 410
        mock_get.return_value = mock_response

        client = CandlepinClient(base_url='https://test.example.com')
        cert_pem = '-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----'
        key_pem = '-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----'

        result = client.get_consumer('test-uuid', cert_pem, key_pem)
        assert result is None

    @mock.patch('awx.main.utils.candlepin.client.requests.post')
    def test_regenerate_cert_timeout(self, mock_post):
        """Test certificate regeneration handles timeout."""
        mock_post.side_effect = requests.exceptions.Timeout('Connection timeout during cert regeneration')

        client = CandlepinClient(base_url='https://test.example.com')
        cert_pem = '-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----'
        key_pem = '-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----'

        with pytest.raises(RuntimeError, match='Candlepin regenerate_cert network error for consumer test-uuid'):
            client.regenerate_cert('test-uuid', cert_pem, key_pem)

    @mock.patch('awx.main.utils.candlepin.client.requests.post')
    def test_regenerate_cert_410_gone_consumer_deleted(self, mock_post):
        """Test certificate regeneration handles 410 Gone (consumer deleted)."""
        mock_response = mock.Mock()
        mock_response.ok = False
        mock_response.status_code = 410
        mock_response.text = 'Consumer has been deleted'
        mock_post.return_value = mock_response

        client = CandlepinClient(base_url='https://test.example.com')
        cert_pem = '-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----'
        key_pem = '-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----'

        with pytest.raises(RuntimeError, match='Candlepin regenerate_cert failed with status 410'):
            client.regenerate_cert('test-uuid', cert_pem, key_pem)

    @mock.patch('awx.main.utils.candlepin.client.requests.post')
    def test_regenerate_cert_403_forbidden_revoked_cert(self, mock_post):
        """Test certificate regeneration handles 403 Forbidden (revoked certificate)."""
        mock_response = mock.Mock()
        mock_response.ok = False
        mock_response.status_code = 403
        mock_response.text = 'Certificate has been revoked'
        mock_post.return_value = mock_response

        client = CandlepinClient(base_url='https://test.example.com')
        cert_pem = '-----BEGIN CERTIFICATE-----\ntest\n-----END CERTIFICATE-----'
        key_pem = '-----BEGIN PRIVATE KEY-----\ntest\n-----END PRIVATE KEY-----'

        with pytest.raises(RuntimeError, match='Candlepin regenerate_cert failed with status 403'):
            client.regenerate_cert('test-uuid', cert_pem, key_pem)

    def test_temp_cert_files_exception_cleanup(self):
        """Test temporary certificate files are cleaned up even when exception occurs."""
        cert_pem = '-----BEGIN CERTIFICATE-----\ntest_cert\n-----END CERTIFICATE-----'
        key_pem = '-----BEGIN PRIVATE KEY-----\ntest_key\n-----END PRIVATE KEY-----'

        cert_path = None
        key_path = None

        try:
            with _temp_cert_files(cert_pem, key_pem) as (cp, kp):
                cert_path = cp
                key_path = kp
                assert os.path.exists(cert_path)
                assert os.path.exists(key_path)
                # Simulate an exception
                raise ValueError('Simulated error')
        except ValueError:
            pass

        # Files should still be cleaned up after exception
        assert not os.path.exists(cert_path)
        assert not os.path.exists(key_path)
