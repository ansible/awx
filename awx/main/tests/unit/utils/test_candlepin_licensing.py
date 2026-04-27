# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

from unittest import mock

import requests

from awx.main.utils.candlepin import (
    CANDLEPIN_UUID_PLACEHOLDER,
    _discover_org,
    _fetch_candlepin_cert_from_db,
    _fetch_registration_credentials_from_db,
    _save_candlepin_cert_to_db,
    _save_candlepin_registration_to_db,
    _register_candlepin_consumer,
    _run_candlepin_lifecycle,
    get_or_generate_candlepin_certificate,
)


class TestCandlepinLicensing:
    """Tests for Candlepin integration in licensing module."""

    def test_constants(self):
        """Test Candlepin constants are defined."""
        assert CANDLEPIN_UUID_PLACEHOLDER == '00000000-0000-0000-0000-000000000000'

    @mock.patch('awx.main.utils.candlepin.requests.get')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_ca')
    def test_discover_org_success(self, mock_get_ca, mock_requests_get):
        """Test successful organization discovery."""
        mock_get_ca.return_value = '/path/to/ca.pem'
        mock_response = mock.Mock()
        mock_response.json.return_value = [
            {'key': 'test_org', 'displayName': 'Test Organization'},
            {'key': 'other_org', 'displayName': 'Other Organization'},
        ]
        mock_requests_get.return_value = mock_response

        org = _discover_org('https://candlepin.example.com', 'test_user', 'test_pass')

        assert org == 'test_org'
        mock_requests_get.assert_called_once_with(
            'https://candlepin.example.com/users/test_user/owners',
            auth=('test_user', 'test_pass'),
            verify='/path/to/ca.pem',
            timeout=30,
        )

    @mock.patch('awx.main.utils.candlepin.requests.get')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_ca')
    def test_discover_org_no_ca(self, mock_get_ca, mock_requests_get):
        """Test organization discovery without custom CA (uses system certs)."""
        mock_get_ca.return_value = None
        mock_response = mock.Mock()
        mock_response.json.return_value = [{'key': 'test_org', 'displayName': 'Test Organization'}]
        mock_requests_get.return_value = mock_response

        org = _discover_org('https://candlepin.example.com', 'test_user', 'test_pass')

        assert org == 'test_org'
        # Should use True for verify when no CA is configured
        mock_requests_get.assert_called_once_with(
            'https://candlepin.example.com/users/test_user/owners',
            auth=('test_user', 'test_pass'),
            verify=True,
            timeout=30,
        )

    @mock.patch('awx.main.utils.candlepin.requests.get')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_ca')
    def test_discover_org_empty_list(self, mock_get_ca, mock_requests_get):
        """Test organization discovery when user has no organizations."""
        mock_get_ca.return_value = None
        mock_response = mock.Mock()
        mock_response.json.return_value = []
        mock_requests_get.return_value = mock_response

        org = _discover_org('https://candlepin.example.com', 'test_user', 'test_pass')

        assert org is None

    @mock.patch('awx.main.utils.candlepin.requests.get')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_ca')
    def test_discover_org_missing_key(self, mock_get_ca, mock_requests_get):
        """Test organization discovery when org key is missing from response."""
        mock_get_ca.return_value = None
        mock_response = mock.Mock()
        mock_response.json.return_value = [{'displayName': 'Test Organization'}]
        mock_requests_get.return_value = mock_response

        org = _discover_org('https://candlepin.example.com', 'test_user', 'test_pass')

        assert org is None

    @mock.patch('awx.main.utils.candlepin.requests.get')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_ca')
    def test_discover_org_http_error(self, mock_get_ca, mock_requests_get):
        """Test organization discovery handles HTTP errors."""
        mock_get_ca.return_value = None
        mock_requests_get.side_effect = requests.exceptions.HTTPError('401 Unauthorized')

        org = _discover_org('https://candlepin.example.com', 'test_user', 'test_pass')

        assert org is None

    @mock.patch('awx.main.utils.candlepin.requests.get')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_ca')
    def test_discover_org_connection_error(self, mock_get_ca, mock_requests_get):
        """Test organization discovery handles connection errors."""
        mock_get_ca.return_value = None
        mock_requests_get.side_effect = requests.exceptions.ConnectionError('Connection refused')

        org = _discover_org('https://candlepin.example.com', 'test_user', 'test_pass')

        assert org is None

    @mock.patch('awx.main.utils.candlepin.requests.get')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_ca')
    def test_discover_org_unexpected_error(self, mock_get_ca, mock_requests_get):
        """Test organization discovery handles unexpected exceptions."""
        mock_get_ca.return_value = None
        mock_requests_get.side_effect = Exception('Unexpected error')

        org = _discover_org('https://candlepin.example.com', 'test_user', 'test_pass')

        assert org is None

    @mock.patch('awx.main.utils.candlepin.settings')
    def test_fetch_candlepin_cert_from_db(self, mock_settings):
        """Test fetching Candlepin cert from conf_settings."""
        mock_settings.CANDLEPIN_CONSUMER_UUID = 'test-uuid'
        mock_settings.CANDLEPIN_CERT_PEM = 'cert-pem-data'
        mock_settings.CANDLEPIN_KEY_PEM = 'key-pem-data'

        cert, key, uuid = _fetch_candlepin_cert_from_db()

        assert cert == 'cert-pem-data'
        assert key == 'key-pem-data'
        assert uuid == 'test-uuid'

    @mock.patch('awx.main.utils.candlepin.settings')
    def test_fetch_candlepin_cert_invalid_data(self, mock_settings):
        """Test fetching Candlepin cert with invalid/placeholder data."""
        mock_settings.CANDLEPIN_CONSUMER_UUID = CANDLEPIN_UUID_PLACEHOLDER
        mock_settings.CANDLEPIN_CERT_PEM = 'cert-pem-data'
        mock_settings.CANDLEPIN_KEY_PEM = 'key-pem-data'

        cert, key, uuid = _fetch_candlepin_cert_from_db()

        assert cert is None
        assert key is None
        assert uuid is None

    @mock.patch('awx.main.utils.candlepin.settings')
    def test_fetch_candlepin_cert_empty_cert(self, mock_settings):
        """Test fetching Candlepin cert when cert_pem is empty."""
        mock_settings.CANDLEPIN_CONSUMER_UUID = 'test-uuid'
        mock_settings.CANDLEPIN_CERT_PEM = ''
        mock_settings.CANDLEPIN_KEY_PEM = 'key-pem-data'

        cert, key, uuid = _fetch_candlepin_cert_from_db()

        assert cert is None
        assert key is None
        assert uuid is None

    @mock.patch('awx.main.utils.candlepin.settings')
    def test_fetch_candlepin_cert_empty_key(self, mock_settings):
        """Test fetching Candlepin cert when key_pem is empty."""
        mock_settings.CANDLEPIN_CONSUMER_UUID = 'test-uuid'
        mock_settings.CANDLEPIN_CERT_PEM = 'cert-pem-data'
        mock_settings.CANDLEPIN_KEY_PEM = ''

        cert, key, uuid = _fetch_candlepin_cert_from_db()

        assert cert is None
        assert key is None
        assert uuid is None

    @mock.patch('awx.main.utils.candlepin.settings')
    def test_fetch_candlepin_cert_exception(self, mock_settings):
        """Test fetching Candlepin cert returns None on exception."""
        type(mock_settings).CANDLEPIN_CONSUMER_UUID = mock.PropertyMock(side_effect=Exception('DB error'))

        cert, key, uuid = _fetch_candlepin_cert_from_db()

        assert cert is None
        assert key is None
        assert uuid is None

    @mock.patch('awx.main.utils.candlepin._discover_org')
    @mock.patch('awx.main.utils.candlepin.settings')
    def test_fetch_registration_credentials_from_db(self, mock_settings, mock_discover_org):
        """Test fetching registration credentials from settings."""
        mock_settings.REDHAT_USERNAME = 'test_user'
        mock_settings.REDHAT_PASSWORD = 'test_pass'
        mock_settings.INSTALL_UUID = 'test-install-uuid'
        mock_settings.SUBSCRIPTIONS_USERNAME = 'subs_user'
        mock_settings.SUBSCRIPTIONS_PASSWORD = 'subs_pass'
        mock_discover_org.return_value = 'test_org'

        username, password, org, install_uuid = _fetch_registration_credentials_from_db()

        assert username == 'test_user'
        assert password == 'test_pass'
        assert org == 'test_org'
        assert install_uuid == 'test-install-uuid'
        # Verify _discover_org was called with SUBSCRIPTIONS credentials
        mock_discover_org.assert_called_once()

    @mock.patch('awx.main.utils.candlepin._discover_org')
    @mock.patch('awx.main.utils.candlepin.settings')
    def test_fetch_registration_credentials_missing_settings(self, mock_settings, mock_discover_org):
        """Test fetching credentials when settings are not configured."""
        mock_settings.REDHAT_USERNAME = None
        mock_settings.REDHAT_PASSWORD = None
        mock_settings.INSTALL_UUID = None
        mock_settings.SUBSCRIPTIONS_USERNAME = 'subs_user'
        mock_settings.SUBSCRIPTIONS_PASSWORD = 'subs_pass'
        mock_discover_org.return_value = None

        username, password, org, install_uuid = _fetch_registration_credentials_from_db()

        # Should return None for missing/unconfigured values
        assert username is None
        assert password is None
        assert org is None
        assert install_uuid is None

    @mock.patch('awx.main.utils.candlepin._discover_org')
    @mock.patch('awx.main.utils.candlepin.settings')
    def test_fetch_registration_credentials_exception(self, mock_settings, mock_discover_org):
        """Test fetching credentials when an unexpected exception occurs."""
        # Simulate unexpected error accessing settings
        type(mock_settings).REDHAT_USERNAME = mock.PropertyMock(side_effect=Exception('Unexpected error'))

        username, password, org, install_uuid = _fetch_registration_credentials_from_db()

        # Should return None for all values on exception
        assert username is None
        assert password is None
        assert org is None
        assert install_uuid is None

    @mock.patch('awx.main.utils.candlepin._discover_org')
    @mock.patch('awx.main.utils.candlepin.settings')
    def test_fetch_registration_credentials_org_discovery_fails(self, mock_settings, mock_discover_org):
        """Test fetching credentials when org discovery returns None."""
        mock_settings.REDHAT_USERNAME = 'test_user'
        mock_settings.REDHAT_PASSWORD = 'test_pass'
        mock_settings.INSTALL_UUID = 'test-install-uuid'
        mock_settings.SUBSCRIPTIONS_USERNAME = 'subs_user'
        mock_settings.SUBSCRIPTIONS_PASSWORD = 'subs_pass'
        mock_discover_org.return_value = None

        username, password, org, install_uuid = _fetch_registration_credentials_from_db()

        assert username == 'test_user'
        assert password == 'test_pass'
        assert org is None
        assert install_uuid == 'test-install-uuid'

    @mock.patch('awx.main.utils.candlepin.parse_cert')
    @mock.patch('awx.conf.models.Setting')
    def test_save_candlepin_cert_to_db(self, mock_setting, mock_parse_cert):
        """Test saving Candlepin cert to conf_settings."""
        mock_parse_cert.return_value = {
            'serial': '123456',
            'cn': 'test-consumer',
            'not_before': '2026-01-01T00:00:00+00:00',
            'not_after': '2027-01-01T00:00:00+00:00',
            'days_remaining': 365,
        }

        result = _save_candlepin_cert_to_db('new-cert', 'new-key')

        assert result is True
        # Verify update_or_create was called for each setting
        assert mock_setting.objects.update_or_create.call_count == 4
        calls = mock_setting.objects.update_or_create.call_args_list
        # Check that cert, key, serial, and expires_at were all saved
        keys_saved = {call[1]['key'] for call in calls}
        assert 'CANDLEPIN_CERT_PEM' in keys_saved
        assert 'CANDLEPIN_KEY_PEM' in keys_saved
        assert 'CANDLEPIN_SERIAL_NUMBER' in keys_saved
        assert 'CANDLEPIN_EXPIRES_AT' in keys_saved

    @mock.patch('awx.main.utils.candlepin.parse_cert')
    @mock.patch('awx.conf.models.Setting')
    def test_save_candlepin_registration_to_db(self, mock_setting, mock_parse_cert):
        """Test saving Candlepin registration to conf_settings."""
        mock_parse_cert.return_value = {
            'serial': '789012',
            'cn': 'test-consumer',
            'not_before': '2026-01-01T00:00:00+00:00',
            'not_after': '2027-01-01T00:00:00+00:00',
            'days_remaining': 365,
        }

        result = _save_candlepin_registration_to_db('cert', 'key', 'uuid')

        assert result is True
        # Verify update_or_create was called for each setting (including consumer_uuid)
        assert mock_setting.objects.update_or_create.call_count == 5
        calls = mock_setting.objects.update_or_create.call_args_list
        # Check that all registration data was saved
        keys_saved = {call[1]['key'] for call in calls}
        assert 'CANDLEPIN_CONSUMER_UUID' in keys_saved
        assert 'CANDLEPIN_CERT_PEM' in keys_saved
        assert 'CANDLEPIN_KEY_PEM' in keys_saved
        assert 'CANDLEPIN_SERIAL_NUMBER' in keys_saved
        assert 'CANDLEPIN_EXPIRES_AT' in keys_saved

    @mock.patch('awx.main.utils.candlepin.parse_cert')
    @mock.patch('awx.conf.models.Setting')
    def test_save_candlepin_cert_to_db_parse_failure(self, mock_setting, mock_parse_cert):
        """Test saving Candlepin cert when parse_cert fails."""
        mock_parse_cert.side_effect = Exception('Parse error')

        result = _save_candlepin_cert_to_db('new-cert', 'new-key')

        assert result is True
        # Should still save cert, key, and serial (empty), but not expires_at
        assert mock_setting.objects.update_or_create.call_count == 3
        calls = mock_setting.objects.update_or_create.call_args_list
        keys_saved = {call[1]['key'] for call in calls}
        assert 'CANDLEPIN_CERT_PEM' in keys_saved
        assert 'CANDLEPIN_KEY_PEM' in keys_saved
        assert 'CANDLEPIN_SERIAL_NUMBER' in keys_saved
        # Verify serial_number was saved as empty string
        for call in calls:
            if call[1]['key'] == 'CANDLEPIN_SERIAL_NUMBER':
                assert call[1]['defaults']['value'] == ''

    @mock.patch('awx.main.utils.candlepin.parse_cert')
    @mock.patch('awx.conf.models.Setting')
    def test_save_candlepin_cert_to_db_no_expiry(self, mock_setting, mock_parse_cert):
        """Test saving Candlepin cert when not_after is missing."""
        mock_parse_cert.return_value = {
            'serial': '123456',
            'cn': 'test-consumer',
        }

        result = _save_candlepin_cert_to_db('new-cert', 'new-key')

        assert result is True
        # Should save cert, key, and serial, but not expires_at
        assert mock_setting.objects.update_or_create.call_count == 3
        calls = mock_setting.objects.update_or_create.call_args_list
        keys_saved = {call[1]['key'] for call in calls}
        assert 'CANDLEPIN_CERT_PEM' in keys_saved
        assert 'CANDLEPIN_KEY_PEM' in keys_saved
        assert 'CANDLEPIN_SERIAL_NUMBER' in keys_saved
        assert 'CANDLEPIN_EXPIRES_AT' not in keys_saved

    @mock.patch('awx.conf.models.Setting')
    def test_save_candlepin_cert_to_db_failure(self, mock_setting):
        """Test saving Candlepin cert returns False on exception."""
        mock_setting.objects.update_or_create.side_effect = Exception('DB error')

        result = _save_candlepin_cert_to_db('cert', 'key')

        assert result is False

    @mock.patch('awx.main.utils.candlepin.parse_cert')
    @mock.patch('awx.conf.models.Setting')
    def test_save_candlepin_registration_to_db_parse_failure(self, mock_setting, mock_parse_cert):
        """Test saving Candlepin registration when parse_cert fails."""
        mock_parse_cert.side_effect = Exception('Parse error')

        result = _save_candlepin_registration_to_db('cert', 'key', 'uuid')

        assert result is True
        # Should still save uuid, cert, key, and serial (empty), but not expires_at
        assert mock_setting.objects.update_or_create.call_count == 4
        calls = mock_setting.objects.update_or_create.call_args_list
        keys_saved = {call[1]['key'] for call in calls}
        assert 'CANDLEPIN_CONSUMER_UUID' in keys_saved
        assert 'CANDLEPIN_CERT_PEM' in keys_saved
        assert 'CANDLEPIN_KEY_PEM' in keys_saved
        assert 'CANDLEPIN_SERIAL_NUMBER' in keys_saved
        # Verify serial_number was saved as empty string
        for call in calls:
            if call[1]['key'] == 'CANDLEPIN_SERIAL_NUMBER':
                assert call[1]['defaults']['value'] == ''

    @mock.patch('awx.main.utils.candlepin.parse_cert')
    @mock.patch('awx.conf.models.Setting')
    def test_save_candlepin_registration_to_db_no_expiry(self, mock_setting, mock_parse_cert):
        """Test saving Candlepin registration when not_after is missing."""
        mock_parse_cert.return_value = {
            'serial': '789012',
            'cn': 'test-consumer',
        }

        result = _save_candlepin_registration_to_db('cert', 'key', 'uuid')

        assert result is True
        # Should save uuid, cert, key, and serial, but not expires_at
        assert mock_setting.objects.update_or_create.call_count == 4
        calls = mock_setting.objects.update_or_create.call_args_list
        keys_saved = {call[1]['key'] for call in calls}
        assert 'CANDLEPIN_CONSUMER_UUID' in keys_saved
        assert 'CANDLEPIN_CERT_PEM' in keys_saved
        assert 'CANDLEPIN_KEY_PEM' in keys_saved
        assert 'CANDLEPIN_SERIAL_NUMBER' in keys_saved
        assert 'CANDLEPIN_EXPIRES_AT' not in keys_saved

    @mock.patch('awx.conf.models.Setting')
    def test_save_candlepin_registration_to_db_failure(self, mock_setting):
        """Test saving Candlepin registration returns False on exception."""
        mock_setting.objects.update_or_create.side_effect = Exception('DB error')

        result = _save_candlepin_registration_to_db('cert', 'key', 'uuid')

        assert result is False

    @mock.patch('awx.main.utils.candlepin._save_candlepin_registration_to_db')
    @mock.patch('awx.main.utils.candlepin.CandlepinClient')
    @mock.patch('awx.main.utils.candlepin._fetch_registration_credentials_from_db')
    def test_register_candlepin_consumer_success(self, mock_fetch_creds, mock_client_class, mock_save):
        """Test successful Candlepin consumer registration."""
        mock_fetch_creds.return_value = ('user', 'pass', 'org', 'install-uuid')
        mock_save.return_value = True

        mock_client = mock.Mock()
        mock_client.register_consumer.return_value = ('cert', 'key', 'uuid')
        mock_client_class.return_value = mock_client

        cert, key, uuid = _register_candlepin_consumer()

        assert cert == 'cert'
        assert key == 'key'
        assert uuid == 'uuid'
        mock_save.assert_called_once_with('cert', 'key', 'uuid')

    @mock.patch('awx.main.utils.candlepin._fetch_registration_credentials_from_db')
    def test_register_candlepin_consumer_missing_credentials(self, mock_fetch_creds):
        """Test registration fails when credentials are missing."""
        mock_fetch_creds.return_value = (None, None, None, None)

        cert, key, uuid = _register_candlepin_consumer()

        assert cert is None
        assert key is None
        assert uuid is None

    @mock.patch('awx.main.utils.candlepin._save_candlepin_registration_to_db')
    @mock.patch('awx.main.utils.candlepin.CandlepinClient')
    @mock.patch('awx.main.utils.candlepin._fetch_registration_credentials_from_db')
    def test_register_candlepin_consumer_save_fails(self, mock_fetch_creds, mock_client_class, mock_save):
        """Test registration fails when save to database fails."""
        mock_fetch_creds.return_value = ('user', 'pass', 'org', 'install-uuid')
        mock_save.return_value = False

        mock_client = mock.Mock()
        mock_client.register_consumer.return_value = ('cert', 'key', 'uuid')
        mock_client_class.return_value = mock_client

        cert, key, uuid = _register_candlepin_consumer()

        assert cert is None
        assert key is None
        assert uuid is None
        mock_save.assert_called_once_with('cert', 'key', 'uuid')

    @mock.patch('awx.main.utils.candlepin._save_candlepin_cert_to_db')
    @mock.patch('awx.main.utils.candlepin.run_candlepin_lifecycle')
    def test_run_candlepin_lifecycle_placeholder_uuid(self, mock_lifecycle, mock_save):
        """Test lifecycle is skipped with placeholder UUID."""
        cert, key = _run_candlepin_lifecycle('cert', 'key', CANDLEPIN_UUID_PLACEHOLDER)

        assert cert == 'cert'
        assert key == 'key'
        mock_lifecycle.assert_not_called()
        mock_save.assert_not_called()

    @mock.patch('awx.main.utils.candlepin._save_candlepin_cert_to_db')
    @mock.patch('awx.main.utils.candlepin.run_candlepin_lifecycle')
    def test_run_candlepin_lifecycle_with_renewal(self, mock_lifecycle, mock_save):
        """Test lifecycle with certificate renewal."""
        mock_lifecycle.return_value = ('new-cert', 'new-key')
        mock_save.return_value = True

        cert, key = _run_candlepin_lifecycle('old-cert', 'old-key', 'real-uuid')

        assert cert == 'new-cert'
        assert key == 'new-key'
        mock_lifecycle.assert_called_once()
        mock_save.assert_called_once_with('new-cert', 'new-key')

    @mock.patch('awx.main.utils.candlepin.run_candlepin_lifecycle')
    def test_run_candlepin_lifecycle_error_handling(self, mock_lifecycle):
        """Test lifecycle error handling returns original cert."""
        mock_lifecycle.side_effect = Exception('Test error')

        cert, key = _run_candlepin_lifecycle('cert', 'key', 'uuid')

        # Should return original cert/key on error
        assert cert == 'cert'
        assert key == 'key'

    @mock.patch('awx.main.utils.candlepin.is_cert_valid')
    @mock.patch('awx.main.utils.candlepin._run_candlepin_lifecycle')
    @mock.patch('awx.main.utils.candlepin._fetch_candlepin_cert_from_db')
    def test_get_or_generate_candlepin_certificate_existing_valid(self, mock_fetch, mock_lifecycle, mock_is_valid):
        """Test get_or_generate with existing valid certificate."""
        mock_fetch.return_value = ('cert-pem', 'key-pem', 'consumer-uuid')
        mock_lifecycle.return_value = ('cert-pem', 'key-pem')
        mock_is_valid.return_value = True

        cert, key = get_or_generate_candlepin_certificate('user', 'pass')

        assert cert == 'cert-pem'
        assert key == 'key-pem'
        mock_lifecycle.assert_called_once_with('cert-pem', 'key-pem', 'consumer-uuid')

    @mock.patch('awx.main.utils.candlepin.is_cert_valid')
    @mock.patch('awx.main.utils.candlepin._run_candlepin_lifecycle')
    @mock.patch('awx.main.utils.candlepin._register_candlepin_consumer')
    @mock.patch('awx.main.utils.candlepin._fetch_candlepin_cert_from_db')
    def test_get_or_generate_candlepin_certificate_register_new(self, mock_fetch, mock_register, mock_lifecycle, mock_is_valid):
        """Test get_or_generate when no certificate exists - registers new."""
        mock_fetch.return_value = (None, None, None)
        mock_register.return_value = ('new-cert', 'new-key', 'new-uuid')
        mock_lifecycle.return_value = ('new-cert', 'new-key')
        mock_is_valid.return_value = True

        cert, key = get_or_generate_candlepin_certificate('user', 'pass')

        assert cert == 'new-cert'
        assert key == 'new-key'
        mock_register.assert_called_once()
        mock_lifecycle.assert_called_once_with('new-cert', 'new-key', 'new-uuid')

    @mock.patch('awx.main.utils.candlepin._register_candlepin_consumer')
    @mock.patch('awx.main.utils.candlepin._fetch_candlepin_cert_from_db')
    def test_get_or_generate_candlepin_certificate_registration_fails(self, mock_fetch, mock_register):
        """Test get_or_generate when registration fails."""
        mock_fetch.return_value = (None, None, None)
        mock_register.return_value = (None, None, None)

        cert, key = get_or_generate_candlepin_certificate('user', 'pass')

        assert cert is None
        assert key is None

    @mock.patch('awx.main.utils.candlepin.is_cert_valid')
    @mock.patch('awx.main.utils.candlepin._run_candlepin_lifecycle')
    @mock.patch('awx.main.utils.candlepin._fetch_candlepin_cert_from_db')
    def test_get_or_generate_candlepin_certificate_invalid_cert(self, mock_fetch, mock_lifecycle, mock_is_valid):
        """Test get_or_generate when certificate is invalid."""
        mock_fetch.return_value = ('cert-pem', 'key-pem', 'consumer-uuid')
        mock_lifecycle.return_value = ('cert-pem', 'key-pem')
        mock_is_valid.return_value = False

        cert, key = get_or_generate_candlepin_certificate('user', 'pass')

        assert cert is None
        assert key is None

    @mock.patch('awx.main.utils.candlepin.is_cert_valid')
    @mock.patch('awx.main.utils.candlepin._run_candlepin_lifecycle')
    @mock.patch('awx.main.utils.candlepin._fetch_candlepin_cert_from_db')
    def test_get_or_generate_candlepin_certificate_placeholder_uuid(self, mock_fetch, mock_lifecycle, mock_is_valid):
        """Test get_or_generate when consumer_uuid is placeholder - skips lifecycle."""
        mock_fetch.return_value = ('cert-pem', 'key-pem', CANDLEPIN_UUID_PLACEHOLDER)
        mock_is_valid.return_value = True

        cert, key = get_or_generate_candlepin_certificate('user', 'pass')

        # Should not call lifecycle with placeholder UUID
        mock_lifecycle.assert_not_called()
        # But should still validate cert and return it
        assert cert == 'cert-pem'
        assert key == 'key-pem'
