# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

from unittest import mock

import requests

from awx.main.utils.candlepin import (
    _discover_org,
    _fetch_candlepin_cert_from_db,
    _fetch_registration_credentials_from_db,
    _save_candlepin_cert_to_db,
    _save_candlepin_registration_to_db,
    _register_candlepin_consumer,
    _run_candlepin_lifecycle,
    get_or_generate_candlepin_certificate,
    resolve_registration_credentials,
)


class TestCandlepinLicensing:
    """Tests for Candlepin integration in licensing module."""

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
    def test_discover_org_no_verify_tls(self, mock_requests_get):
        """Test organization discovery with TLS verification disabled."""
        mock_response = mock.Mock()
        mock_response.json.return_value = [{'key': 'test_org', 'displayName': 'Test Organization'}]
        mock_requests_get.return_value = mock_response

        org = _discover_org('https://candlepin.example.com', 'test_user', 'test_pass', verify_tls=False)

        assert org == 'test_org'
        # Should use False for verify when verify_tls=False
        mock_requests_get.assert_called_once_with(
            'https://candlepin.example.com/users/test_user/owners',
            auth=('test_user', 'test_pass'),
            verify=False,
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

    @mock.patch('awx.main.utils.candlepin.requests.get')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_ca')
    def test_discover_org_non_list_response(self, mock_get_ca, mock_requests_get):
        """Test organization discovery handles non-list response."""
        mock_get_ca.return_value = None
        mock_response = mock.Mock()
        mock_response.json.return_value = {'key': 'test_org'}  # Dict instead of list
        mock_requests_get.return_value = mock_response

        org = _discover_org('https://candlepin.example.com', 'test_user', 'test_pass')

        assert org is None

    @mock.patch('awx.main.utils.candlepin.requests.get')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_ca')
    def test_discover_org_non_dict_entry(self, mock_get_ca, mock_requests_get):
        """Test organization discovery handles non-dict org entry."""
        mock_get_ca.return_value = None
        mock_response = mock.Mock()
        mock_response.json.return_value = ['not_a_dict']  # String instead of dict
        mock_requests_get.return_value = mock_response

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
        """Test fetching Candlepin cert with empty consumer UUID."""
        mock_settings.CANDLEPIN_CONSUMER_UUID = ''
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
        assert mock_discover_org.call_count == 1
        args = mock_discover_org.call_args[0]
        assert args[1] == 'subs_user'  # SUBSCRIPTIONS_USERNAME
        assert args[2] == 'subs_pass'  # SUBSCRIPTIONS_PASSWORD

    @mock.patch('awx.main.utils.candlepin._discover_org')
    @mock.patch('awx.main.utils.candlepin.settings')
    def test_fetch_registration_credentials_missing_settings(self, mock_settings, mock_discover_org):
        """Test fetching credentials when REDHAT settings are not configured but SUBSCRIPTIONS are."""
        mock_settings.REDHAT_USERNAME = None
        mock_settings.REDHAT_PASSWORD = None
        mock_settings.INSTALL_UUID = None
        mock_settings.SUBSCRIPTIONS_USERNAME = 'subs_user'
        mock_settings.SUBSCRIPTIONS_PASSWORD = 'subs_pass'
        mock_discover_org.return_value = None

        username, password, org, install_uuid = _fetch_registration_credentials_from_db()

        # Should fall back to SUBSCRIPTIONS credentials
        assert username == 'subs_user'
        assert password == 'subs_pass'
        assert org is None
        assert install_uuid is None

    @mock.patch('awx.main.utils.candlepin._discover_org')
    @mock.patch('awx.main.utils.candlepin.settings')
    def test_fetch_registration_credentials_redhat_with_subscriptions_for_org(self, mock_settings, mock_discover_org):
        """Test REDHAT credentials for auth with SUBSCRIPTIONS credentials for org discovery."""
        mock_settings.REDHAT_USERNAME = 'redhat_user'
        mock_settings.REDHAT_PASSWORD = 'redhat_pass'
        mock_settings.SUBSCRIPTIONS_USERNAME = 'subs_user'
        mock_settings.SUBSCRIPTIONS_PASSWORD = 'subs_pass'
        mock_settings.INSTALL_UUID = 'test-install-uuid'
        mock_discover_org.return_value = 'discovered_org'

        username, password, org, install_uuid = _fetch_registration_credentials_from_db()

        # Should use REDHAT for auth
        assert username == 'redhat_user'
        assert password == 'redhat_pass'
        # But org should be discovered using SUBSCRIPTIONS credentials
        assert org == 'discovered_org'
        assert install_uuid == 'test-install-uuid'
        # Verify _discover_org was called with SUBSCRIPTIONS credentials
        args = mock_discover_org.call_args[0]
        assert args[1] == 'subs_user'
        assert args[2] == 'subs_pass'

    @mock.patch('awx.main.utils.candlepin._discover_org')
    @mock.patch('awx.main.utils.candlepin.settings')
    def test_fetch_registration_credentials_client_id_fallback(self, mock_settings, mock_discover_org):
        """Test fetching credentials falls back to CLIENT_ID/SECRET when others missing.

        Note: org will be None because org discovery requires SUBSCRIPTIONS_USERNAME/PASSWORD.
        """
        mock_settings.REDHAT_USERNAME = None
        mock_settings.REDHAT_PASSWORD = None
        mock_settings.SUBSCRIPTIONS_USERNAME = None
        mock_settings.SUBSCRIPTIONS_PASSWORD = None
        mock_settings.SUBSCRIPTIONS_CLIENT_ID = 'client_id'
        mock_settings.SUBSCRIPTIONS_CLIENT_SECRET = 'client_secret'
        mock_settings.INSTALL_UUID = 'test-install-uuid'

        username, password, org, install_uuid = _fetch_registration_credentials_from_db()

        # Should fall back to CLIENT_ID/SECRET credentials
        assert username == 'client_id'
        assert password == 'client_secret'
        # org is None because _discover_org requires SUBSCRIPTIONS_USERNAME/PASSWORD
        assert org is None
        assert install_uuid == 'test-install-uuid'
        # _discover_org should not be called when SUBSCRIPTIONS credentials missing
        mock_discover_org.assert_not_called()

    @mock.patch('awx.main.utils.candlepin._discover_org')
    @mock.patch('awx.main.utils.candlepin.settings')
    def test_fetch_registration_credentials_all_missing(self, mock_settings, mock_discover_org):
        """Test fetching credentials when all credential settings are not configured."""
        mock_settings.REDHAT_USERNAME = None
        mock_settings.REDHAT_PASSWORD = None
        mock_settings.SUBSCRIPTIONS_USERNAME = None
        mock_settings.SUBSCRIPTIONS_PASSWORD = None
        mock_settings.SUBSCRIPTIONS_CLIENT_ID = None
        mock_settings.SUBSCRIPTIONS_CLIENT_SECRET = None
        mock_settings.INSTALL_UUID = None

        username, password, org, install_uuid = _fetch_registration_credentials_from_db()

        # Should return None for all values when no credentials found
        assert username is None
        assert password is None
        assert org is None
        assert install_uuid is None
        # _discover_org should not be called when credentials are missing
        mock_discover_org.assert_not_called()

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

    @mock.patch('awx.main.utils.candlepin._discover_org')
    @mock.patch('awx.main.utils.candlepin.settings')
    def test_fetch_registration_credentials_no_verify_tls(self, mock_settings, mock_discover_org):
        """Test fetching credentials passes verify_tls=False to _discover_org."""
        mock_settings.REDHAT_USERNAME = 'test_user'
        mock_settings.REDHAT_PASSWORD = 'test_pass'
        mock_settings.INSTALL_UUID = 'test-install-uuid'
        mock_settings.SUBSCRIPTIONS_USERNAME = 'subs_user'
        mock_settings.SUBSCRIPTIONS_PASSWORD = 'subs_pass'
        mock_discover_org.return_value = 'test_org'

        username, password, org, install_uuid = _fetch_registration_credentials_from_db(verify_tls=False)

        assert username == 'test_user'
        assert password == 'test_pass'
        assert org == 'test_org'
        assert install_uuid == 'test-install-uuid'
        # Verify _discover_org was called with verify_tls=False
        mock_discover_org.assert_called_once()
        call_kwargs = mock_discover_org.call_args[1]
        assert call_kwargs['verify_tls'] is False

    @mock.patch('awx.main.utils.candlepin._fetch_registration_credentials_from_db')
    def test_resolve_registration_credentials_no_overrides(self, mock_fetch):
        """Test resolve_registration_credentials with no overrides."""
        mock_fetch.return_value = ('db_user', 'db_pass', 'db_org', 'install-uuid')

        username, password, org, install_uuid, errors = resolve_registration_credentials()

        assert username == 'db_user'
        assert password == 'db_pass'
        assert org == 'db_org'
        assert install_uuid == 'install-uuid'
        assert errors is None

    @mock.patch('awx.main.utils.candlepin._fetch_registration_credentials_from_db')
    def test_resolve_registration_credentials_with_overrides(self, mock_fetch):
        """Test resolve_registration_credentials with CLI overrides."""
        mock_fetch.return_value = ('db_user', 'db_pass', 'db_org', 'install-uuid')

        username, password, org, install_uuid, errors = resolve_registration_credentials(
            username_override='cli_user', password_override='cli_pass', org_override='cli_org'
        )

        assert username == 'cli_user'
        assert password == 'cli_pass'
        assert org == 'cli_org'
        assert install_uuid == 'install-uuid'
        assert errors is None

    @mock.patch('awx.main.utils.candlepin._fetch_registration_credentials_from_db')
    def test_resolve_registration_credentials_partial_overrides(self, mock_fetch):
        """Test resolve_registration_credentials with partial overrides."""
        mock_fetch.return_value = ('db_user', 'db_pass', 'db_org', 'install-uuid')

        username, password, org, install_uuid, errors = resolve_registration_credentials(username_override='cli_user')

        assert username == 'cli_user'
        assert password == 'db_pass'
        assert org == 'db_org'
        assert install_uuid == 'install-uuid'
        assert errors is None

    @mock.patch('awx.main.utils.candlepin._fetch_registration_credentials_from_db')
    def test_resolve_registration_credentials_missing_values(self, mock_fetch):
        """Test resolve_registration_credentials validation fails when values missing."""
        mock_fetch.return_value = (None, None, None, 'install-uuid')

        username, password, org, install_uuid, errors = resolve_registration_credentials()

        assert username is None
        assert password is None
        assert org is None
        assert install_uuid is None
        assert errors is not None
        assert len(errors) == 3
        assert 'username' in errors[0]
        assert 'password' in errors[1]
        assert 'org' in errors[2]

    @mock.patch('awx.main.utils.candlepin._fetch_registration_credentials_from_db')
    def test_resolve_registration_credentials_verify_tls_false(self, mock_fetch):
        """Test resolve_registration_credentials passes verify_tls=False to fetch function."""
        mock_fetch.return_value = ('db_user', 'db_pass', 'db_org', 'install-uuid')

        username, password, org, install_uuid, errors = resolve_registration_credentials(verify_tls=False)

        # Verify _fetch_registration_credentials_from_db was called with verify_tls=False
        mock_fetch.assert_called_once_with(verify_tls=False)
        assert username == 'db_user'
        assert password == 'db_pass'
        assert org == 'db_org'
        assert install_uuid == 'install-uuid'
        assert errors is None

    @mock.patch('awx.main.utils.candlepin.parse_cert')
    @mock.patch('awx.main.utils.candlepin.settings')
    def test_save_candlepin_cert_to_db(self, mock_settings, mock_parse_cert):
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
        # Verify settings were assigned
        assert mock_settings.CANDLEPIN_CERT_PEM == 'new-cert'
        assert mock_settings.CANDLEPIN_KEY_PEM == 'new-key'
        assert mock_settings.CANDLEPIN_SERIAL_NUMBER == '123456'

    @mock.patch('awx.main.utils.candlepin.parse_cert')
    @mock.patch('awx.main.utils.candlepin.settings')
    def test_save_candlepin_registration_to_db(self, mock_settings, mock_parse_cert):
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
        # Verify all registration data was saved
        assert mock_settings.CANDLEPIN_CONSUMER_UUID == 'uuid'
        assert mock_settings.CANDLEPIN_CERT_PEM == 'cert'
        assert mock_settings.CANDLEPIN_KEY_PEM == 'key'
        assert mock_settings.CANDLEPIN_SERIAL_NUMBER == '789012'

    @mock.patch('awx.main.utils.candlepin.parse_cert')
    @mock.patch('awx.main.utils.candlepin.settings')
    def test_save_candlepin_cert_to_db_parse_failure(self, mock_settings, mock_parse_cert):
        """Test saving Candlepin cert when parse_cert fails."""
        mock_parse_cert.side_effect = Exception('Parse error')

        result = _save_candlepin_cert_to_db('new-cert', 'new-key')

        assert result is True
        # Should still save cert, key, and serial (empty string)
        assert mock_settings.CANDLEPIN_CERT_PEM == 'new-cert'
        assert mock_settings.CANDLEPIN_KEY_PEM == 'new-key'
        assert mock_settings.CANDLEPIN_SERIAL_NUMBER == ''

    @mock.patch('awx.main.utils.candlepin.settings')
    def test_save_candlepin_cert_to_db_failure(self, mock_settings):
        """Test saving Candlepin cert returns False on exception."""
        # Simulate settings assignment raising an exception
        type(mock_settings).CANDLEPIN_CERT_PEM = mock.PropertyMock(side_effect=Exception('Settings error'))

        result = _save_candlepin_cert_to_db('cert', 'key')

        assert result is False

    @mock.patch('awx.main.utils.candlepin.parse_cert')
    @mock.patch('awx.main.utils.candlepin.settings')
    def test_save_candlepin_registration_to_db_parse_failure(self, mock_settings, mock_parse_cert):
        """Test saving Candlepin registration when parse_cert fails."""
        mock_parse_cert.side_effect = Exception('Parse error')

        result = _save_candlepin_registration_to_db('cert', 'key', 'uuid')

        assert result is True
        # Should still save uuid, cert, key, and serial (empty string)
        assert mock_settings.CANDLEPIN_CONSUMER_UUID == 'uuid'
        assert mock_settings.CANDLEPIN_CERT_PEM == 'cert'
        assert mock_settings.CANDLEPIN_KEY_PEM == 'key'
        assert mock_settings.CANDLEPIN_SERIAL_NUMBER == ''

    @mock.patch('awx.main.utils.candlepin.settings')
    def test_save_candlepin_registration_to_db_failure(self, mock_settings):
        """Test saving Candlepin registration returns False on exception."""
        # Simulate settings assignment raising an exception
        type(mock_settings).CANDLEPIN_CONSUMER_UUID = mock.PropertyMock(side_effect=Exception('Settings error'))

        result = _save_candlepin_registration_to_db('cert', 'key', 'uuid')

        assert result is False

    @mock.patch('awx.main.utils.candlepin._save_candlepin_registration_to_db')
    @mock.patch('awx.main.utils.candlepin.CandlepinClient')
    @mock.patch('awx.main.utils.candlepin._fetch_registration_credentials_from_db')
    @mock.patch('awx.main.utils.candlepin.get_proxy_url')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_ca')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_url')
    def test_register_candlepin_consumer_success(self, mock_get_url, mock_get_ca, mock_get_proxy, mock_fetch_creds, mock_client_class, mock_save):
        """Test successful Candlepin consumer registration."""
        mock_get_url.return_value = 'https://candlepin.example.com'
        mock_get_ca.return_value = '/path/to/ca.pem'
        mock_get_proxy.return_value = None
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
    @mock.patch('awx.main.utils.candlepin.get_proxy_url')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_ca')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_url')
    def test_register_candlepin_consumer_save_fails(self, mock_get_url, mock_get_ca, mock_get_proxy, mock_fetch_creds, mock_client_class, mock_save):
        """Test registration fails when save to database fails."""
        mock_get_url.return_value = 'https://candlepin.example.com'
        mock_get_ca.return_value = '/path/to/ca.pem'
        mock_get_proxy.return_value = None
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
    def test_run_candlepin_lifecycle_empty_uuid(self, mock_lifecycle, mock_save):
        """Test lifecycle is skipped with empty consumer UUID."""
        cert, key = _run_candlepin_lifecycle('cert', 'key', '')

        assert cert == 'cert'
        assert key == 'key'
        mock_lifecycle.assert_not_called()
        mock_save.assert_not_called()

    @mock.patch('awx.main.utils.candlepin._save_candlepin_cert_to_db')
    @mock.patch('awx.main.utils.candlepin.run_candlepin_lifecycle')
    @mock.patch('awx.main.utils.candlepin.get_proxy_url')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_ca')
    @mock.patch('awx.main.utils.candlepin.get_renewal_days')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_url')
    def test_run_candlepin_lifecycle_with_renewal(self, mock_get_url, mock_get_days, mock_get_ca, mock_get_proxy, mock_lifecycle, mock_save):
        """Test lifecycle with certificate renewal."""
        mock_get_url.return_value = 'https://candlepin.example.com'
        mock_get_days.return_value = 90
        mock_get_ca.return_value = '/path/to/ca.pem'
        mock_get_proxy.return_value = None
        mock_lifecycle.return_value = ('new-cert', 'new-key')
        mock_save.return_value = True

        cert, key = _run_candlepin_lifecycle('old-cert', 'old-key', 'real-uuid')

        assert cert == 'new-cert'
        assert key == 'new-key'
        mock_lifecycle.assert_called_once()
        mock_save.assert_called_once_with('new-cert', 'new-key')

    @mock.patch('awx.main.utils.candlepin.run_candlepin_lifecycle')
    @mock.patch('awx.main.utils.candlepin.get_proxy_url')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_ca')
    @mock.patch('awx.main.utils.candlepin.get_renewal_days')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_url')
    def test_run_candlepin_lifecycle_error_handling(self, mock_get_url, mock_get_days, mock_get_ca, mock_get_proxy, mock_lifecycle):
        """Test lifecycle error handling returns original cert."""
        mock_get_url.return_value = 'https://candlepin.example.com'
        mock_get_days.return_value = 90
        mock_get_ca.return_value = '/path/to/ca.pem'
        mock_get_proxy.return_value = None
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

        cert, key = get_or_generate_candlepin_certificate()

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

        cert, key = get_or_generate_candlepin_certificate()

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

        cert, key = get_or_generate_candlepin_certificate()

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

        cert, key = get_or_generate_candlepin_certificate()

        assert cert is None
        assert key is None

    @mock.patch('awx.main.utils.candlepin.is_cert_valid')
    @mock.patch('awx.main.utils.candlepin._run_candlepin_lifecycle')
    @mock.patch('awx.main.utils.candlepin._fetch_candlepin_cert_from_db')
    def test_get_or_generate_candlepin_certificate_empty_uuid(self, mock_fetch, mock_lifecycle, mock_is_valid):
        """Test get_or_generate when consumer_uuid is empty - skips lifecycle."""
        mock_fetch.return_value = ('cert-pem', 'key-pem', '')
        mock_is_valid.return_value = True

        cert, key = get_or_generate_candlepin_certificate()

        # Should not call lifecycle with empty UUID
        mock_lifecycle.assert_not_called()
        # But should still validate cert and return it
        assert cert == 'cert-pem'
        assert key == 'key-pem'

    @mock.patch('awx.main.utils.candlepin.is_cert_valid')
    @mock.patch('awx.main.utils.candlepin._run_candlepin_lifecycle')
    @mock.patch('awx.main.utils.candlepin._fetch_candlepin_cert_from_db')
    def test_get_or_generate_candlepin_certificate_expired_cert_not_renewed(self, mock_fetch, mock_lifecycle, mock_is_valid):
        """Test get_or_generate with expired certificate that lifecycle fails to renew."""
        mock_fetch.return_value = ('expired-cert', 'key-pem', 'consumer-uuid')
        # Lifecycle fails to renew (returns same expired cert)
        mock_lifecycle.return_value = ('expired-cert', 'key-pem')
        # Certificate is still invalid after lifecycle
        mock_is_valid.return_value = False

        cert, key = get_or_generate_candlepin_certificate()

        assert cert is None
        assert key is None
        mock_lifecycle.assert_called_once()
        mock_is_valid.assert_called_once()

    @mock.patch('awx.main.utils.candlepin.is_cert_valid')
    @mock.patch('awx.main.utils.candlepin._run_candlepin_lifecycle')
    @mock.patch('awx.main.utils.candlepin._fetch_candlepin_cert_from_db')
    def test_get_or_generate_candlepin_certificate_expired_cert_renewed_successfully(self, mock_fetch, mock_lifecycle, mock_is_valid):
        """Test get_or_generate with expired certificate that is successfully renewed."""
        mock_fetch.return_value = ('expired-cert', 'old-key', 'consumer-uuid')
        # Lifecycle successfully renews
        mock_lifecycle.return_value = ('new-cert', 'new-key')
        # New certificate is valid
        mock_is_valid.return_value = True

        cert, key = get_or_generate_candlepin_certificate()

        assert cert == 'new-cert'
        assert key == 'new-key'
        mock_lifecycle.assert_called_once_with('expired-cert', 'old-key', 'consumer-uuid')

    @mock.patch('awx.main.utils.candlepin.is_cert_valid')
    @mock.patch('awx.main.utils.candlepin._run_candlepin_lifecycle')
    @mock.patch('awx.main.utils.candlepin._fetch_candlepin_cert_from_db')
    def test_get_or_generate_candlepin_certificate_lifecycle_exception_cert_still_valid(self, mock_fetch, mock_lifecycle, mock_is_valid):
        """Test get_or_generate when lifecycle fails but returns valid original cert."""
        mock_fetch.return_value = ('cert-pem', 'key-pem', 'consumer-uuid')
        # Lifecycle fails and returns original cert (this is what _run_candlepin_lifecycle does on exception)
        mock_lifecycle.return_value = ('cert-pem', 'key-pem')
        # If the cert is still valid, it gets returned
        mock_is_valid.return_value = True

        cert, key = get_or_generate_candlepin_certificate()

        assert cert == 'cert-pem'
        assert key == 'key-pem'
        mock_lifecycle.assert_called_once_with('cert-pem', 'key-pem', 'consumer-uuid')

    @mock.patch('awx.main.utils.candlepin.is_cert_valid')
    @mock.patch('awx.main.utils.candlepin._run_candlepin_lifecycle')
    @mock.patch('awx.main.utils.candlepin._fetch_candlepin_cert_from_db')
    def test_get_or_generate_candlepin_certificate_lifecycle_exception_cert_invalid(self, mock_fetch, mock_lifecycle, mock_is_valid):
        """Test get_or_generate when lifecycle fails and original cert is invalid."""
        mock_fetch.return_value = ('expired-cert-pem', 'key-pem', 'consumer-uuid')
        # Lifecycle fails and returns original expired cert
        mock_lifecycle.return_value = ('expired-cert-pem', 'key-pem')
        # Original cert is invalid (expired)
        mock_is_valid.return_value = False

        cert, key = get_or_generate_candlepin_certificate()

        # Should return None because cert is invalid
        assert cert is None
        assert key is None
        mock_lifecycle.assert_called_once_with('expired-cert-pem', 'key-pem', 'consumer-uuid')

    @mock.patch('awx.main.utils.candlepin.CandlepinClient')
    @mock.patch('awx.main.utils.candlepin.get_proxy_url')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_ca')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_url')
    @mock.patch('awx.main.utils.candlepin._save_candlepin_registration_to_db')
    @mock.patch('awx.main.utils.candlepin._fetch_registration_credentials_from_db')
    def test_register_candlepin_consumer_network_timeout(self, mock_fetch_creds, mock_save, mock_get_url, mock_get_ca, mock_get_proxy, mock_client_class):
        """Test _register_candlepin_consumer handles network timeout."""
        mock_fetch_creds.return_value = ('user', 'pass', 'org', 'install-uuid')
        mock_get_url.return_value = 'https://candlepin.example.com'
        mock_get_ca.return_value = None
        mock_get_proxy.return_value = None

        # Simulate network timeout
        mock_client = mock.Mock()
        mock_client.register_consumer.side_effect = requests.exceptions.Timeout('Connection timeout')
        mock_client_class.return_value = mock_client

        cert, key, uuid = _register_candlepin_consumer()

        assert cert is None
        assert key is None
        assert uuid is None
        mock_save.assert_not_called()

    @mock.patch('awx.main.utils.candlepin.run_candlepin_lifecycle')
    @mock.patch('awx.main.utils.candlepin.get_proxy_url')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_ca')
    @mock.patch('awx.main.utils.candlepin.get_renewal_days')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_url')
    @mock.patch('awx.main.utils.candlepin._save_candlepin_cert_to_db')
    def test_run_candlepin_lifecycle_timeout_during_renewal(self, mock_save, mock_get_url, mock_get_renewal, mock_get_ca, mock_get_proxy, mock_lifecycle):
        """Test _run_candlepin_lifecycle handles timeout during renewal."""
        mock_get_url.return_value = 'https://candlepin.example.com'
        mock_get_renewal.return_value = 90
        mock_get_ca.return_value = None
        mock_get_proxy.return_value = None

        # Lifecycle raises timeout exception
        mock_lifecycle.side_effect = requests.exceptions.Timeout('Renewal timeout')

        cert, key = _run_candlepin_lifecycle('cert', 'key', 'consumer-uuid')

        # Should return original cert on failure
        assert cert == 'cert'
        assert key == 'key'
        mock_save.assert_not_called()

    @mock.patch('awx.main.utils.candlepin.run_candlepin_lifecycle')
    @mock.patch('awx.main.utils.candlepin.get_proxy_url')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_ca')
    @mock.patch('awx.main.utils.candlepin.get_renewal_days')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_url')
    @mock.patch('awx.main.utils.candlepin._save_candlepin_cert_to_db')
    def test_run_candlepin_lifecycle_consumer_deleted(self, mock_save, mock_get_url, mock_get_renewal, mock_get_ca, mock_get_proxy, mock_lifecycle):
        """Test _run_candlepin_lifecycle handles consumer deleted server-side."""
        mock_get_url.return_value = 'https://candlepin.example.com'
        mock_get_renewal.return_value = 90
        mock_get_ca.return_value = None
        mock_get_proxy.return_value = None

        # Lifecycle raises 410 Gone error
        mock_lifecycle.side_effect = Exception('410 Client Error: Gone')

        cert, key = _run_candlepin_lifecycle('cert', 'key', 'consumer-uuid')

        # Should return original cert on failure
        assert cert == 'cert'
        assert key == 'key'
        mock_save.assert_not_called()

    @mock.patch('awx.main.utils.candlepin.requests.get')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_ca')
    def test_discover_org_network_timeout(self, mock_get_ca, mock_requests_get):
        """Test _discover_org handles network timeout gracefully."""
        mock_get_ca.return_value = None
        mock_requests_get.side_effect = requests.exceptions.Timeout('Connection timeout')

        org = _discover_org('https://candlepin.example.com', 'test_user', 'test_pass')

        assert org is None

    @mock.patch('awx.main.utils.candlepin.requests.get')
    @mock.patch('awx.main.utils.candlepin.get_candlepin_ca')
    def test_discover_org_401_unauthorized(self, mock_get_ca, mock_requests_get):
        """Test _discover_org handles 401 unauthorized (invalid credentials)."""
        mock_get_ca.return_value = None
        mock_response = mock.Mock()
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError('401 Client Error: Unauthorized')
        mock_requests_get.return_value = mock_response

        org = _discover_org('https://candlepin.example.com', 'bad_user', 'bad_pass')

        assert org is None

    @mock.patch('awx.main.utils.candlepin.parse_cert')
    @mock.patch('awx.main.utils.candlepin.settings')
    def test_save_candlepin_cert_to_db_cert_parse_failure(self, mock_settings, mock_parse_cert):
        """Test _save_candlepin_cert_to_db handles cert parsing failure gracefully."""
        # Cert parsing fails
        mock_parse_cert.side_effect = ValueError('Invalid certificate format')

        result = _save_candlepin_cert_to_db('invalid-cert', 'key-pem')

        # Should still save cert even if parsing fails
        assert result is True
        # Verify cert, key, and serial (empty string) were saved
        assert mock_settings.CANDLEPIN_CERT_PEM == 'invalid-cert'
        assert mock_settings.CANDLEPIN_KEY_PEM == 'key-pem'
        assert mock_settings.CANDLEPIN_SERIAL_NUMBER == ''

    @mock.patch('awx.main.utils.candlepin.parse_cert')
    @mock.patch('awx.main.utils.candlepin.settings')
    def test_save_candlepin_registration_to_db_cert_parse_failure(self, mock_settings, mock_parse_cert):
        """Test _save_candlepin_registration_to_db handles cert parsing failure gracefully."""
        # Cert parsing fails
        mock_parse_cert.side_effect = ValueError('Invalid certificate format')

        result = _save_candlepin_registration_to_db('invalid-cert', 'key-pem', 'consumer-uuid')

        # Should still save registration even if parsing fails
        assert result is True
        # Verify UUID, cert, key, and serial (empty string) were saved
        assert mock_settings.CANDLEPIN_CONSUMER_UUID == 'consumer-uuid'
        assert mock_settings.CANDLEPIN_CERT_PEM == 'invalid-cert'
        assert mock_settings.CANDLEPIN_KEY_PEM == 'key-pem'
        assert mock_settings.CANDLEPIN_SERIAL_NUMBER == ''
