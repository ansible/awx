# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

import os
from unittest import mock

from awx.main.utils.candlepin.client import CandlepinClient, _temp_cert_files


class TestCandlepinClient:
    """Tests for CandlepinClient."""

    def test_base_url_required(self):
        """Test base_url parameter is required."""
        client = CandlepinClient(base_url='https://subscription.example.com/candlepin')
        assert client.base_url == 'https://subscription.example.com/candlepin'

    def test_verify_tls_enabled_by_default(self):
        """Test TLS verification is enabled by default."""
        client = CandlepinClient(base_url='https://test.example.com')
        assert client.verify is True

    def test_verify_tls_with_ca(self):
        """Test TLS verification with custom CA."""
        client = CandlepinClient(base_url='https://test.example.com', candlepin_ca='/path/to/ca.pem')
        assert client.verify == '/path/to/ca.pem'

    def test_proxy_configuration(self):
        """Test proxy configuration."""
        client = CandlepinClient(base_url='https://test.example.com', proxy='http://proxy.example.com:8080')
        assert client.proxies == {'https': 'http://proxy.example.com:8080', 'http': 'http://proxy.example.com:8080'}

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
