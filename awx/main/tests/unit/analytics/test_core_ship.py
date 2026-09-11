# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

"""Tests for analytics ship() function with mTLS authentication."""

import os
import tempfile
from unittest import mock

from django.test.utils import override_settings

from awx.main.analytics.core import ship, _get_cert_upload_url, _log_shipping_response


class TestGetCertUploadUrl:
    """Test _get_cert_upload_url() helper function."""

    def test_adds_cert_subdomain(self):
        """Test that 'cert.' is added to hostname."""
        url = 'https://analytics.example.com/api/ingress/v1/upload'
        result = _get_cert_upload_url(url)
        assert result == 'https://cert.analytics.example.com/api/ingress/v1/upload'

    def test_preserves_existing_cert_subdomain(self):
        """Test that existing 'cert.' subdomain is preserved."""
        url = 'https://cert.analytics.example.com/api/ingress/v1/upload'
        result = _get_cert_upload_url(url)
        assert result == 'https://cert.analytics.example.com/api/ingress/v1/upload'


class TestShipMTLS:
    """Test ship() function's mTLS authentication path."""

    def setup_method(self):
        """Create a temporary tarball for testing."""
        self.temp_file = tempfile.NamedTemporaryFile(mode='wb', suffix='.tar.gz', delete=False)
        self.temp_file.write(b'test tarball content')
        self.temp_file.close()
        self.tarball_path = self.temp_file.name

    def teardown_method(self):
        """Clean up temporary tarball."""
        if os.path.exists(self.tarball_path):
            os.unlink(self.tarball_path)

    @override_settings(
        AUTOMATION_ANALYTICS_URL='https://analytics.example.com/api/ingress/v1/upload',
        INSIGHTS_AGENT_MIME='application/vnd.redhat.tower.analytics+tgz',
        INSIGHTS_CERT_PATH='/etc/pki/tls/certs/ca-bundle.crt',
        REDHAT_USERNAME='test_user',
        REDHAT_PASSWORD='test_pass',  # NOSONAR
        AWX_TASK_ENV={},
    )
    @mock.patch('awx.main.analytics.core.get_awx_http_client_headers')
    @mock.patch('awx.main.analytics.core._temp_cert_files')
    @mock.patch('awx.main.analytics.core.get_or_generate_candlepin_certificate')
    @mock.patch('awx.main.analytics.core.requests.Session')
    def test_ship_with_mtls_success(self, mock_session_class, mock_get_cert, mock_temp_files, mock_headers):
        """Test successful upload with mTLS certificate authentication."""
        # Mock headers to avoid database access
        mock_headers.return_value = {'Content-Type': 'application/json'}

        # Mock certificate retrieval
        mock_get_cert.return_value = ('cert-pem-data', 'key-pem-data')

        # Mock temp files context manager
        mock_temp_files.return_value.__enter__.return_value = ('/tmp/cert.pem', '/tmp/key.pem')
        mock_temp_files.return_value.__exit__.return_value = None

        # Mock successful mTLS response
        mock_response = mock.Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {'request_id': 'abc-123', 'account_number': '12345', 'org_id': '67890'}
        mock_session = mock.Mock()
        mock_session.headers = {}
        mock_session.post.return_value = mock_response
        mock_session_class.return_value = mock_session

        result = ship(self.tarball_path)

        assert result is True
        mock_get_cert.assert_called_once()
        mock_temp_files.assert_called_once_with('cert-pem-data', 'key-pem-data')
        mock_session.post.assert_called_once()
        mock_response.json.assert_called_once()

        # Verify cert URL is used (cert. subdomain added)
        call_args = mock_session.post.call_args
        assert call_args[0][0] == 'https://cert.analytics.example.com/api/ingress/v1/upload'

        # Verify mTLS cert was used
        call_kwargs = call_args[1]
        assert call_kwargs['cert'] == ('/tmp/cert.pem', '/tmp/key.pem')

    @override_settings(
        AUTOMATION_ANALYTICS_URL='https://analytics.example.com/api/ingress/v1/upload',
        INSIGHTS_AGENT_MIME='application/vnd.redhat.tower.analytics+tgz',
        INSIGHTS_CERT_PATH='/etc/pki/tls/certs/ca-bundle.crt',
        REDHAT_USERNAME='test_user',
        REDHAT_PASSWORD='test_pass',  # NOSONAR
        AWX_TASK_ENV={},
    )
    @mock.patch('awx.main.analytics.core.get_awx_http_client_headers')
    @mock.patch('awx.main.analytics.core.OIDCClient')
    @mock.patch('awx.main.analytics.core._temp_cert_files')
    @mock.patch('awx.main.analytics.core.get_or_generate_candlepin_certificate')
    @mock.patch('awx.main.analytics.core.requests.Session')
    def test_ship_mtls_fallback_to_oidc_on_cert_failure(self, mock_session_class, mock_get_cert, mock_temp_files, mock_oidc_client, mock_headers):
        """Test fallback to OIDC auth when mTLS cert authentication fails."""
        # Mock headers to avoid database access
        mock_headers.return_value = {'Content-Type': 'application/json'}

        # Mock certificate retrieval
        mock_get_cert.return_value = ('cert-pem-data', 'key-pem-data')

        # Mock temp files context manager
        mock_temp_files.return_value.__enter__.return_value = ('/tmp/cert.pem', '/tmp/key.pem')
        mock_temp_files.return_value.__exit__.return_value = None

        # Mock failed mTLS response (401 Unauthorized)
        mock_mtls_response = mock.Mock()
        mock_mtls_response.status_code = 401
        mock_session = mock.Mock()
        mock_session.headers = {}
        mock_session.post.return_value = mock_mtls_response
        mock_session_class.return_value = mock_session

        # Mock successful OIDC response
        mock_oidc_response = mock.Mock()
        mock_oidc_response.status_code = 200
        mock_oidc_response.json.return_value = {'request_id': 'oidc-456', 'account_number': '12345', 'org_id': '67890'}
        mock_oidc_instance = mock.Mock()
        mock_oidc_instance.make_request.return_value = mock_oidc_response
        mock_oidc_client.return_value = mock_oidc_instance

        result = ship(self.tarball_path)

        assert result is True
        # Both mTLS and OIDC should be attempted
        assert mock_session.post.call_count == 1
        mock_oidc_instance.make_request.assert_called_once()

        # Verify mTLS used cert URL
        mtls_call_args = mock_session.post.call_args
        assert mtls_call_args[0][0] == 'https://cert.analytics.example.com/api/ingress/v1/upload'

        # Verify OIDC used original URL
        oidc_call_args = mock_oidc_instance.make_request.call_args
        assert oidc_call_args[0][1] == 'https://analytics.example.com/api/ingress/v1/upload'

    @override_settings(
        AUTOMATION_ANALYTICS_URL='https://analytics.example.com/api/ingress/v1/upload',
        INSIGHTS_AGENT_MIME='application/vnd.redhat.tower.analytics+tgz',
        INSIGHTS_CERT_PATH='/etc/pki/tls/certs/ca-bundle.crt',
        REDHAT_USERNAME='test_user',
        REDHAT_PASSWORD='test_pass',  # NOSONAR
        AWX_TASK_ENV={},
    )
    @mock.patch('awx.main.analytics.core.get_awx_http_client_headers')
    @mock.patch('awx.main.analytics.core._temp_cert_files')
    @mock.patch('awx.main.analytics.core.get_or_generate_candlepin_certificate')
    @mock.patch('awx.main.analytics.core.OIDCClient')
    @mock.patch('awx.main.analytics.core.requests.Session')
    def test_ship_mtls_exception_fallback_to_oidc(self, mock_session_class, mock_oidc_client, mock_get_cert, mock_temp_files, mock_headers):
        """Test fallback to OIDC auth when mTLS raises an exception."""
        # Mock headers to avoid database access
        mock_headers.return_value = {'Content-Type': 'application/json'}

        # Mock certificate retrieval
        mock_get_cert.return_value = ('cert-pem-data', 'key-pem-data')

        # Mock temp files context manager raising an exception
        mock_temp_files.return_value.__enter__.side_effect = OSError('Temp file creation failed')

        # Mock successful OIDC response
        mock_oidc_response = mock.Mock()
        mock_oidc_response.status_code = 200
        mock_oidc_response.json.return_value = {'request_id': 'oidc-789', 'account_number': '12345', 'org_id': '67890'}
        mock_oidc_instance = mock.Mock()
        mock_oidc_instance.make_request.return_value = mock_oidc_response
        mock_oidc_client.return_value = mock_oidc_instance

        mock_session = mock.Mock()
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        result = ship(self.tarball_path)

        assert result is True
        # mTLS should fail, OIDC should succeed
        mock_oidc_instance.make_request.assert_called_once()

    @override_settings(
        AUTOMATION_ANALYTICS_URL='https://analytics.example.com/api/ingress/v1/upload',
        INSIGHTS_AGENT_MIME='application/vnd.redhat.tower.analytics+tgz',
        INSIGHTS_CERT_PATH='/etc/pki/tls/certs/ca-bundle.crt',
        REDHAT_USERNAME='test_user',
        REDHAT_PASSWORD='test_pass',  # NOSONAR
        AWX_TASK_ENV={},
    )
    @mock.patch('awx.main.analytics.core.get_awx_http_client_headers')
    @mock.patch('awx.main.analytics.core.OIDCClient')
    @mock.patch('awx.main.analytics.core.get_or_generate_candlepin_certificate')
    @mock.patch('awx.main.analytics.core.requests.Session')
    def test_ship_no_certificate_available(self, mock_session_class, mock_get_cert, mock_oidc_client, mock_headers):
        """Test ship() when no Candlepin certificate is available."""
        # Mock headers to avoid database access
        mock_headers.return_value = {'Content-Type': 'application/json'}

        # Mock no certificate available
        mock_get_cert.return_value = (None, None)

        # Mock successful OIDC response
        mock_oidc_response = mock.Mock()
        mock_oidc_response.status_code = 200
        mock_oidc_response.json.return_value = {'request_id': 'oidc-no-cert', 'account_number': '12345', 'org_id': '67890'}
        mock_oidc_instance = mock.Mock()
        mock_oidc_instance.make_request.return_value = mock_oidc_response
        mock_oidc_client.return_value = mock_oidc_instance

        mock_session = mock.Mock()
        mock_session.headers = {}
        mock_session_class.return_value = mock_session

        result = ship(self.tarball_path)

        assert result is True
        # Should skip mTLS and go straight to OIDC
        mock_oidc_instance.make_request.assert_called_once()

    @override_settings(
        AUTOMATION_ANALYTICS_URL='https://analytics.example.com/api/ingress/v1/upload',
        INSIGHTS_AGENT_MIME='application/vnd.redhat.tower.analytics+tgz',
        INSIGHTS_CERT_PATH='/etc/pki/tls/certs/ca-bundle.crt',
        REDHAT_USERNAME='test_user',
        REDHAT_PASSWORD='test_pass',  # NOSONAR
        AWX_TASK_ENV={},
    )
    @mock.patch('awx.main.analytics.core.get_awx_http_client_headers')
    @mock.patch('awx.main.analytics.core.OIDCClient')
    @mock.patch('awx.main.analytics.core._temp_cert_files')
    @mock.patch('awx.main.analytics.core.get_or_generate_candlepin_certificate')
    @mock.patch('awx.main.analytics.core.requests.Session')
    def test_ship_both_auth_methods_fail(self, mock_session_class, mock_get_cert, mock_temp_files, mock_oidc_client, mock_headers):
        """Test ship() when both mTLS and OIDC authentication fail."""
        # Mock headers to avoid database access
        mock_headers.return_value = {'Content-Type': 'application/json'}

        # Mock certificate retrieval
        mock_get_cert.return_value = ('cert-pem-data', 'key-pem-data')

        # Mock temp files context manager
        mock_temp_files.return_value.__enter__.return_value = ('/tmp/cert.pem', '/tmp/key.pem')
        mock_temp_files.return_value.__exit__.return_value = None

        # Mock failed mTLS response
        mock_mtls_response = mock.Mock()
        mock_mtls_response.status_code = 401
        mock_session = mock.Mock()
        mock_session.headers = {}
        mock_session.post.return_value = mock_mtls_response
        mock_session_class.return_value = mock_session

        # Mock failed OIDC response
        mock_oidc_response = mock.Mock()
        mock_oidc_response.status_code = 403
        mock_oidc_response.text = 'Forbidden'
        mock_oidc_instance = mock.Mock()
        mock_oidc_instance.make_request.return_value = mock_oidc_response
        mock_oidc_client.return_value = mock_oidc_instance

        result = ship(self.tarball_path)

        assert result is False
        mock_session.post.assert_called_once()
        mock_oidc_instance.make_request.assert_called_once()


