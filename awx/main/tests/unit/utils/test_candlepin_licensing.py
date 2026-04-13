# Copyright (c) 2026 Ansible, Inc.
# All Rights Reserved.

import pytest
from unittest import mock

from awx.main.utils.licensing import (
    CANDLEPIN_CERT_SETTING_KEY,
    CANDLEPIN_KEY_SETTING_KEY,
    CANDLEPIN_UUID_SETTING_KEY,
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
        assert CANDLEPIN_CERT_SETTING_KEY == 'CANDLEPIN_CONSUMER_CERT'
        assert CANDLEPIN_KEY_SETTING_KEY == 'CANDLEPIN_CONSUMER_KEY'
        assert CANDLEPIN_UUID_SETTING_KEY == 'CANDLEPIN_CONSUMER_UUID'
        assert CANDLEPIN_UUID_PLACEHOLDER == '00000000-0000-0000-0000-000000000000'
        assert SUBSCRIPTIONS_USERNAME_SETTING_KEY == 'SUBSCRIPTIONS_USERNAME'
        assert SUBSCRIPTIONS_PASSWORD_SETTING_KEY == 'SUBSCRIPTIONS_PASSWORD'

    @mock.patch('awx.main.utils.licensing.connection')
    def test_fetch_candlepin_cert_from_db(self, mock_connection):
        """Test fetching Candlepin lifecycle data from database."""
        mock_cursor = mock.Mock()
        mock_cursor.fetchall.return_value = [
            ('CANDLEPIN_CONSUMER_CERT', '"cert-pem-data"'),
            ('CANDLEPIN_CONSUMER_KEY', '"key-pem-data"'),
            ('CANDLEPIN_CONSUMER_UUID', '"test-uuid"'),
        ]
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

        cert, key, uuid = _fetch_candlepin_cert_from_db()

        assert cert == 'cert-pem-data'
        assert key == 'key-pem-data'
        assert uuid == 'test-uuid'

    @mock.patch('awx.main.utils.licensing.connection')
    def test_fetch_candlepin_cert_missing_data(self, mock_connection):
        """Test fetching Candlepin data when not present."""
        mock_cursor = mock.Mock()
        mock_cursor.fetchall.return_value = []
        mock_connection.cursor.return_value.__enter__.return_value = mock_cursor

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

    @mock.patch('awx.main.utils.licensing._upsert_conf_settings')
    def test_save_candlepin_cert_to_db(self, mock_upsert):
        """Test saving Candlepin cert to database."""
        mock_upsert.return_value = True

        _save_candlepin_cert_to_db('new-cert', 'new-key')

        mock_upsert.assert_called_once()
        call_args = mock_upsert.call_args[0][0]
        assert ('CANDLEPIN_CONSUMER_CERT', 'new-cert') in list(call_args)
        assert ('CANDLEPIN_CONSUMER_KEY', 'new-key') in list(call_args)

    @mock.patch('awx.main.utils.licensing._upsert_conf_settings')
    def test_save_candlepin_registration_to_db(self, mock_upsert):
        """Test saving Candlepin registration to database."""
        mock_upsert.return_value = True

        _save_candlepin_registration_to_db('cert', 'key', 'uuid')

        mock_upsert.assert_called_once()
        call_args = mock_upsert.call_args[0][0]
        call_list = list(call_args)
        assert ('CANDLEPIN_CONSUMER_CERT', 'cert') in call_list
        assert ('CANDLEPIN_CONSUMER_KEY', 'key') in call_list
        assert ('CANDLEPIN_CONSUMER_UUID', 'uuid') in call_list

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
