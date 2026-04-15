# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

from unittest import mock

from awx.main.utils.licensing import (
    CANDLEPIN_UUID_PLACEHOLDER,
    SUBSCRIPTIONS_USERNAME_SETTING_KEY,
    SUBSCRIPTIONS_PASSWORD_SETTING_KEY,
    _fetch_candlepin_cert_from_db,
    _fetch_registration_credentials_from_db,
    _save_candlepin_cert_to_db,
    _save_candlepin_registration_to_db,
    _register_candlepin_consumer,
    _run_candlepin_lifecycle,
)


class TestCandlepinLicensing:
    """Tests for Candlepin integration in licensing module."""

    def test_constants(self):
        """Test Candlepin constants are defined."""
        assert CANDLEPIN_UUID_PLACEHOLDER == '00000000-0000-0000-0000-000000000000'
        assert SUBSCRIPTIONS_USERNAME_SETTING_KEY == 'SUBSCRIPTIONS_USERNAME'
        assert SUBSCRIPTIONS_PASSWORD_SETTING_KEY == 'SUBSCRIPTIONS_PASSWORD'

    @mock.patch('awx.main.models.CandlepinCertificate')
    def test_fetch_candlepin_cert_from_db(self, mock_cert_model):
        """Test fetching Candlepin cert from CandlepinCertificate model."""
        mock_instance = mock.Mock()
        mock_instance.cert_pem = 'cert-pem-data'
        mock_instance.key_pem = 'key-pem-data'
        mock_instance.consumer_uuid = 'test-uuid'
        mock_instance.has_valid_data.return_value = True
        mock_cert_model.get_instance.return_value = mock_instance

        cert, key, uuid = _fetch_candlepin_cert_from_db()

        assert cert == 'cert-pem-data'
        assert key == 'key-pem-data'
        assert uuid == 'test-uuid'

    @mock.patch('awx.main.models.CandlepinCertificate')
    def test_fetch_candlepin_cert_missing_data(self, mock_cert_model):
        """Test fetching Candlepin cert when not present."""
        mock_cert_model.get_instance.return_value = None

        cert, key, uuid = _fetch_candlepin_cert_from_db()

        assert cert is None
        assert key is None
        assert uuid is None

    @mock.patch('awx.main.models.CandlepinCertificate')
    def test_fetch_candlepin_cert_invalid_data(self, mock_cert_model):
        """Test fetching Candlepin cert with invalid/placeholder data."""
        mock_instance = mock.Mock()
        mock_instance.has_valid_data.return_value = False
        mock_cert_model.get_instance.return_value = mock_instance

        cert, key, uuid = _fetch_candlepin_cert_from_db()

        assert cert is None
        assert key is None
        assert uuid is None

    @mock.patch('awx.main.utils.licensing.connection')
    def test_fetch_registration_credentials_from_db(self, mock_connection):
        """Test fetching registration credentials from database."""
        mock_cursor = mock.Mock()
        mock_cursor.fetchall.return_value = [
            ('SUBSCRIPTIONS_USERNAME', '"test_user"'),
            ('SUBSCRIPTIONS_PASSWORD', '"test_pass"'),
            ('LICENSE', '{"account_number": "test_org"}'),
            ('INSTALL_UUID', '"test-install-uuid"'),
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        username, password, org, install_uuid = _fetch_registration_credentials_from_db()

        assert username == 'test_user'
        assert password == 'test_pass'
        assert org == 'test_org'
        assert install_uuid == 'test-install-uuid'

    @mock.patch('awx.main.utils.licensing.parse_cert')
    @mock.patch('awx.main.models.CandlepinCertificate')
    def test_save_candlepin_cert_to_db(self, mock_cert_model, mock_parse_cert):
        """Test saving Candlepin cert to CandlepinCertificate model."""
        mock_instance = mock.Mock()
        mock_cert_model.get_or_create_instance.return_value = mock_instance

        mock_parse_cert.return_value = {
            'serial': '123456',
            'expires_at': '2027-01-01T00:00:00+00:00',
        }

        _save_candlepin_cert_to_db('new-cert', 'new-key')

        mock_cert_model.get_or_create_instance.assert_called_once()
        mock_instance.update_certificate.assert_called_once()
        call_kwargs = mock_instance.update_certificate.call_args[1]
        assert call_kwargs['cert_pem'] == 'new-cert'
        assert call_kwargs['key_pem'] == 'new-key'
        assert call_kwargs['serial_number'] == '123456'
        assert 'expires_at' in call_kwargs

    @mock.patch('awx.main.utils.licensing.parse_cert')
    @mock.patch('awx.main.models.CandlepinCertificate')
    def test_save_candlepin_registration_to_db(self, mock_cert_model, mock_parse_cert):
        """Test saving Candlepin registration to CandlepinCertificate model."""
        mock_instance = mock.Mock()
        mock_cert_model.get_or_create_instance.return_value = mock_instance

        mock_parse_cert.return_value = {
            'serial': '789012',
            'expires_at': '2027-01-01T00:00:00+00:00',
        }

        _save_candlepin_registration_to_db('cert', 'key', 'uuid')

        mock_cert_model.get_or_create_instance.assert_called_once()
        mock_instance.update_certificate.assert_called_once()
        call_kwargs = mock_instance.update_certificate.call_args[1]
        assert call_kwargs['cert_pem'] == 'cert'
        assert call_kwargs['key_pem'] == 'key'
        assert call_kwargs['consumer_uuid'] == 'uuid'
        assert call_kwargs['serial_number'] == '789012'
        assert 'expires_at' in call_kwargs

    @mock.patch('awx.main.utils.licensing._save_candlepin_registration_to_db')
    @mock.patch('awx.main.utils.licensing.CandlepinClient')
    @mock.patch('awx.main.utils.licensing._fetch_registration_credentials_from_db')
    def test_register_candlepin_consumer_success(self, mock_fetch_creds, mock_client_class, mock_save):
        """Test successful Candlepin consumer registration."""
        mock_fetch_creds.return_value = ('user', 'pass', 'org', 'install-uuid')

        mock_client = mock.Mock()
        mock_client.register_consumer.return_value = ('cert', 'key', 'uuid')
        mock_client_class.return_value = mock_client

        cert, key, uuid = _register_candlepin_consumer()

        assert cert == 'cert'
        assert key == 'key'
        assert uuid == 'uuid'
        mock_save.assert_called_once_with('cert', 'key', 'uuid')

    @mock.patch('awx.main.utils.licensing._fetch_registration_credentials_from_db')
    def test_register_candlepin_consumer_missing_credentials(self, mock_fetch_creds):
        """Test registration fails when credentials are missing."""
        mock_fetch_creds.return_value = (None, None, None, None)

        cert, key, uuid = _register_candlepin_consumer()

        assert cert is None
        assert key is None
        assert uuid is None

    @mock.patch('awx.main.utils.licensing._save_candlepin_cert_to_db')
    @mock.patch('awx.main.utils.licensing.run_candlepin_lifecycle')
    def test_run_candlepin_lifecycle_placeholder_uuid(self, mock_lifecycle, mock_save):
        """Test lifecycle is skipped with placeholder UUID."""
        cert, key = _run_candlepin_lifecycle('cert', 'key', CANDLEPIN_UUID_PLACEHOLDER)

        assert cert == 'cert'
        assert key == 'key'
        mock_lifecycle.assert_not_called()
        mock_save.assert_not_called()

    @mock.patch('awx.main.utils.licensing._save_candlepin_cert_to_db')
    @mock.patch('awx.main.utils.licensing.run_candlepin_lifecycle')
    def test_run_candlepin_lifecycle_with_renewal(self, mock_lifecycle, mock_save):
        """Test lifecycle with certificate renewal."""
        mock_lifecycle.return_value = ('new-cert', 'new-key')

        cert, key = _run_candlepin_lifecycle('old-cert', 'old-key', 'real-uuid')

        assert cert == 'new-cert'
        assert key == 'new-key'
        mock_lifecycle.assert_called_once()
        mock_save.assert_called_once_with('new-cert', 'new-key')

    @mock.patch('awx.main.utils.licensing.run_candlepin_lifecycle')
    def test_run_candlepin_lifecycle_error_handling(self, mock_lifecycle):
        """Test lifecycle error handling returns original cert."""
        mock_lifecycle.side_effect = Exception('Test error')

        cert, key = _run_candlepin_lifecycle('cert', 'key', 'uuid')

        # Should return original cert/key on error
        assert cert == 'cert'
        assert key == 'key'