class TestLogShippingResponse:
    """Test _log_shipping_response() helper function."""

    def test_logs_response_fields(self):
        """Test that request_id, account_number, and org_id are logged."""
        response = mock.Mock()
        response.json.return_value = {'request_id': 'req-abc', 'account_number': '99999', 'org_id': '11111'}
        with mock.patch('awx.main.analytics.core.logger') as mock_logger:
            _log_shipping_response(response, '/tmp/analytics.tar.gz')
            mock_logger.info.assert_called_once_with("Analytics upload successful: file=analytics.tar.gz request_id=req-abc account_number=99999 org_id=11111")

    def test_logs_unknown_for_missing_fields(self):
        """Test fallback to 'unknown' when response fields are absent."""
        response = mock.Mock()
        response.json.return_value = {}
        with mock.patch('awx.main.analytics.core.logger') as mock_logger:
            _log_shipping_response(response, '/tmp/analytics.tar.gz')
            mock_logger.info.assert_called_once_with(
                "Analytics upload successful: file=analytics.tar.gz request_id=unknown account_number=unknown org_id=unknown"
            )

    def test_graceful_fallback_on_json_error(self):
        """Test fallback log when response body is not valid JSON."""
        response = mock.Mock()
        response.json.side_effect = ValueError("No JSON")
        response.status_code = 202
        with mock.patch('awx.main.analytics.core.logger') as mock_logger:
            _log_shipping_response(response, '/tmp/analytics.tar.gz')
            mock_logger.info.assert_called_once_with("Analytics upload successful: file=analytics.tar.gz status=202")
